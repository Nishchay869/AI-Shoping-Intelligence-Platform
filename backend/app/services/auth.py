"""Authentication use-cases with no dependency on FastAPI routing details."""
from typing import Any
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models import User


def provision_or_get_user(db: Session, claims: dict[str, Any]) -> User | None:
    """Resolve the local User row for a verified Supabase token, JIT-provisioning it on first sight.

    Supabase's own Postgres/auth schema is a separate database this app has no access to, so the verified
    token's claims are the only bridge between the two identity systems. A Supabase user's `sub` becomes
    this row's primary key, so every existing FK (wishlists.user_id, reviews.user_id, ...) keeps working
    unmodified.
    """
    try:
        user_id = UUID(str(claims["sub"]))
    except (KeyError, ValueError, TypeError):
        return None

    user = db.get(User, user_id)
    if user:
        return user if user.is_active else None

    email = claims.get("email")
    if not email:
        return None  # phone-only/anonymous Supabase sessions aren't supported by this app

    metadata = claims.get("user_metadata") or {}
    display_name = str(metadata.get("display_name") or email.split("@")[0])[:80]

    user = User(id=user_id, email=email.lower(), display_name=display_name, is_active=True)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Lost a provisioning race against a concurrent request for this same new user. Re-fetch by id; a
        # genuine conflict (e.g. duplicate email) re-raises rather than being masked as a silent 401.
        db.rollback()
        user = db.get(User, user_id)
        if user is None:
            raise
    db.refresh(user)
    return user if user.is_active else None
