from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, rate_limit
from app.db.session import get_db
from app.models import User
from app.schemas.preferences import ConfirmPhoneVerification, RequestPhoneVerification, UpdateUserPreferencesRequest, UserPreferencesResponse
from app.services import preferences

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("", response_model=UserPreferencesResponse, dependencies=[Depends(rate_limit(60, 60))])
def get_my_preferences(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return the current user's alert, AI persona, and smart-rule preferences, creating defaults on first access."""
    return preferences.get_or_create(db, user)


@router.patch("", response_model=UserPreferencesResponse, dependencies=[Depends(rate_limit(30, 60))])
def update_my_preferences(payload: UpdateUserPreferencesRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Apply a partial update to the current user's preferences."""
    return preferences.update(db, user, payload)


@router.post("/phone/verify", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(rate_limit(5, 60))])
def send_phone_verification(payload: RequestPhoneVerification, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate a one-time code for the given phone number. See services.preferences for the delivery caveat."""
    code = preferences.request_phone_verification(db, user, payload.phone_number)
    return {"sent": True, **({"dev_code": code} if code else {})}


@router.post("/phone/confirm", response_model=UserPreferencesResponse, dependencies=[Depends(rate_limit(10, 60))])
def confirm_phone_verification(payload: ConfirmPhoneVerification, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Mark the pending phone number verified if the submitted code matches."""
    return preferences.confirm_phone_verification(db, user, payload.code)
