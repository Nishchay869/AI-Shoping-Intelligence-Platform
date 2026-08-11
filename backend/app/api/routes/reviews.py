from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, rate_limit
from app.db.session import get_db
from app.models import Review, User
from app.schemas.reviews import CreateReviewRequest, ReviewResponse, ReviewSummaryResponse
from app.services import reviews as reviews_service
from app.services.review_summary import summarize_product_reviews

router = APIRouter(prefix="/products/{product_id}/reviews", tags=["reviews"])


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit(20, 60))])
def create_review(product_id: UUID, payload: CreateReviewRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ReviewResponse:
    """Submit one review for a product and keep its cached aggregate rating consistent with it."""
    return reviews_service.create_review(db, user, product_id, payload)


@router.get("", response_model=list[ReviewResponse], dependencies=[Depends(rate_limit(120, 60))])
def list_reviews(product_id: UUID, limit: int = Query(default=20, ge=1, le=100), offset: int = Query(default=0, ge=0), db: Session = Depends(get_db)) -> list[Review]:
    """List a product's visible reviews, newest first - matches ix_reviews_product_visible_created."""
    return reviews_service.list_reviews(db, product_id, limit=limit, offset=offset)


@router.get("/summary", response_model=ReviewSummaryResponse, dependencies=[Depends(rate_limit(5, 60))])
def get_review_summary(product_id: UUID, db: Session = Depends(get_db)) -> ReviewSummaryResponse:
    """Return the AI-generated pros/cons/complaints/sentiment/recommendation summary for a product's reviews."""
    return summarize_product_reviews(db, product_id)
