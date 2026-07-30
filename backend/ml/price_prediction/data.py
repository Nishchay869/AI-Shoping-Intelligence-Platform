"""Historical price time series: a synthetic generator for demo/testing, and a loader for real offer data.

The synthetic generator isn't just noise around a flat line - it composes a slow price-creep trend, a
yearly seasonal wave, a tiny weekend effect, sale-event-driven discount dips (from sale_events.py), and
occasional off-calendar flash sales, so the resulting series actually has the structure (trend + seasonality
+ event effects) the three models are each built to capture. For production, replace
`generate_synthetic_price_series()` with `load_price_history_from_db()` against a real `product_offers` /
`price_history` pair.
"""
from uuid import UUID
import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session
from ml.price_prediction.sale_events import is_sale_event_day, sale_events_calendar


def generate_synthetic_price_series(start_date: str = "2022-01-01", n_days: int = 900, base_price_minor: int = 500_000, seed: int = 42) -> pd.DataFrame:
    """Build a daily [date, price_minor, is_available] series with realistic trend/seasonality/discount structure."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start_date, periods=n_days, freq="D")
    day_index = np.arange(n_days)

    trend = base_price_minor * (1 + 0.00015 * day_index)                          # slow list-price creep
    yearly_wave = 0.05 * np.sin(2 * np.pi * (dates.dayofyear.values / 365.25))     # +/-5% seasonal swing
    weekend_bump = np.where(dates.weekday.values >= 5, 0.01, 0.0)                  # small weekend effect
    daily_noise = rng.normal(0, 0.01, n_days)
    list_price = trend * (1 + yearly_wave + weekend_bump) * (1 + daily_noise)

    calendar = sale_events_calendar(dates[0].year - 1, dates[-1].year + 2)         # buffer years for edge lookups
    on_sale_event = is_sale_event_day(pd.Series(dates), calendar)
    discount = np.where(on_sale_event, rng.uniform(0.12, 0.35, n_days), rng.uniform(0.0, 0.05, n_days))
    flash_sale = rng.random(n_days) < 0.03                                        # occasional off-calendar flash sales
    discount = np.where(flash_sale, np.maximum(discount, rng.uniform(0.10, 0.25, n_days)), discount)

    price = np.round(list_price * (1 - discount)).astype(np.int64)
    is_available = rng.random(n_days) > 0.01                                       # rare stockouts

    return pd.DataFrame({"date": dates, "price_minor": price, "is_available": is_available})


def load_price_history_from_db(db: Session, offer_id: UUID) -> pd.DataFrame:
    """Load a real offer's price history, resampled to a daily grid (forward-filled across observation gaps)."""
    from app.models import PriceHistory  # imported lazily so this module doesn't require the FastAPI app at import time

    rows = db.execute(select(PriceHistory.observed_at, PriceHistory.price_minor, PriceHistory.is_available).where(PriceHistory.offer_id == offer_id).order_by(PriceHistory.observed_at)).all()
    if not rows:
        raise ValueError(f"No price history recorded for offer {offer_id}")
    frame = pd.DataFrame(rows, columns=["date", "price_minor", "is_available"])
    frame["date"] = pd.to_datetime(frame["date"]).dt.tz_localize(None).dt.normalize()
    return frame.drop_duplicates("date").set_index("date").asfreq("D").ffill().reset_index()
