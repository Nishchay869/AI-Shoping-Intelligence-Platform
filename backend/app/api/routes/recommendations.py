from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, rate_limit
from app.db.session import get_db
from app.models import User
from app.schemas.personalization import PersonalizedRecommendationResponse
from app.schemas.recommendations import RecommendationRequest, RecommendationResponse
from app.services.personalization import generate_personalized_recommendations
from app.services.recommendations import generate_recommendations

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=RecommendationResponse, dependencies=[Depends(rate_limit(10, 60))])
def recommend(payload: RecommendationRequest) -> RecommendationResponse:
    """Turn a shopper's budget/purpose/brand/features into up to 10 ranked, real, live product listings."""
    return generate_recommendations(payload)


@router.get("/personalized", response_model=PersonalizedRecommendationResponse, dependencies=[Depends(rate_limit(20, 60))])
def personalized_recommendations(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PersonalizedRecommendationResponse:
    """Behavioral, embeddings-only picks built from this shopper's own search/wishlist/purchase/click history - no LLM in the loop."""
    return generate_personalized_recommendations(db, user.id)
