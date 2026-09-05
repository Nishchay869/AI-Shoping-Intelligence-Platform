from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, rate_limit
from app.db.session import get_db
from app.models import User
from app.schemas.notifications import NotificationResponse
from app.services.notifications import list_notifications

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse], dependencies=[Depends(rate_limit(60, 60))])
def list_my_notifications(limit: int = Query(default=20, ge=1, le=50), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[NotificationResponse]:
    """List this user's most recent price-drop alerts, newest first."""
    return list_notifications(db, user, limit=limit)
