"""Recurring e-commerce sale-event calendar - the concrete form of the "Sales events" input.

This calendar is consumed two ways: (1) directly as Prophet's `holidays` regressor, so Prophet learns a
dedicated price effect for each named event instead of folding sale-driven dips into generic yearly
seasonality; (2) as the source for "days to next/since last sale event" tabular features fed to XGBoost
and the LSTM, which have no built-in notion of a holiday calendar the way Prophet does.

Black Friday and Cyber Monday are floating US retail dates (computed properly per year); the rest are
fixed calendar dates. Adjust `FIXED_SALE_EVENTS` to match the actual promotional calendar of the catalog
being modeled - a lunar-calendar event like Diwali is approximated here with a fixed placeholder date.
"""
from datetime import date, timedelta
import numpy as np
import pandas as pd

FIXED_SALE_EVENTS: list[tuple[str, int, int]] = [
    ("New Year Sale", 1, 1),
    ("Republic Day Sale", 1, 26),
    ("Summer Sale Kickoff", 6, 1),
    ("Independence Day Sale", 8, 15),
    ("Festive Season Sale", 10, 15),   # placeholder window for a lunar-calendar event (e.g. Diwali)
    ("Christmas Sale", 12, 25),
    ("Year End Clearance", 12, 31),
]


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """The date of the nth occurrence of `weekday` (Monday=0) in the given month/year."""
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def sale_events_calendar(start_year: int, end_year: int) -> pd.DataFrame:
    """Prophet-compatible holidays frame (columns: holiday, ds, lower_window, upper_window) with a +/-1 day effect window."""
    rows: list[tuple[str, date]] = []
    for year in range(start_year, end_year + 1):
        rows.extend((name, date(year, month, day)) for name, month, day in FIXED_SALE_EVENTS)
        black_friday = _nth_weekday(year, 11, 3, 4) + timedelta(days=1)  # day after the 4th Thursday of November
        rows.append(("Black Friday", black_friday))
        rows.append(("Cyber Monday", black_friday + timedelta(days=3)))
    frame = pd.DataFrame(rows, columns=["holiday", "ds"]).sort_values("ds").reset_index(drop=True)
    frame["ds"] = pd.to_datetime(frame["ds"])
    frame["lower_window"] = -1
    frame["upper_window"] = 1
    return frame


def _event_day_ordinals(events: pd.DataFrame) -> np.ndarray:
    return np.sort(events["ds"].values.astype("datetime64[D]").astype(np.int64))


def days_to_next_event(as_of: pd.Series, events: pd.DataFrame) -> np.ndarray:
    """Calendar days until the nearest upcoming sale event on or after each date (requires the calendar to extend past `as_of`)."""
    event_days = _event_day_ordinals(events)
    query_days = pd.to_datetime(as_of).values.astype("datetime64[D]").astype(np.int64)
    idx = np.clip(np.searchsorted(event_days, query_days, side="left"), 0, len(event_days) - 1)
    return event_days[idx] - query_days


def days_since_last_event(as_of: pd.Series, events: pd.DataFrame) -> np.ndarray:
    """Calendar days since the most recent past sale event for each date (requires the calendar to start before `as_of`)."""
    event_days = _event_day_ordinals(events)
    query_days = pd.to_datetime(as_of).values.astype("datetime64[D]").astype(np.int64)
    idx = np.clip(np.searchsorted(event_days, query_days, side="right") - 1, 0, len(event_days) - 1)
    return query_days - event_days[idx]


def is_sale_event_day(as_of: pd.Series, events: pd.DataFrame) -> np.ndarray:
    """Binary flag: does this date fall within a sale event's +/-1 day effect window?"""
    return (np.abs(days_to_next_event(as_of, events)) <= 1) | (np.abs(days_since_last_event(as_of, events)) <= 1)
