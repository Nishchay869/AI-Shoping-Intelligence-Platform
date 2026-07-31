"""AI recommendation engine: real, live, purchasable product listings ranked by fit to a shopper's stated
budget/purpose/brand/features - there is no internal catalog fallback, since a small demo catalog can never
represent real inventory or scale to a genuine top-10 ranked list. The single best-fit listing also gets real
review excerpts attached, pulled live from the web rather than written by the LLM."""
from app.core.exceptions import NotFoundError
from app.schemas.recommendations import RecommendationItem, RecommendationRequest, RecommendationResponse, ReviewSnippet
from app.services.web_product_search import search_reviews, search_web_products


def generate_recommendations(request: RecommendationRequest) -> RecommendationResponse:
    """Run the full pipeline and return up to 10 real, ranked web listings, with the top pick's real reviews attached."""
    listings = search_web_products(request.purpose, request.features, request.budget, request.currency, request.brand_preference, request.category)
    if not listings:
        raise NotFoundError("No matching products found on the web for this request")

    items = []
    for index, listing in enumerate(listings):
        is_best_pick = index == 0
        reviews = search_reviews(listing.title, listing.brand) if is_best_pick else []
        items.append(RecommendationItem(
            rank=index + 1,
            title=listing.title,
            brand=listing.brand,
            retailer=listing.retailer,
            price=listing.price,
            currency=listing.currency,
            image_url=listing.image_url,
            url=listing.url,
            reason=listing.reason,
            is_best_pick=is_best_pick,
            reviews=[ReviewSnippet(source=r.source, quote=r.quote, url=r.url) for r in reviews],
        ))

    return RecommendationResponse(interpreted_intent=request.purpose, items=items)
