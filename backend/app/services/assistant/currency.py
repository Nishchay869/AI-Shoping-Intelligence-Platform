"""Approximate currency conversion so the AI shopping assistant always quotes catalog prices in INR,
regardless of what currency a product is actually listed in. The rate table is a fixed approximation, not a
live feed - the assistant is a shopping guide, not a financial instrument, and a clearly-approximate figure
is more honest than a stale "precise-looking" one anyway.
"""

APPROX_RATE_TO_INR = {"INR": 1.0, "USD": 83.0, "EUR": 90.0, "GBP": 105.0}
DEFAULT_RATE_TO_INR = 83.0  # fallback for any currency not in the table above


def to_inr(amount_minor: int, currency: str) -> str:
    """Convert a minor-unit amount (e.g. paise/cents) in `currency` to a formatted INR string, e.g. '₹66,317'."""
    rate = APPROX_RATE_TO_INR.get(currency.upper(), DEFAULT_RATE_TO_INR)
    inr_amount = (amount_minor / 100) * rate
    return f"₹{inr_amount:,.0f}"
