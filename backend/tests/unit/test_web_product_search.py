"""Unit tests: web_product_search.py's price extraction - no DB, no network."""
from app.services.web_product_search import _extract_price_inr


def test_picks_the_discounted_price_not_the_struck_original() -> None:
    """Retailer listing text states the original/MRP price before the discounted one - confirmed live on
    Flipkart ("₹34,000" / "₹21,999" / "₹19,924 with Bank offer" in that order). The shopper should be shown
    the lowest (the price they'd actually pay), never the first/highest one mentioned."""
    text = "₹34,000\n₹21,999\n₹19,924 with Bank offer"
    assert _extract_price_inr(text) == 19_924.0


def test_single_price_is_returned_as_is() -> None:
    assert _extract_price_inr("Only ₹9,999 today") == 9_999.0


def test_ignores_small_figures_like_fees_or_ratings() -> None:
    """A guard against matching an EMI/fee line rather than the actual product price - anything under ₹1,000 is skipped."""
    assert _extract_price_inr("EMI from ₹999/month, price ₹45,000") == 45_000.0


def test_returns_none_when_no_price_is_present() -> None:
    assert _extract_price_inr("No pricing information available") is None


def test_discount_amount_and_emi_installment_are_not_mistaken_for_the_price() -> None:
    """Confirmed live on Flipkart: a listing can mention only a discount *amount* ("₹1,975 off") and an EMI
    *installment* ("₹1,757 x 36m") without the raw crawled snippet actually containing the real price at all
    - both must be excluded rather than picked up as if they were (smaller) real prices."""
    assert _extract_price_inr("₹1,975 off\nAdditional ₹500 off | No Cost EMI") is None
    assert _extract_price_inr("₹49,949\nBuy at ₹46,976\nOR\n₹1,757 x 36m\nPay ₹63,219") == 46_976.0


def test_mrp_label_pattern_still_picks_the_labelled_price() -> None:
    text = "MRP: | ₹19999 |\nPrice: ₹11494 | (₹11494 / pc) |\nYou Save: | 43% OFF |"
    assert _extract_price_inr(text) == 11_494.0


def test_exchange_offer_credit_is_not_mistaken_for_a_lower_real_price() -> None:
    """Confirmed live on Flipkart: a listing's real price ("Buy at ₹16,599") can coexist with a smaller,
    unrelated "Up to ₹16,100" exchange/trade-in credit figure - a plain minimum-of-all-numbers approach picks
    the exchange credit since it's numerically smaller, even though it is not a price at all."""
    text = "₹17,999+₹156 Protect Promise Fee\nBuy at ₹16,599\nApply offers for maximum savings\n₹16,599\nLowest price for you\nExchange offer\nUp to ₹16,100\nChange pincode to exchange item"
    assert _extract_price_inr(text) == 16_599.0
