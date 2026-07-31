"""Live web-wide product discovery: there is no meaningful internal catalog to fall back to, so every
recommendation comes from a real, live listing search - title, brand, price, image, retailer, link, and a
grounded reason - ranked by fit to the shopper's stated need (not just price). Also looks up real review
excerpts for the single best-fit listing, via the same search-then-extract pattern applied to review content
instead of product listings.
"""
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, replace
from urllib.parse import urlparse
import httpx
from app.core.config import get_settings
from app.core.currency import convert_to_inr
from app.infrastructure.llm import create_message, verify_product_photos
from app.infrastructure.web_search import search_web

logger = logging.getLogger(__name__)

# Major Indian retailers first: their listing pages have accurate prices/retailer names and clean product
# packshots, unlike review/news/blog sites, whose "images" are often marketing banners or article art that
# read as blurry/misleading when shown as a product photo. Falls back to an unrestricted search (see
# _search_listings) so a niche product these retailers don't stock still returns something.
INDIAN_RETAIL_DOMAINS = ["amazon.in", "flipkart.com", "croma.com", "reliancedigital.in", "tatacliq.com", "vijaysales.com"]
RETAILER_NAMES = {"amazon.in": "Amazon", "flipkart.com": "Flipkart", "croma.com": "Croma", "reliancedigital.in": "Reliance Digital", "tatacliq.com": "Tata Cliq", "vijaysales.com": "Vijay Sales"}

# A resolved page's own "images" list is site-wide (nav sprites, logos, tracking pixels), not just its
# product gallery - confirmed live: an Amazon product page's first image was its global nav sprite, a
# Reliance Digital page's was the site logo, another was a raw analytics beacon URL, and a Cashify one was a
# generic "Best Mobile Phones under X" listicle banner rather than a photo of the specific product. Reject
# anything matching these before trusting an image as a genuine product photo. "/images/g/" specifically
# targets Amazon's own site-chrome asset path, distinct from its real product-photo path "/images/i/".
BAD_IMAGE_PATTERNS = ("sprite", "logo", "icon", "pixel", "tracking", "uedata", "placeholder", "blank-", "favicon", "spacer", "1x1", "/images/g/", "best-mobile", "best-phone", "top-10", "top10")

# Matches a real rupee figure in crawled page text (e.g. "₹32,990", "Rs. 27,999"). >=1000 guards against
# incidentally matching a small fee/EMI line rather than the actual product price.
PRICE_PATTERN = re.compile(r"(?:₹|Rs\.?\s?|INR\s?)\s?([\d]{1,3}(?:,\d{2,3})+|\d{4,7})")

DISCOVERY_MAX_CANDIDATES = 15
MAX_LISTINGS = 10

