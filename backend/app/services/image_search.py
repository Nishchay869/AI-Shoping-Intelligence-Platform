"""Image-based product search: embed the uploaded photo with CLIP, then run pgvector cosine search over
Product.image_embedding - the same retrieve-by-vector pattern used elsewhere in this app (recommendations,
RAG), just with an image query instead of a text one. Catalog matches alone don't go far with a small
catalog, so this also identifies the product via a vision call and runs it through the same live
cross-retailer web search every other "find this on Flipkart/Amazon/..." feature already uses.
"""
import logging
from PIL import UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.exceptions import ServiceUnavailableError
from app.infrastructure.clip_embeddings import embed_image
from app.infrastructure.llm import identify_product_photo
from app.models import Product
from app.services.price_comparison import PriceListing, compare_prices

logger = logging.getLogger(__name__)

# CLIP cosine similarity runs far "hotter" than intuition suggests - confirmed live, a completely unrelated
# photo (a forest) still scored 0.47 against an iPhone product photo, and a different product entirely (a
# MacBook photo against that same iPhone) scored 0.70. 0.15 was accepting nearly anything as a "match." Set
# above the observed different-product score so a wrong catalog item never gets shown as if it were genuinely
# similar - this catalog is also tiny right now, so most searches correctly finding no match is expected and
# fine; the live web listings (compare_prices) are this feature's real value, not the catalog cross-check.
MIN_SIMILARITY = 0.9


def search_by_image(db: Session, image_bytes: bytes, mime_type: str, top_k: int = 10) -> tuple[list[tuple[Product, float]], str | None, list[PriceListing]]:
    """Returns (catalog matches most-similar-first, what the photo was identified as, live web listings for
    it) - the identification and web search are best-effort (None/empty on failure) so a hiccup there never
    hides the catalog matches this endpoint could already provide on its own."""
    try:
        query_embedding = embed_image(image_bytes)
    except UnidentifiedImageError as exc:
        raise ValueError("The uploaded file is not a readable image") from exc
    except Exception as exc:
        raise ServiceUnavailableError("Could not process the uploaded image") from exc

    query = (
        select(Product, (1 - Product.image_embedding.cosine_distance(query_embedding)).label("similarity"))
        .where(Product.image_embedding.is_not(None))
        .order_by(Product.image_embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )
    rows = db.execute(query).all()
    catalog_matches = [(product, float(similarity)) for product, similarity in rows if similarity >= MIN_SIMILARITY]

    identified_as = identify_product_photo(image_bytes, mime_type)
    web_listings: list[PriceListing] = []
    if identified_as:
        try:
            web_listings = compare_prices(identified_as)
        except ServiceUnavailableError:
            # Unlike its own direct /compare-prices endpoint (where raising is correct - a shopper who
            # explicitly asked to compare prices should see "temporarily unavailable", not a silent "found
            # nothing"), a photo search that already has real catalog matches and a real identification must
            # not fail outright just because this one extra piece hit a rate limit or transient error.
            logger.warning("image_search_web_listings_failed identified_as=%s", identified_as)
    return catalog_matches, identified_as, web_listings
