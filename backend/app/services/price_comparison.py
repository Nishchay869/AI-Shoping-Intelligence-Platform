"""Live cross-retailer price comparison. There's no free API that returns structured multi-retailer price
data directly (Amazon/Google Shopping APIs are paid or partner-gated), so this composes two building
blocks already used elsewhere in this app: a live Tavily web search, then Gemini structured extraction to
turn raw search snippets into real {retailer, price, url} listings.

The app is India-focused (catalog and every other page price in INR), so the search itself is biased
toward Indian retailers/pricing, and any listing that still comes back in another currency is converted to
INR rather than shown as-is - the shopper should never see a stray "$248" next to a page full of "₹".
"""
import json
from dataclasses import dataclass
from app.core.config import get_settings
from app.core.currency import convert_to_inr
from app.infrastructure.llm import create_message
from app.infrastructure.web_search import search_web

LISTING_SCHEMA = {
    "type": "object",
    "properties": {
        "listings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "retailer": {"type": "string", "description": "The store/retailer name, e.g. 'Amazon', 'Flipkart', 'Croma' - not the raw domain or URL."},
                    "price": {"type": ["number", "null"], "description": "The numeric price in major currency units (e.g. 24990, not 2499000 paise). Null if this result has no stated price."},
                    "currency": {"type": "string", "description": "ISO 4217 currency code (e.g. INR, USD), inferred from the site or price format."},
                    "url": {"type": "string", "description": "The exact source URL for this listing."},
                },
                "required": ["retailer", "price", "currency", "url"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["listings"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class PriceListing:
    retailer: str
    price: float
    currency: str
    url: str


def compare_prices(product_name: str, max_results: int = 8) -> list[PriceListing]:
    """Search the live web for `product_name` and extract real shopping listings with prices - one result
    (the cheapest found) per retailer, sorted lowest price first, always priced in INR."""
    results = search_web(f"{product_name} price in India buy online", max_results=max_results)
    if not results:
        return []

    settings = get_settings()
    context = "\n\n".join(f"[{r.label}] {r.title} ({r.url})\n{r.snippet}" for r in results)
    response = create_message(
        model=settings.recommendation_model,
        max_tokens=1024,
        system=(
            "You extract real shopping listings from web search results for one product, for a shopper in "
            "India. Only include results that are an actual listing on a shopping/retailer site with a "
            "clearly stated price - skip review sites, news articles, blogs, forums, and any result with no "
            "price mentioned. Prefer Indian retailers (Amazon.in, Flipkart, Croma, Reliance Digital, "
            "Tata Cliq, Vijay Sales, etc.) and INR prices when the search results contain them. Never invent "
            "a price or retailer that is not present in the source text."
        ),
        messages=[{"role": "user", "content": f"Product: {product_name}\n\nSearch results:\n{context}"}],
        output_config={"format": {"type": "json_schema", "schema": LISTING_SCHEMA}},
    )
    if response.stop_reason == "refusal":
        return []

    payload = json.loads(response.content[0].text)
    listings = [
        PriceListing(retailer=item["retailer"], price=convert_to_inr(item["price"], item["currency"]), currency="INR", url=item["url"])
        for item in payload["listings"]
        if item["price"] is not None
    ]

    cheapest_per_retailer: dict[str, PriceListing] = {}
    for listing in listings:
        existing = cheapest_per_retailer.get(listing.retailer)
        if existing is None or listing.price < existing.price:
            cheapest_per_retailer[listing.retailer] = listing
    return sorted(cheapest_per_retailer.values(), key=lambda listing: listing.price)
