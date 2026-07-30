"""Prophet: models trend + weekly/yearly seasonality + named sale-event effects directly on the raw price series.

Prophet is the only one of the three models handed the sale-event calendar directly, as its `holidays`
regressor - it's purpose-built to fit a dedicated effect size per named event (with a +/-1 day window),
which is exactly what "sales events" as an input calls for. Its fitted in-sample components (trend, yearly
seasonality, weekly seasonality, holiday effect) are also exposed as engineered features for XGBoost - a
standard hybrid-forecasting trick: let Prophet's additive model do the interpretable decomposition, then
let the tree model capture whatever nonlinear interaction is left on top of it.
"""
import pandas as pd
from prophet import Prophet
from ml.price_prediction.sale_events import sale_events_calendar

PROPHET_COMPONENT_COLUMNS = {"trend": "prophet_trend", "yearly": "prophet_yearly", "weekly": "prophet_weekly", "holidays": "prophet_holiday_effect"}


class ProphetPriceModel:
    def __init__(self, interval_width: float = 0.8):
        self.interval_width = interval_width
        self.model: Prophet | None = None

    def fit(self, price_series: pd.DataFrame) -> "ProphetPriceModel":
        """price_series: columns [date, price_minor]."""
        calendar = sale_events_calendar(price_series["date"].min().year - 1, price_series["date"].max().year + 2)
        self.model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False, holidays=calendar, interval_width=self.interval_width)
        self.model.fit(price_series.rename(columns={"date": "ds", "price_minor": "y"})[["ds", "y"]])
        return self

    def in_sample_components(self, dates: pd.Series) -> pd.DataFrame:
        """Fitted trend/seasonal/holiday components for historical dates, to merge in as XGBoost features."""
        forecast = self.model.predict(pd.DataFrame({"ds": dates}))
        available = {source: target for source, target in PROPHET_COMPONENT_COLUMNS.items() if source in forecast.columns}
        result = forecast[["ds", *available.keys()]].rename(columns={"ds": "date", **available})
        for target in PROPHET_COMPONENT_COLUMNS.values():
            if target not in result.columns:
                result[target] = 0.0
        return result

    def forecast(self, horizon_days: int) -> pd.DataFrame:
        """Point forecast (yhat) plus an 80% uncertainty interval for the next `horizon_days` beyond the fitted data."""
        future = self.model.make_future_dataframe(periods=horizon_days)
        forecast = self.model.predict(future)
        return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(horizon_days).rename(columns={"ds": "date"})
