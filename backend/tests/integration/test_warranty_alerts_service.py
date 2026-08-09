"""Integration tests: services/warranty_alerts.py against a real Postgres database."""
from datetime import date, timedelta
from uuid import uuid4

from app.core.exceptions import ServiceUnavailableError
from app.models import Receipt
from app.services import preferences, warranty_alerts


def _opt_in_whatsapp(db_session, user, phone: str = "+15551234567"):
    prefs = preferences.get_or_create(db_session, user)
    prefs.notify_whatsapp = True
    prefs.phone_verified = True
    prefs.phone_number = phone
    db_session.commit()
    return prefs


def _make_receipt(db_session, user, *, warranty_expires_at, warranty_alert_sent: bool = False, store_name: str = "Test Store") -> Receipt:
    receipt = Receipt(
        id=uuid4(), user_id=user.id, store_name=store_name, currency="USD",
        raw_ocr_text="synthetic", ocr_confidence=0.9,
        warranty_expires_at=warranty_expires_at, warranty_alert_sent=warranty_alert_sent,
    )
    db_session.add(receipt)
    db_session.commit()
    db_session.refresh(receipt)
    return receipt


def test_sends_alert_for_receipt_expiring_within_window(db_session, make_user, monkeypatch) -> None:
    user = make_user()
    _opt_in_whatsapp(db_session, user)
    receipt = _make_receipt(db_session, user, warranty_expires_at=date.today() + timedelta(days=5))
    monkeypatch.setattr("app.services.whatsapp.send_warranty_expiring_alert", lambda **kwargs: "wamid.TEST")

    notified = warranty_alerts.send_expiring_warranty_alerts(db_session, within_days=7)

    assert [r.id for r in notified] == [receipt.id]
    db_session.refresh(receipt)
    assert receipt.warranty_alert_sent is True


def test_does_not_alert_for_receipt_expiring_outside_window(db_session, make_user, monkeypatch) -> None:
    user = make_user()
    _opt_in_whatsapp(db_session, user)
    _make_receipt(db_session, user, warranty_expires_at=date.today() + timedelta(days=30))
    monkeypatch.setattr("app.services.whatsapp.send_warranty_expiring_alert", lambda **kwargs: "wamid.TEST")

    assert warranty_alerts.send_expiring_warranty_alerts(db_session, within_days=7) == []


def test_does_not_alert_for_already_expired_warranty(db_session, make_user, monkeypatch) -> None:
    user = make_user()
    _opt_in_whatsapp(db_session, user)
    _make_receipt(db_session, user, warranty_expires_at=date.today() - timedelta(days=1))
    monkeypatch.setattr("app.services.whatsapp.send_warranty_expiring_alert", lambda **kwargs: "wamid.TEST")

    assert warranty_alerts.send_expiring_warranty_alerts(db_session, within_days=7) == []


def test_does_not_alert_without_whatsapp_opt_in(db_session, make_user, monkeypatch) -> None:
    user = make_user()  # no preferences configured - notify_whatsapp/phone_verified default False
    _make_receipt(db_session, user, warranty_expires_at=date.today() + timedelta(days=3))
    monkeypatch.setattr("app.services.whatsapp.send_warranty_expiring_alert", lambda **kwargs: "wamid.TEST")

    assert warranty_alerts.send_expiring_warranty_alerts(db_session, within_days=7) == []


def test_does_not_re_alert_already_sent_receipts(db_session, make_user, monkeypatch) -> None:
    user = make_user()
    _opt_in_whatsapp(db_session, user)
    _make_receipt(db_session, user, warranty_expires_at=date.today() + timedelta(days=3), warranty_alert_sent=True)
    monkeypatch.setattr("app.services.whatsapp.send_warranty_expiring_alert", lambda **kwargs: "wamid.TEST")

    assert warranty_alerts.send_expiring_warranty_alerts(db_session, within_days=7) == []


def test_failed_send_is_recorded_but_still_marks_the_receipt_alerted(db_session, make_user, monkeypatch) -> None:
    user = make_user()
    _opt_in_whatsapp(db_session, user)
    receipt = _make_receipt(db_session, user, warranty_expires_at=date.today() + timedelta(days=3))

    def _raise(**kwargs):
        raise ServiceUnavailableError("boom")

    monkeypatch.setattr("app.services.whatsapp.send_warranty_expiring_alert", _raise)

    notified = warranty_alerts.send_expiring_warranty_alerts(db_session, within_days=7)

    assert [r.id for r in notified] == [receipt.id]
    db_session.refresh(receipt)
    assert receipt.warranty_alert_sent is True  # one bad send must not retry-spam every subsequent run
