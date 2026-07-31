"""Approximate currency conversion to INR - shared by anything that needs to normalize a price found in a
different currency (the AI shopping assistant's tool results, live web price comparisons) into INR. The
rate table is a fixed approximation, not a live feed - a shopping guide doesn't need to be a financial
instrument, and a clearly-approximate figure is more honest than a stale "precise-looking" one anyway.
"""

APPROX_RATE_TO_INR = {"INR": 1.0, "USD": 83.0, "EUR": 90.0, "GBP": 105.0}
DEFAULT_RATE_TO_INR = 83.0  # fallback for any currency not in the table above


def convert_to_inr(amount: float, currency: str) -> float:
    """Convert a major-unit amount (e.g. rupees/dollars, not paise/cents) in `currency` to INR."""
    rate = APPROX_RATE_TO_INR.get(currency.upper(), DEFAULT_RATE_TO_INR)
    return round(amount * rate, 2)


def to_inr(amount_minor: int, currency: str) -> str:
    """Convert a minor-unit amount (e.g. paise/cents) in `currency` to a formatted INR string, e.g. '₹66,317'."""
    return f"₹{convert_to_inr(amount_minor / 100, currency):,.0f}"
