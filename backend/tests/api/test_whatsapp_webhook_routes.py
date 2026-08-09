"""API tests: /api/v1/webhooks/whatsapp - Meta's verification handshake, delivery-status callbacks, and
STOP opt-out, over real HTTP + DB. No get_current_user auth here (Meta calls these, not a signed-in user) -
trust is the verify-token handshake (GET) and HMAC signature (POST) instead."""
import hashlib
import hmac
import json

from app.core.config import get_settings
from app.models import WhatsappMessageStatus
from app.schemas.wishlist import AddWishlistItemRequest, CreateWishlistRequest
from app.services import preferences, price_alerts, wishlist


def _sign(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_get_verification_echoes_challenge_on_matching_token(client, monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "whatsapp_verify_token", "test-verify-token")
    response = client.get("/api/v1/webhooks/whatsapp", params={"hub.mode": "subscribe", "hub.verify_token": "test-verify-token", "hub.challenge": "12345"})
    assert response.status_code == 200
    assert response.text == "12345"


def test_get_verification_rejects_wrong_token(client, monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "whatsapp_verify_token", "test-verify-token")
    response = client.get("/api/v1/webhooks/whatsapp", params={"hub.mode": "subscribe", "hub.verify_token": "wrong-token", "hub.challenge": "12345"})
    assert response.status_code == 403


def test_post_without_valid_signature_is_rejected(client, monkeypatch) -> None:
    monkeypatch.setattr(get_settings(), "whatsapp_app_secret", "test-secret")
    response = client.post("/api/v1/webhooks/whatsapp", content=b'{"entry": []}', headers={"x-hub-signature-256": "sha256=wrong"})
    assert response.status_code == 400


def test_post_status_update_marks_message_delivered(client, monkeypatch, db_session, make_user, make_product, make_offer) -> None:
    user = make_user()
    prefs = preferences.get_or_create(db_session, user)
    prefs.notify_whatsapp = True
    prefs.phone_verified = True
    prefs.phone_number = "+15551234567"
    db_session.commit()
    product = make_product()
    offer = make_offer(product=product, price_minor=10000)
    my_list = wishlist.create_wishlist(db_session, user, CreateWishlistRequest())
    wishlist.add_item(db_session, user, my_list.id, AddWishlistItemRequest(product_id=product.id, target_price_minor=9000))
    monkeypatch.setattr("app.services.whatsapp.send_price_drop_alert", lambda **kwargs: "wamid.ROUTE_TEST")
    sent = price_alerts.evaluate_and_notify(db_session, offer, 8000)
    assert sent[0].wa_message_id == "wamid.ROUTE_TEST"

    secret = "test-secret"
    monkeypatch.setattr(get_settings(), "whatsapp_app_secret", secret)
    body = json.dumps({"entry": [{"changes": [{"value": {"statuses": [{"id": "wamid.ROUTE_TEST", "status": "delivered"}]}}]}]}).encode()
    response = client.post("/api/v1/webhooks/whatsapp", content=body, headers={"x-hub-signature-256": _sign(body, secret), "content-type": "application/json"})

    assert response.status_code == 200
    db_session.refresh(sent[0])
    assert sent[0].status == WhatsappMessageStatus.DELIVERED


def test_post_unrecognized_status_update_is_ignored_not_errored(client, monkeypatch) -> None:
    secret = "test-secret"
    monkeypatch.setattr(get_settings(), "whatsapp_app_secret", secret)
    body = json.dumps({"entry": [{"changes": [{"value": {"statuses": [{"id": "wamid.UNKNOWN", "status": "deleted"}]}}]}]}).encode()

    response = client.post("/api/v1/webhooks/whatsapp", content=body, headers={"x-hub-signature-256": _sign(body, secret), "content-type": "application/json"})

    assert response.status_code == 200


def test_post_stop_message_opts_user_out(client, monkeypatch, db_session, make_user) -> None:
    user = make_user()
    prefs = preferences.get_or_create(db_session, user)
    prefs.notify_whatsapp = True
    prefs.phone_verified = True
    prefs.phone_number = "+15551234567"
    db_session.commit()

    secret = "test-secret"
    monkeypatch.setattr(get_settings(), "whatsapp_app_secret", secret)
    body = json.dumps({"entry": [{"changes": [{"value": {"messages": [{"from": "15551234567", "text": {"body": "stop"}}]}}]}]}).encode()
    response = client.post("/api/v1/webhooks/whatsapp", content=body, headers={"x-hub-signature-256": _sign(body, secret), "content-type": "application/json"})

    assert response.status_code == 200
    db_session.refresh(prefs)
    assert prefs.notify_whatsapp is False


def test_post_non_stop_message_does_not_opt_user_out(client, monkeypatch, db_session, make_user) -> None:
    user = make_user()
    prefs = preferences.get_or_create(db_session, user)
    prefs.notify_whatsapp = True
    prefs.phone_verified = True
    prefs.phone_number = "+15551234567"
    db_session.commit()

    secret = "test-secret"
    monkeypatch.setattr(get_settings(), "whatsapp_app_secret", secret)
    body = json.dumps({"entry": [{"changes": [{"value": {"messages": [{"from": "15551234567", "text": {"body": "thanks!"}}]}}]}]}).encode()
    response = client.post("/api/v1/webhooks/whatsapp", content=body, headers={"x-hub-signature-256": _sign(body, secret), "content-type": "application/json"})

    assert response.status_code == 200
    db_session.refresh(prefs)
    assert prefs.notify_whatsapp is True
