"""Train, evaluate, and run a live forecast for the price-prediction pipeline (Prophet + LSTM + XGBoost).

Setup (from backend/, in the venv):
    pip install -r ml/requirements.txt
    python -m cmdstanpy.install_cmdstan   # one-time: compiles Prophet's Stan backend

Usage:
    python -m ml.price_prediction.train                      # synthetic demo series, 900 days
    python -m ml.price_prediction.train --n-days 1500 --horizon-days 14

macOS note: PyTorch and XGBoost each bundle their own OpenMP runtime, which crashes with a segfault the
moment both are loaded in one process unless you set (this is a well-known upstream issue, not specific to
this code - the same crash happens with any script that imports both libraries on macOS):
    KMP_DUPLICATE_LIB_OK=TRUE python -m ml.price_prediction.train
"""
import argparse
import joblib
from pathlib import Path
from ml.price_prediction.data import generate_synthetic_price_series
from ml.price_prediction.pipeline import PricePredictionPipeline

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"


def train_and_evaluate(n_days: int = 900, horizon_days: int = 30, test_size: float = 0.2, seed: int = 42, save_artifacts: bool = True) -> dict:
    print("Loading price history...")
    history = generate_synthetic_price_series(n_days=n_days, seed=seed)
    print(f"  {len(history)} days, price range {history['price_minor'].min():,} - {history['price_minor'].max():,} (minor units)")

    print(f"\nFitting on the training split (holding out the last {test_size:.0%}, purged by the {horizon_days}-day horizon)...")
    pipeline = PricePredictionPipeline(horizon_days=horizon_days, test_size=test_size, seed=seed)
    pipeline.fit(history)

    print("\nHoldout evaluation:")
    for metrics in pipeline.evaluate().values():
        print("\n" + metrics.report())

    print("\nRefitting on the full series for the live forecast...")
    pipeline.fit_final(history)
    prediction = pipeline.predict()
    last_price = history["price_minor"].iloc[-1]
    print(f"\nLast observed price      : {last_price:,}")
    print(f"Expected price in {horizon_days:>3}d   : {prediction.expected_future_price_minor:,.0f}  (Prophet={prediction.component_forecasts['prophet']:,.0f}, XGBoost={prediction.component_forecasts['xgboost']:,.0f}, LSTM={prediction.component_forecasts['lstm']:,.0f})")
    print(f"Probability of price drop: {prediction.price_drop_probability:.1%}")

    if save_artifacts:
        ARTIFACT_DIR.mkdir(exist_ok=True)
        artifact_path = ARTIFACT_DIR / "price_prediction_model.joblib"
        joblib.dump({"xgb_regressor": pipeline.xgb_regressor, "xgb_classifier": pipeline.xgb_classifier, "lstm": pipeline.lstm}, artifact_path)
        print(f"\nSaved XGBoost + LSTM artifacts to {artifact_path} (Prophet is refit fresh each run - see module docstring).")

    return {"prediction": prediction}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--n-days", type=int, default=900, help="Synthetic price history length in days.")
    parser.add_argument("--horizon-days", type=int, default=30, help="How many days ahead to predict.")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    train_and_evaluate(n_days=args.n_days, horizon_days=args.horizon_days, test_size=args.test_size, seed=args.seed)
