"""Signature verification for inbound webhooks from third parties (currently: Meta's WhatsApp Cloud API).
Kept separate from core/security.py, which verifies Supabase-issued user JWTs - a distinct trust boundary."""
import hashlib
import hmac


def verify_meta_signature(payload: bytes, signature_header: str | None, app_secret: str) -> bool:
    """Check the `X-Hub-Signature-256: sha256=<hex>` header Meta sends against an HMAC-SHA256 of the raw
    request body, computed with the app secret. Must be called with the exact raw bytes Meta signed -
    parsing to JSON and re-serializing before verifying would not reproduce the same signature."""
    if not signature_header or not signature_header.startswith("sha256=") or not app_secret:
        return False
    expected = hmac.new(app_secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header.removeprefix("sha256="))
