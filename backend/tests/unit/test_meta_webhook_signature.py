"""Unit tests: core/webhooks.py's Meta HMAC signature verification - no DB, no network."""
import hashlib
import hmac

from app.core.webhooks import verify_meta_signature


def _sign(payload: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def test_valid_signature_is_accepted() -> None:
    payload = b'{"entry": []}'
    secret = "test-secret"
    assert verify_meta_signature(payload, _sign(payload, secret), secret) is True


def test_tampered_payload_is_rejected() -> None:
    secret = "test-secret"
    signature = _sign(b'{"entry": []}', secret)
    assert verify_meta_signature(b'{"entry": ["tampered"]}', signature, secret) is False


def test_wrong_secret_is_rejected() -> None:
    payload = b'{"entry": []}'
    signature = _sign(payload, "wrong-secret")
    assert verify_meta_signature(payload, signature, "test-secret") is False


def test_missing_signature_header_is_rejected() -> None:
    assert verify_meta_signature(b"{}", None, "test-secret") is False


def test_malformed_signature_header_is_rejected() -> None:
    assert verify_meta_signature(b"{}", "not-a-valid-header", "test-secret") is False


def test_missing_app_secret_is_rejected() -> None:
    assert verify_meta_signature(b"{}", "sha256=abc", "") is False
