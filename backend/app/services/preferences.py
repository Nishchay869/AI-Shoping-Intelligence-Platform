"""Alert trigger rules, AI shopping persona, and smart-rule preferences - all real, persisted settings.

No background job evaluates min_discount_percentage / alert_all_time_low / alert_below_90d_average /
restock_alerts_enabled against live prices yet (that's a price-monitoring worker, out of scope here) -
this module only owns reading and writing the settings themselves, same as wishlist_items.target_price_minor
already exists without anything consuming it.
"""
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.exceptions import DomainError
from app.models import User, UserPreferences
from app.schemas.preferences import UpdateUserPreferencesRequest

logger = logging.getLogger(__name__)
_OTP_TTL = timedelta(minutes=10)


def get_or_create(db: Session, user: User) -> UserPreferences:
    """Return the user's preference row, creating it with defaults on first access."""
    prefs = db.get(UserPreferences, user.id)
    if prefs:
        return prefs
    prefs = UserPreferences(user_id=user.id)
    db.add(prefs)
    db.commit()
    db.refresh(prefs)
    return prefs


def update(db: Session, user: User, payload: UpdateUserPreferencesRequest) -> UserPreferences:
    """Apply only the fields the client actually sent, leaving the rest untouched."""
    prefs = get_or_create(db, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(prefs, field, value)
    db.commit()
    db.refresh(prefs)
    return prefs


def request_phone_verification(db: Session, user: User, phone_number: str) -> str | None:
    """Generate and store a hashed one-time code for the given phone number.

    No SMS provider (e.g. Twilio) is configured anywhere in this app yet, so there is no real delivery
    mechanism - the raw code is returned directly outside production so the flow is testable end-to-end,
    and logged either way. Swap this for a real provider call when one is configured; the hash/expiry
    storage and confirm_phone_verification below don't need to change.
    """
    prefs = get_or_create(db, user)
    code = f"{secrets.randbelow(1_000_000):06d}"
    prefs.phone_number = phone_number
    prefs.phone_verified = False
    prefs.phone_otp_hash = hashlib.sha256(code.encode()).hexdigest()
    prefs.phone_otp_expires_at = datetime.now(timezone.utc) + _OTP_TTL
    db.commit()
    logger.info("phone_otp_generated user_id=%s", user.id)
    return None if get_settings().app_env == "production" else code


def confirm_phone_verification(db: Session, user: User, code: str) -> UserPreferences:
    """Mark the pending phone number verified if the code matches and hasn't expired."""
    prefs = get_or_create(db, user)
    if not prefs.phone_otp_hash or not prefs.phone_otp_expires_at or prefs.phone_otp_expires_at < datetime.now(timezone.utc):
        raise DomainError("Verification code expired - request a new one")
    if hashlib.sha256(code.encode()).hexdigest() != prefs.phone_otp_hash:
        raise DomainError("Incorrect verification code")
    prefs.phone_verified = True
    prefs.phone_otp_hash = None
    prefs.phone_otp_expires_at = None
    db.commit()
    db.refresh(prefs)
    return prefs
