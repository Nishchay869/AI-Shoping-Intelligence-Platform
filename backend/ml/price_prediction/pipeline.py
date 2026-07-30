"""End-to-end orchestration for one product's price series.

Two-phase usage, standard ML practice:
  1. `.fit(history)` + `.evaluate()`  - chronological, purged train/test split; reports honest holdout
     metrics for all three models before anything is deployed.
  2. `.fit_final(history)` + `.predict()` - once the holdout metrics look acceptable, refit every model on
     the *entire* history (test data is real signal too, once you're done measuring generalization) and
     forecast forward from the true latest observed date.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from ml.price_prediction.evaluate import ClassificationMetrics, RegressionMetrics, evaluate_classification, evaluate_regression
from ml.price_prediction.features import FEATURE_COLUMNS, build_features, make_supervised
from ml.price_prediction.lstm_model import SEQUENCE_LENGTH, LSTMPricePredictor, make_sequences
from ml.price_prediction.prophet_model import ProphetPriceModel
from ml.price_prediction.xgboost_model import train_price_drop_classifier, train_price_regressor

PROPHET_FEATURE_COLUMNS = ["prophet_trend", "prophet_yearly", "prophet_weekly", "prophet_holiday_effect"]
ALL_FEATURE_COLUMNS = FEATURE_COLUMNS + PROPHET_FEATURE_COLUMNS


@dataclass(frozen=True)
class PricePrediction:
    expected_future_price_minor: float
    price_drop_probability: float
    component_forecasts: dict[str, float]  # per-model forecast, for transparency into the ensemble


class PricePredictionPipeline:
    def __init__(self, horizon_days: int = 30, price_drop_threshold: float = 0.02, test_size: float = 0.2, seed: int = 42):
        self.horizon_days = horizon_days
        self.price_drop_threshold = price_drop_threshold
        self.test_size = test_size
        self.seed = seed

    def _prepare(self, price_series: pd.DataFrame, prophet_fit_frame: pd.DataFrame) -> pd.DataFrame:
        features = build_features(price_series)
        supervised = make_supervised(features, self.horizon_days, self.price_drop_threshold)
        self.prophet = ProphetPriceModel().fit(prophet_fit_frame)
        components = self.prophet.in_sample_components(supervised["date"])
        return supervised.merge(components, on="date", how="left")

    def fit(self, price_series: pd.DataFrame) -> "PricePredictionPipeline":
        """Fit on a purged training prefix only, holding out the tail for honest evaluation via `.evaluate()`."""
        raw_supervised = make_supervised(build_features(price_series), self.horizon_days, self.price_drop_threshold)
        provisional_cutoff = int(len(raw_supervised) * (1 - self.test_size))
        prophet_cutoff = max(provisional_cutoff - self.horizon_days, 1)  # Prophet must never see test-period price levels
        merged = self._prepare(price_series, raw_supervised.iloc[:prophet_cutoff][["date", "price_minor"]])

        usable = merged.dropna(subset=ALL_FEATURE_COLUMNS + ["future_price"]).reset_index(drop=True)
        cutoff = int(len(usable) * (1 - self.test_size))
        train_cutoff = max(cutoff - self.horizon_days, 1)  # purge horizon_days so no training target overlaps the test window
        self.train_frame_, self.test_frame_, self.full_frame_ = usable.iloc[:train_cutoff], usable.iloc[cutoff:], usable
        self._fit_models(self.train_frame_)
        return self

    def fit_final(self, price_series: pd.DataFrame) -> "PricePredictionPipeline":
        """Refit on the entire series - call after `.evaluate()` has reported acceptable holdout metrics."""
        raw_supervised = make_supervised(build_features(price_series), self.horizon_days, self.price_drop_threshold)
        merged = self._prepare(price_series, raw_supervised[["date", "price_minor"]])
        self.full_frame_ = merged.dropna(subset=ALL_FEATURE_COLUMNS).reset_index(drop=True)
        trainable = self.full_frame_.dropna(subset=["future_price"])
        self._fit_models(trainable)
        return self

    def _fit_models(self, train_frame: pd.DataFrame) -> None:
        X_train = train_frame[ALL_FEATURE_COLUMNS].values
        y_price, y_drop = train_frame["future_price"].values, train_frame["price_will_drop"].values
        self.xgb_regressor = train_price_regressor(X_train, y_price, seed=self.seed)
        self.xgb_classifier = train_price_drop_classifier(X_train, y_drop, seed=self.seed)
        self.lstm = LSTMPricePredictor(seed=self.seed).fit(X_train, y_price)

    def evaluate(self) -> dict[str, RegressionMetrics | ClassificationMetrics]:
        """Holdout metrics for all three models, after `.fit()` (not `.fit_final()`)."""
        X_test = self.test_frame_[ALL_FEATURE_COLUMNS].values
        y_test_price, y_test_drop = self.test_frame_["future_price"].values, self.test_frame_["price_will_drop"].values

        results: dict[str, RegressionMetrics | ClassificationMetrics] = {
            "XGBoost (price regression)": evaluate_regression("XGBoost (price regression)", y_test_price, self.xgb_regressor.predict(X_test)),
            "XGBoost (price-drop classifier)": evaluate_classification("XGBoost (price-drop classifier)", y_test_drop, self.xgb_classifier.predict(X_test)),
        }

        cutoff_index = len(self.full_frame_) - len(self.test_frame_)
        context_and_test = self.full_frame_.iloc[max(cutoff_index - (SEQUENCE_LENGTH - 1), 0):]
        seq_X, seq_y = make_sequences(context_and_test[ALL_FEATURE_COLUMNS].values, context_and_test["future_price"].values, SEQUENCE_LENGTH)
        results["LSTM (price regression)"] = evaluate_regression("LSTM (price regression)", seq_y, self.lstm.predict(seq_X))

        prophet_forecast = self.prophet.forecast(len(self.test_frame_) + self.horizon_days)
        on_test = prophet_forecast.merge(self.test_frame_[["date", "price_minor"]], on="date", how="inner")
        if len(on_test):
            results["Prophet (price regression)"] = evaluate_regression("Prophet (price regression)", on_test["price_minor"].values, on_test["yhat"].values)
        return results

    def predict(self) -> PricePrediction:
        """Forecast `horizon_days` beyond the last observed date, ensembling all three models. Call after `.fit_final()`."""
        latest = self.full_frame_.iloc[[-1]]
        xgb_price = float(self.xgb_regressor.predict(latest[ALL_FEATURE_COLUMNS].values)[0])
        drop_probability = float(self.xgb_classifier.predict_proba(latest[ALL_FEATURE_COLUMNS].values)[0, 1])

        window = self.full_frame_.iloc[-SEQUENCE_LENGTH:][ALL_FEATURE_COLUMNS].values[None, :, :]
        lstm_price = float(self.lstm.predict(window)[0])

        last_date = self.full_frame_["date"].iloc[-1]
        target_date = last_date + pd.Timedelta(days=self.horizon_days)
        prophet_forecast = self.prophet.forecast(self.horizon_days)
        prophet_row = prophet_forecast[prophet_forecast["date"] == target_date]
        prophet_price = float(prophet_row["yhat"].iloc[0]) if len(prophet_row) else xgb_price

        ensemble_price = float(np.mean([xgb_price, lstm_price, prophet_price]))
        return PricePrediction(expected_future_price_minor=ensemble_price, price_drop_probability=drop_probability, component_forecasts={"prophet": prophet_price, "xgboost": xgb_price, "lstm": lstm_price})
