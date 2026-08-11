"""Review submission and the product-level aggregate rating it feeds."""
import logging
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.exceptions import ConflictError, NotFoundError
from app.infrastructure.embeddings import embed_documents
from app.infrastructure.fake_review_detection import score_texts
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
    _score_review_trust(review)
    db.commit()
    db.refresh(review)
    return review


def list_reviews(db: Session, product_id: UUID, *, limit: int = 20, offset: int = 0) -> list[Review]:
    """Newest-first visible reviews for a product - product_id + is_visible + created_at DESC is exactly the
    shape ix_reviews_product_visible_created (migration 0002) was built to serve."""
    query = (
        select(Review)
        .where(Review.product_id == product_id, Review.is_visible.is_(True))
        .order_by(Review.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(query))


def _embed_review(review: Review) -> None:
    """Embed at write time so the review is immediately RAG-searchable. Best-effort: an embedding-provider
    outage must never block a review submission - scripts/backfill_embeddings.py catches any misses later."""
    text = review_document_text(review)
    if not text.strip(): return
    try:
        review.embedding = embed_documents([text])[0]
    except Exception:
        logger.warning("review_embedding_failed review_id=%s", review.id, exc_info=True)


def _score_review_trust(review: Review) -> None:
    """Score fake-review probability at write time so the trust badge is visible immediately. Best-effort,
    mirroring _embed_review above exactly: this ensemble is a heavy local model rather than a network call,
    but it must still never block a legitimate review submission on a scoring hiccup -
    scripts/backfill_review_trust_scores.py catches any misses, including reviews written before this
    feature existed."""
    text = review_document_text(review)
    if not text.strip(): return
    try:
        review.trust_score = score_texts([text])[0]
    except Exception:
        logger.warning("review_trust_scoring_failed review_id=%s", review.id, exc_info=True)
