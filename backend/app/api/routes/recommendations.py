from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_current_user_optional, rate_limit
from app.db.session import get_db
from app.models import User
from app.schemas.personalization import PersonalizedRecommendationResponse
from app.schemas.recommendations import RecommendationRequest, RecommendationResponse
from app.services.personalization import generate_personalized_recommendations
from app.services.recommendations import generate_recommendations

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=RecommendationResponse, dependencies=[Depends(rate_limit(10, 60))])
def recommend(payload: RecommendationRequest, db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)) -> RecommendationResponse:
    """Turn a shopper's budget/purpose/brand/features into the top AI-explained product picks; persists to the feed when signed in."""
    return generate_recommendations(db, payload, user.id if user else None)


@router.get("/personalized", response_model=PersonalizedRecommendationResponse, dependencies=[Depends(rate_limit(20, 60))])
def personalized_recommendations(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PersonalizedRecommendationResponse:
    """Behavioral, embeddings-only picks built from this shopper's own search/wishlist/purchase/click history - no LLM in the loop."""
    return generate_personalized_recommendations(db, user.id)
