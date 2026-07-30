"""Review submission and the product-level aggregate rating it feeds."""
import logging
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.exceptions import ConflictError, NotFoundError
from app.infrastructure.embeddings import embed_documents
from app.models import Product, Review, User
from app.schemas.reviews import CreateReviewRequest
from app.services.review_nlp import review_document_text

logger = logging.getLogger(__name__)


def recompute_rating(db: Session, product: Product) -> None:
    """Recalculate the product's cached average_rating/review_count from its visible reviews."""
    average, count = db.execute(select(func.avg(Review.rating), func.count(Review.id)).where(Review.product_id == product.id, Review.is_visible.is_(True))).one()
    product.average_rating = round(float(average), 1) if average is not None else None
    product.review_count = count or 0


def create_review(db: Session, user: User, product_id: UUID, payload: CreateReviewRequest) -> Review:
    """Record one shopper's review and keep the product's aggregate rating consistent with it."""
    product = db.get(Product, product_id)
    if not product: raise NotFoundError("Product not found")
    if db.scalar(select(Review).where(Review.user_id == user.id, Review.product_id == product_id)):
        raise ConflictError("You have already reviewed this product")
    review = Review(user_id=user.id, product_id=product_id, rating=payload.rating, title=payload.title, body=payload.body, is_verified_purchase=payload.is_verified_purchase)
    db.add(review)
    db.flush()
    recompute_rating(db, product)
    _embed_review(review)
    db.commit()
    db.refresh(review)
    return review


def _embed_review(review: Review) -> None:
    """Embed at write time so the review is immediately RAG-searchable. Best-effort: an embedding-provider
    outage must never block a review submission - scripts/backfill_embeddings.py catches any misses later."""
    text = review_document_text(review)
    if not text.strip(): return
    try:
        review.embedding = embed_documents([text])[0]
    except Exception:
        logger.warning("review_embedding_failed review_id=%s", review.id, exc_info=True)
