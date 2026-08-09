"""Live cross-retailer price comparison. There's no free API that returns structured multi-retailer price
data directly (Amazon/Google Shopping APIs are paid or partner-gated), so this composes two building
blocks already used elsewhere in this app: a live Tavily web search, then Gemini structured extraction to
turn raw search snippets into real {retailer, price, url} listings.

The app is India-focused (catalog and every other page price in INR), so the search itself is biased
toward Indian retailers/pricing, and any listing that still comes back in another currency is converted to
INR rather than shown as-is - the shopper should never see a stray "$248" next to a page full of "₹".
"""
import json
import re
from dataclasses import dataclass
from urllib.parse import urlparse
from app.core.config import get_settings
from app.core.currency import convert_to_inr
from app.infrastructure.llm import create_message
from app.infrastructure.web_search import search_web
from app.services.web_product_search import EXCLUDED_DOMAINS, INDIAN_RETAIL_DOMAINS, retailer_label

# The "reject category pages" prompt instruction alone isn't reliably followed - confirmed live: asked for
# "red saree", the model picked Myntra's category page (myntra.com/red-saree) over a genuine single-product
# Flipkart listing (.../red-saree-.../p/itm2fb3600ad222f) that was right there in the same search results.
# This is a structural backstop: each of these retailers' own real single-product page URLs consistently
# contain a distinct marker a category/collection page never has (confirmed live for each) - a listing whose
# url doesn't match gets dropped rather than trusted on the model's judgment alone. Domains with no known
# rule aren't filtered - better to trust the prompt there than risk dropping a genuinely good listing over a
# guessed pattern.
_SINGLE_PRODUCT_URL_MARKERS = {
    "flipkart.com": re.compile(r"/p/"),
    "shopsy.in": re.compile(r"/p/"),
    "amazon.in": re.compile(r"/dp/"),
    "meesho.com": re.compile(r"/p/"),
    "croma.com": re.compile(r"/p/"),
    "myntra.com": re.compile(r"/\d+/buy/?$"),
}


def _is_single_product_url(url: str) -> bool:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    for domain, marker in _SINGLE_PRODUCT_URL_MARKERS.items():
        if domain in host:
            return bool(marker.search(url))
    return True  # no known rule for this domain - don't filter what we can't verify

# News/spec-comparison/aggregator sites - real, useful sources for the recommendation engine's product
# *discovery* (see web_product_search.py), but never an actual page a shopper can check out from, which is
# the one thing this feature promises ("direct navigation to buy"). Confirmed live: a gadgets360.com article
# that merely mentions a Flipkart price was otherwise coming back labelled "Flipkart" and linking to the
# article itself, not anything purchasable - excluded here rather than in the shared EXCLUDED_DOMAINS list,
# since web_product_search.py's discovery stage intentionally wants roundup/news articles as a source.
NON_PURCHASABLE_DOMAINS = EXCLUDED_DOMAINS + [
    "gadgets360.com", "91mobiles.com", "gsmarena.com", "smartprix.com", "pricebaba.com",
    "mysmartprice.com", "pricehistory.app", "cashify.in", "livemint.com", "digit.in", "gizbot.com",
]

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


def compare_prices(product_name: str, max_results: int = 15) -> list[PriceListing]:
    """Search the live web for `product_name` and extract real shopping listings with prices - one result
    (the cheapest found) per retailer, sorted lowest price first, always priced in INR.

    Searches the major Indian retailers first (Amazon.in, Flipkart, Myntra, Meesho, Shopsy, Croma, etc.) -
    confirmed live this was missing: an unrestricted search can rank a small/unfamiliar site above Flipkart
    or Amazon entirely, or not surface them at all even when the product is clearly available there, which
    both undermines "prefer major retailers" (nothing to prefer if they're not in the candidate pool) and
    can show a stale/wrong price from a less reliable source as if it were the best deal. Only broadens to an
    unrestricted search if the major retailers genuinely have nothing for this query.

    max_results defaults higher than it used to (was 8): confirmed live, searching "OPPO K14x 5G" returned 8
    results that were entirely Flipkart review pages plus an unrelated screen-protector listing - correctly
    rejected by the single-product-page filter below, leaving nothing. The real Flipkart/Amazon product pages
    were there, just past the top 8; asking for more results up front reliably surfaces them."""
    query = f"{product_name} price in India buy online"
    results = search_web(query, max_results=max_results, include_domains=INDIAN_RETAIL_DOMAINS, exclude_domains=NON_PURCHASABLE_DOMAINS)
    if not results:
        results = search_web(query, max_results=max_results, exclude_domains=NON_PURCHASABLE_DOMAINS)
    if not results:
        return []

    settings = get_settings()
    context = "\n\n".join(f"[{r.label}] {r.title} ({r.url})\n{r.snippet}" for r in results)
    response = create_message(
        model=settings.recommendation_model,
        max_tokens=1024,
        system=(
            "You extract real shopping listings from web search results for one specific product, for a "
            "shopper in India. Only include a result if it is that one specific product's own page with its "
            "own specific price - never a category, collection, or search-results page listing many "
            "different products (e.g. a url/title like 'white-sarees', '/womens-sarees/white~color', or a "
            "generic search page), even if its headline 'starting from ₹X' price looks like a real price - "
            "that price belongs to whichever cheapest item happens to be in that category, not to the "
            "product actually being searched for. If the product name states specific attributes (color, "
            "material, style, size, etc.), only include a listing whose own text actually confirms it has "
            "those same attributes - never substitute a different color or variant just because it's a "
            "similar product; skip it instead if no matching listing is found. Also skip review sites, news "
            "articles, blogs, forums, and any result with no price mentioned. Prefer Indian retailers "
            "(Amazon.in, Flipkart, Shopsy, Myntra, Meesho, Croma, Reliance Digital, Tata Cliq, Vijay Sales, "
            "etc.) and INR prices when the search results contain them. When a source "
            "states more than one price for the same listing (a struck-through original/MRP price alongside "
            "a discounted/sale/bank-offer price - retailer pages list the original first), always use the "
            "lower, current discounted price the shopper would actually pay, never the crossed-out original. "
            "Never invent a price or retailer that is not present in the source text."
        ),
        messages=[{"role": "user", "content": f"Product: {product_name}\n\nSearch results:\n{context}"}],
        output_config={"format": {"type": "json_schema", "schema": LISTING_SCHEMA}},
    )
    if response.stop_reason == "refusal":
        return []

    payload = json.loads(response.content[0].text)
    listings = [
        # The displayed retailer name is derived from the URL itself, not trusted from the LLM's own
        # "retailer" field - confirmed live, a listing can come back labelled "Flipkart" while its url is
        # actually a news article that merely mentions a Flipkart price, which is not a page a shopper can
        # buy from. Deriving from the url guarantees the label always matches where the link actually goes.
        PriceListing(retailer=retailer_label(item["url"]), price=convert_to_inr(item["price"], item["currency"]), currency="INR", url=item["url"])
        for item in payload["listings"]
        if item["price"] is not None and _is_single_product_url(item["url"])
    ]

    cheapest_per_retailer: dict[str, PriceListing] = {}
    for listing in listings:
        existing = cheapest_per_retailer.get(listing.retailer)
        if existing is None or listing.price < existing.price:
            cheapest_per_retailer[listing.retailer] = listing
    return sorted(cheapest_per_retailer.values(), key=lambda listing: listing.price)