LISTING_SCHEMA = {
    "type": "object",
    "properties": {
        "listings": {
            "type": "array",
            "maxItems": DISCOVERY_MAX_CANDIDATES,
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The specific product name/model, e.g. 'Sony WH-1000XM5'."},
                    "brand": {"type": ["string", "null"], "description": "Brand name if identifiable from the source, else null."},
                    "retailer": {"type": "string", "description": "The store/retailer name, e.g. 'Amazon', 'Flipkart', 'Croma' - not the raw domain."},
                    "price": {"type": ["number", "null"], "description": "The numeric price in major currency units, if this source happens to state one for this exact model - null is fine and common, since the real listing price is looked up separately afterward."},
                    "currency": {"type": "string", "description": "ISO 4217 currency code (e.g. INR, USD), inferred from the site or price format."},
                    "image_url": {"type": ["string", "null"], "description": "The best matching product photo URL for this listing, copied exactly from that result's 'Candidate images' list - never invent or alter one. Null only if none of that result's candidate images plausibly show this product (e.g. only logos, banners, or unrelated thumbnails were listed)."},
                    "url": {"type": "string", "description": "The exact source URL this product was mentioned in."},
                    "reason": {"type": "string", "description": "2-3 concrete sentences on why this specific product fits the shopper's stated budget/purpose/features, citing its actual attributes - not generic praise."},
                },
                "required": ["title", "brand", "retailer", "price", "currency", "image_url", "url", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["listings"],
    "additionalProperties": False,
}

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "reviews": {
            "type": "array",
            "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "The reviewer or site name, e.g. 'GSMArena', 'Amazon customer review', '91mobiles'."},
                    "quote": {"type": "string", "description": "A short 1-2 sentence excerpt grounded in the provided search result text - never invented or exaggerated."},
                    "url": {"type": "string", "description": "The exact source URL this quote came from."},
                },
                "required": ["source", "quote", "url"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["reviews"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class WebProductListing:
    title: str
    brand: str | None
    retailer: str
    price: float | None  # None only pre-resolve; search_web_products never returns an item with a null price
    currency: str
    image_url: str | None
    url: str
    reason: str
    image_candidates: list[str] = field(default_factory=list)  # internal only - alternates for _verify_listing_images to fall back through


@dataclass(frozen=True)
class ReviewSnippet:
    source: str
    quote: str
    url: str


def _format_result(r) -> str:
    # Cap at 5 candidate images per result - Tavily returns every image found on the page (logos, icons,
    # tracking pixels included), and a long list per result blows up prompt size for no extraction benefit.
    images_block = "\nCandidate images:\n" + "\n".join(r.images[:5]) if r.images else "\nCandidate images: none"
    return f"[{r.label}] {r.title} ({r.url})\n{r.snippet}{images_block}"


def _search_listings(query: str, max_results: int):
    results = search_web(query, max_results=max_results, include_images=True, include_domains=INDIAN_RETAIL_DOMAINS)
    if results:
        return results
    # Nothing on the major retailers for this query - broaden rather than return empty.
    return search_web(query, max_results=max_results, include_images=True)


def _retailer_label(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    for domain, name in RETAILER_NAMES.items():
        if domain in host:
            return name
    return host.split(".")[0].capitalize() if host else "Retailer"


def _looks_like_product_photo(url: str) -> bool:
    if urlparse(url).path.lower().endswith(".svg"):  # vector graphics are UI chrome - never real photography
        return False
    lowered = url.lower()
    return not any(pattern in lowered for pattern in BAD_IMAGE_PATTERNS)


def _upscale_image_url(url: str) -> str:
    """Several retailer/CDN image URLs embed an explicit thumbnail size that reads as blurry once stretched
    to fill a full product card (confirmed live: a 91mobiles image capped at 271px wide, an Amazon one scaled
    to 75px, a Gadgets360 one downsized to 220px) - request a much larger rendition via each CDN's own resize
    convention instead of the tiny one Tavily happened to crawl. A no-op for any URL that matches none of these."""
    url = re.sub(r"(media-amazon\.com/images/I/[^./]+)\._[^.]+_\.(jpg|jpeg|png)", r"\1.\2", url)
    url = re.sub(r"tr=w-\d+", "tr=w-960", url)  # ImageKit-style CDNs, e.g. 91mobiles' 91-img.com
    url = re.sub(r"(rukminim\d*\.flixcart\.com/image)/\d+/\d+/", r"\1/832/832/", url)  # Flipkart
    url = re.sub(r"[?&]downsize=[^&]+", "", url)  # Gadgets360
    return url


def _is_real_product_url(url: str) -> bool:
    # Tavily occasionally returns a bare redirect stub (e.g. "/goto?url=...") instead of the actual page -
    # unusable as a "buy this" link, so only accept a proper absolute URL with a real host.
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _extract_price_inr(text: str) -> float | None:
    for match in PRICE_PATTERN.finditer(text):
        try:
            value = float(match.group(1).replace(",", ""))
        except ValueError:
            continue
        if value >= 1000:
            return value
    return None


def _resolve_listing(listing: WebProductListing) -> WebProductListing | None:
    """A discovery-stage listing's source is often a 'best phones under X' roundup article, not a page a
    shopper can actually buy from - a specific product-name search reliably surfaces the real single-product
    page instead (confirmed live: named-product queries return direct retailer/brand pages, unlike broad
    budget/purpose queries which return comparison content). Swaps in that direct link + a real photo, and
    fills in a real price straight off the page text when the discovery stage didn't have one (product-
    specific pages almost always state a price, even when the roundup that surfaced this candidate didn't).
    Returns None - dropping the candidate - only if no price can be found anywhere, since a shopper can't act
    on a product with no price."""
    results = search_web(f"{listing.title} buy price India"[:400], max_results=6, include_images=True)
    valid = [r for r in results if _is_real_product_url(r.url)]
    # Prefer a result actually hosted on an Indian storefront over a generic/global one (e.g. amazon.com
    # instead of amazon.in) - a stable sort keeps Tavily's own relevance order within each group.
    valid.sort(key=lambda r: 0 if urlparse(r.url).netloc.lower().endswith(".in") or any(d in r.url for d in INDIAN_RETAIL_DOMAINS) else 1)

    if not valid:
        price = listing.price
        if price is None:
            for r in results:
                found = _extract_price_inr(r.snippet)
                if found is not None:
                    price = found
                    break
        if price is None:
            return None
        return replace(listing, price=price, currency="INR")

    # Pick the URL and its price together, from the *same* result - pairing one result's price with a
    # different result's link (e.g. a stale price from the discovery-stage roundup article, next to a live
    # Flipkart URL) is exactly what made the price shown not match what the shopper sees after clicking
    # through. Only if none of the candidate pages state a price of their own do we fall back to whatever
    # price the discovery stage had, alongside the best-ranked link anyway.
    top = None
    price = None
    for r in valid:
        found = _extract_price_inr(r.snippet)
        if found is not None:
            top = r
            price = found
            break
    if top is None:
        top = valid[0]
        price = listing.price
    if price is None:
        return None

    # A single result's images can all be site chrome (or absent) even when a *different* candidate result
    # has a clean packshot - pool candidates across every candidate result, not just the top-ranked one's.
    # Keyword filtering alone can't catch everything (a retailer's own generic warranty/trust-badge graphic
    # passes it easily), so up to 3 alternates are kept for _verify_listing_images to fall through if a vision
    # check later rejects the first choice.
    image_candidates = []
    for r in valid:
        for img in r.images:
            if _looks_like_product_photo(img) and img not in image_candidates:
                image_candidates.append(_upscale_image_url(img))
        if len(image_candidates) >= 3:
            break
    image_candidates = image_candidates[:3]
    image_url = image_candidates[0] if image_candidates else listing.image_url
    return replace(listing, retailer=_retailer_label(top.url), url=top.url, image_url=image_url, image_candidates=image_candidates, price=price, currency="INR")


def _download_image(url: str) -> tuple[bytes, str] | None:
    try:
        response = httpx.get(url, timeout=5.0, follow_redirects=True)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        if not content_type.startswith("image/"):
            return None
        return response.content, content_type
    except Exception:
        return None


def _verify_listing_images(listings: list[WebProductListing]) -> list[WebProductListing]:
    """URL-pattern filtering catches obviously-bad images (nav sprites, logos, tracking pixels) but missed a
    real one live: Amazon's site-wide "Amazon's Choice" trust-badge graphic lives at a normal-looking
    /images/I/ path with no suspicious filename, and was showing up as the product photo for several
    unrelated laptops. Runs candidate images through Gemini vision, in priority order per listing, up to 3
    rounds - a listing's first choice failing (as with that badge) falls through to its next alternate rather
    than going straight to no image at all. Ends with genuine photos where the results support them, and an
    honest "no image" only when nothing available for that listing ever passes."""
    candidate_queues = [list(listing.image_candidates) or ([listing.image_url] if listing.image_url else []) for listing in listings]
    chosen: list[str | None] = [None] * len(listings)
    resolved = [False] * len(listings)

    for _round in range(3):
        pending_indexes = [i for i, queue in enumerate(candidate_queues) if not resolved[i] and queue]
        if not pending_indexes:
            break
        urls_this_round = {i: candidate_queues[i].pop(0) for i in pending_indexes}
        with ThreadPoolExecutor(max_workers=min(len(urls_this_round), 8) or 1) as pool:
            downloads = dict(zip(urls_this_round.keys(), pool.map(_download_image, urls_this_round.values())))

        downloaded_indexes = [i for i, data in downloads.items() if data is not None]
        for i, data in downloads.items():
            if data is None:
                resolved[i] = not candidate_queues[i]  # out of alternates - give up honestly rather than loop forever
        if not downloaded_indexes:
            continue

        verdicts = verify_product_photos([(listings[i].title, downloads[i][0], downloads[i][1]) for i in downloaded_indexes])
        for i, is_genuine in zip(downloaded_indexes, verdicts):
            if is_genuine:
                chosen[i] = urls_this_round[i]
                resolved[i] = True
            elif not candidate_queues[i]:
                resolved[i] = True

    return [replace(listing, image_url=chosen[i]) for i, listing in enumerate(listings)]


def search_web_products(purpose: str, features: list[str], budget: float | None, currency: str, brand: str | None, category: str | None = None, max_results: int = 20) -> list[WebProductListing]:
    """Search the live web for real products matching a shopper's need, ranked best-fit-first (per the LLM's
    own ordering, not just cheapest first), always priced in INR. Returns at most MAX_LISTINGS."""
    # Tavily caps queries at 400 characters, so the search query is built from short, user-typed fields only.
    # Category leads the query - it's the single strongest keyword for keeping results on-topic (a free-text
    # "purpose" like "something for daily use" gives a search engine almost nothing to anchor on otherwise).
    query_parts = [category] if category else []
    query_parts.append(purpose)
    if brand:
        query_parts.append(brand)
    query_parts.extend(features[:2])
    if budget is not None:
        query_parts.append(f"under {budget:.0f} {currency}")
    query_parts.append("buy price India")
    query = " ".join(query_parts)[:400]

    # A second, roundup-phrased query (confirmed live to return an almost entirely different set of pages
    # from the query above) widens the pool of distinct named products on offer - a single query's results
    # alone tend to name only 3-5 genuinely distinct products, nowhere near enough for a full ranked list.
    roundup_parts = ["top 10 best", category or purpose]
    if brand:
        roundup_parts.append(brand)
    if budget is not None:
        roundup_parts.append(f"under {budget:.0f} {currency}")
    roundup_parts.append("India")
    roundup_query = " ".join(roundup_parts)[:400]

    with ThreadPoolExecutor(max_workers=2) as pool:
        result_sets = list(pool.map(lambda q: _search_listings(q, max_results), [query, roundup_query]))
    seen_urls: set[str] = set()
    results = []
    for result_set in result_sets:
        for r in result_set:
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                results.append(r)
    if not results:
        return []

    settings = get_settings()
    context = "\n\n".join(_format_result(r) for r in results)
    budget_note = f"Budget ceiling: {budget:.0f} {currency}. " if budget is not None else ""
    prompt = (
        f"Stated category: {category or 'not specified - infer it from the purpose'}\n"
        f"Stated purpose: {purpose}\n"
        f"Stated must-have features: {', '.join(features) or 'none specified'}\n"
        f"Stated brand preference: {brand or 'none'}\n"
        f"{budget_note}\n"
        f"Search results:\n{context}"
    )
    response = create_message(
        model=settings.recommendation_model,
        max_tokens=3584,
        system=(
            "You compile a shortlist of real, specific, named products from live web search results for a "
            "shopper in India - including from 'best phones under X' roundup articles, which is where most of "
            "these results will come from. When a category is stated, it is a hard filter - never include a "
            "product from a different category (e.g. a phone when the stated category is Laptops), even if "
            "it fits the budget and search results mention it. Within that category, your goal is breadth: "
            "list every distinct product name that actually appears in the source text and plausibly belongs "
            "in this shopper's category and rough budget range - aim for as many as the results genuinely "
            "support (up to 15), not just the 2-3 safest picks. Being included does not require a perfect "
            "match to every stated feature - a decent, "
            "honestly-explained match ranked further down is far more useful to the shopper than an "
            "artificially short list. The only hard rule is that the product itself must be actually named in "
            "the source text - never invent one that isn't. A price is nice when the source states one, but "
            "null is fine and expected - the real listing price gets looked up separately afterward, so don't "
            "skip a plausible product just because this particular source didn't mention its price. Never "
            "invent a price, retailer, or image URL that is not present in the source text. For image_url, "
            "pick the single best genuine product photo from that result's own 'Candidate images' list - "
            "prefer clear product photography over logos, banners, icons, or tracking pixels, and use null if "
            "nothing in that result's list is a believable product photo. Never reuse an image from a "
            "different result's list. Order the listings array from best fit to worst fit for this shopper's "
            "stated purpose, features, brand preference and budget; the first item should be the single best "
            "recommendation you can genuinely stand behind. Ground every reason in the product's actual "
            "stated attributes, not generic praise - but a shorter, honest reason is fine for lower-ranked items."
        ),
        messages=[{"role": "user", "content": prompt}],
        output_config={"format": {"type": "json_schema", "schema": LISTING_SCHEMA}},
    )
    if response.stop_reason == "refusal":
        return []

    payload = json.loads(response.content[0].text)
    seen_titles: set[str] = set()
    candidates = []
    for item in payload["listings"]:
        key = item["title"].strip().lower()
        if key in seen_titles:  # the same model often turns up in several roundup pages
            continue
        seen_titles.add(key)
        candidates.append(WebProductListing(
            title=item["title"],
            brand=item["brand"],
            retailer=item["retailer"],
            price=convert_to_inr(item["price"], item["currency"]) if item["price"] is not None else None,
            currency="INR",
            image_url=_upscale_image_url(item["image_url"]) if item["image_url"] else None,
            url=item["url"],
            reason=item["reason"],
        ))

    if not candidates:
        return []

    # Resolve each candidate's real, single-product buy link (and fill in its price, if missing) in
    # parallel - these are independent network calls, and doing them one at a time would make a 10-item
    # response take far too long to feel live. Capped workers to stay well within Tavily's rate limits.
    with ThreadPoolExecutor(max_workers=min(len(candidates), 8)) as pool:
        resolved = list(pool.map(_resolve_listing, candidates))
    listings = [listing for listing in resolved if listing is not None][:MAX_LISTINGS]
    return _verify_listing_images(listings)


def search_reviews(title: str, brand: str | None) -> list[ReviewSnippet]:
    """Look up real review excerpts for the single best-fit listing. Returns an empty list - never a
    fabricated quote - when nothing genuinely review-shaped turns up in the search results."""
    query_prefix = f"{brand} " if brand and brand.lower() not in title.lower() else ""
    query = f"{query_prefix}{title} review"[:400]
    results = search_web(query, max_results=5)
    if not results:
        return []

    settings = get_settings()
    context = "\n\n".join(f"[{r.label}] {r.title} ({r.url})\n{r.snippet}" for r in results)
    response = create_message(
        model=settings.recommendation_model,
        max_tokens=768,
        system=(
            "You extract short, genuine review excerpts about a specific product from live web search "
            "results. Only include a quote if the source text actually describes real usage, opinion, or "
            "verdict on the product - skip results that are just spec sheets, price listings, or unrelated "
            "content. Ground every quote strictly in the provided text - never invent, exaggerate, or "
            "paraphrase beyond what's written. Return an empty list if nothing in the results is genuinely "
            "review-shaped."
        ),
        messages=[{"role": "user", "content": f"Product: {title}\n\nSearch results:\n{context}"}],
        output_config={"format": {"type": "json_schema", "schema": REVIEW_SCHEMA}},
    )
    if response.stop_reason == "refusal":
        return []

    payload = json.loads(response.content[0].text)
    return [ReviewSnippet(source=item["source"], quote=item["quote"], url=item["url"]) for item in payload["reviews"]]
