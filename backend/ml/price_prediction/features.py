"""Tabular feature engineering shared by XGBoost and the LSTM.

The four requested inputs become concrete columns here:
  - Historical prices -> the current price itself, lagged prices (t-1/7/14/30), and rolling mean/std over
                          multiple windows, so the models see both recent momentum and longer-run level.
  - Discounts         -> percent off a rolling "reference price" (a trailing 90-day rolling max, the same
                          trick real price-tracking tools use to estimate a historical list price when no
                          separate MRP field exists), a binary discounted flag, and a 30-day discount
                          frequency (how promotion-heavy this product's recent history has been).
  - Season            -> cyclical sin/cos encodings of day-of-week and day-of-year. Raw integers (month=12,
                          month=1) look maximally *far apart* to a tree split or an LSTM gate even though
                          the calendar wraps - sin/cos encoding fixes that, the same reason Prophet models
                          seasonality with Fourier terms internally.
  - Sale events        -> days to the next / since the last known sale event, and a same-day indicator,
                          from sale_events.py's calendar.

All rolling/lag windows are strictly causal (computed only from data up to and including the row's own
date), so nothing here needs shifting to avoid leakage - the leakage risk in this pipeline is entirely on
the *target* side (a future price), handled by `make_supervised`, not the feature side.
"""
import numpy as np
import pandas as pd
from ml.price_prediction.sale_events import days_since_last_event, days_to_next_event, is_sale_event_day, sale_events_calendar

LAG_DAYS = [1, 7, 14, 30]
ROLLING_WINDOWS = [7, 14, 30]
REFERENCE_PRICE_WINDOW = 90
DISCOUNT_THRESHOLD = 0.02

FEATURE_COLUMNS = (
    ["price_minor"]
    + [f"price_lag_{lag}" for lag in LAG_DAYS]
    + [f"price_rolling_mean_{window}" for window in ROLLING_WINDOWS]
    + [f"price_rolling_std_{window}" for window in ROLLING_WINDOWS]
    + ["discount_pct", "is_discounted", "discount_frequency_30d", "day_of_week", "month", "is_weekend",
       "dow_sin", "dow_cos", "doy_sin", "doy_cos", "is_sale_event_today", "days_to_next_sale_event", "days_since_last_sale_event"]
)


def build_features(price_series: pd.DataFrame) -> pd.DataFrame:
    """price_series: columns [date, price_minor, is_available] on a daily grid, sorted by date."""
    frame = price_series.sort_values("date").reset_index(drop=True).copy()
    price = frame["price_minor"].astype(float)

    for lag in LAG_DAYS:
        frame[f"price_lag_{lag}"] = price.shift(lag)
    for window in ROLLING_WINDOWS:
        frame[f"price_rolling_mean_{window}"] = price.rolling(window).mean()
        frame[f"price_rolling_std_{window}"] = price.rolling(window).std()

    reference_price = price.rolling(REFERENCE_PRICE_WINDOW, min_periods=7).max()
    frame["discount_pct"] = (1 - price / reference_price).clip(lower=0)
    frame["is_discounted"] = (frame["discount_pct"] > DISCOUNT_THRESHOLD).astype(int)
    frame["discount_frequency_30d"] = frame["is_discounted"].rolling(30).mean()

    frame["day_of_week"] = frame["date"].dt.weekday
    frame["day_of_year"] = frame["date"].dt.dayofyear
    frame["month"] = frame["date"].dt.month
    frame["is_weekend"] = (frame["day_of_week"] >= 5).astype(int)
    frame["dow_sin"] = np.sin(2 * np.pi * frame["day_of_week"] / 7)
    frame["dow_cos"] = np.cos(2 * np.pi * frame["day_of_week"] / 7)
    frame["doy_sin"] = np.sin(2 * np.pi * frame["day_of_year"] / 365.25)
    frame["doy_cos"] = np.cos(2 * np.pi * frame["day_of_year"] / 365.25)

    calendar = sale_events_calendar(frame["date"].min().year - 1, frame["date"].max().year + 2)
    frame["is_sale_event_today"] = is_sale_event_day(frame["date"], calendar).astype(int)
    frame["days_to_next_sale_event"] = days_to_next_event(frame["date"], calendar)
    frame["days_since_last_sale_event"] = days_since_last_event(frame["date"], calendar)
    return frame


def make_supervised(features: pd.DataFrame, horizon_days: int, price_drop_threshold: float = 0.02) -> pd.DataFrame:
    """Attach the two targets, `horizon_days` ahead: a regression target (future_price) and a classification
    target (price_will_drop = 1 if the future price is at least `price_drop_threshold` below today's)."""
    frame = features.copy()
    frame["future_price"] = frame["price_minor"].shift(-horizon_days)
    frame["price_will_drop"] = (frame["future_price"] < frame["price_minor"] * (1 - price_drop_threshold)).astype(int)
    return frame
