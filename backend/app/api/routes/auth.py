from fastapi import APIRouter, Depends
from app.api.deps import get_current_user, rate_limit
from app.models import User
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/me", response_model=UserResponse, dependencies=[Depends(rate_limit(60, 60))])
def me(user: User = Depends(get_current_user)) -> UserResponse:
    """Return the identity represented by the current bearer token."""
    return UserResponse.model_validate(user)
