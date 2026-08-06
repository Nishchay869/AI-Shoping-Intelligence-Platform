"""Integration tests: services/preferences.py against a real Postgres database."""
from datetime import datetime, timedelta, timezone
import pytest

from app.core.exceptions import DomainError
from app.models import UserPreferences
from app.schemas.preferences import UpdateUserPreferencesRequest
from app.services import preferences


def test_get_or_create_persists_defaults(db_session, make_user) -> None:
    user = make_user()
    prefs = preferences.get_or_create(db_session, user)

    assert prefs.user_id == user.id
    assert prefs.notify_email is True
    assert prefs.notify_sms is False
    assert prefs.notification_frequency == "instant"
    assert prefs.favorite_brands == []
    assert prefs.budget_tier is None

    assert db_session.get(UserPreferences, user.id) is not None


def test_get_or_create_is_idempotent(db_session, make_user) -> None:
    user = make_user()
    first = preferences.get_or_create(db_session, user)
    second = preferences.get_or_create(db_session, user)
    assert first.user_id == second.user_id


def test_update_only_touches_provided_fields(db_session, make_user) -> None:
    user = make_user()
    preferences.update(db_session, user, UpdateUserPreferencesRequest(favorite_brands=["Nike", "Apple"], budget_tier="premium"))

    updated = preferences.update(db_session, user, UpdateUserPreferencesRequest(notify_sms=True))

    assert updated.notify_sms is True
    assert updated.favorite_brands == ["Nike", "Apple"]  # untouched by the second, unrelated update
    assert updated.budget_tier == "premium"


def test_phone_verification_happy_path(db_session, make_user) -> None:
    user = make_user()
    code = preferences.request_phone_verification(db_session, user, "+15551234567")
    assert code is not None  # app_env defaults to "development" in tests, so the dev code is returned

    confirmed = preferences.confirm_phone_verification(db_session, user, code)
    assert confirmed.phone_verified is True
    assert confirmed.phone_number == "+15551234567"
    assert confirmed.phone_otp_hash is None


def test_phone_verification_wrong_code_raises(db_session, make_user) -> None:
    user = make_user()
    preferences.request_phone_verification(db_session, user, "+15551234567")
    with pytest.raises(DomainError):
        preferences.confirm_phone_verification(db_session, user, "000000")


def test_phone_verification_expired_code_raises(db_session, make_user) -> None:
    user = make_user()
    code = preferences.request_phone_verification(db_session, user, "+15551234567")
    prefs = preferences.get_or_create(db_session, user)
    prefs.phone_otp_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    with pytest.raises(DomainError):
        preferences.confirm_phone_verification(db_session, user, code)
