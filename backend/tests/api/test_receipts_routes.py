"""API tests: /api/v1/receipts - OCR runs for real (Tesseract is installed locally, no API key needed);
only the LLM structured-extraction step is mocked, since that needs a real GEMINI_API_KEY this
environment doesn't have.
"""
import io
import json
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image, ImageDraw


def _synthetic_receipt_png() -> bytes:
    image = Image.new("RGB", (300, 150), "white")
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), "TEST STORE", fill="black")
    draw.text((10, 40), "Widget    9.99", fill="black")
    draw.text((10, 70), "Total     9.99", fill="black")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _mock_llm_extraction(**overrides):
    payload = {
        "store_name": "Test Store", "purchase_date": None,
        "items": [{"product_name": "Widget", "price": 9.99, "quantity": 1}],
        "subtotal": None, "tax": None, "total": 9.99, "currency": "USD", "warranty_text": None, "warranty_duration_days": None,
        **overrides,
    }
    return MagicMock(stop_reason="end_turn", content=[MagicMock(text=json.dumps(payload))])


def test_scan_empty_file_returns_400(client) -> None:
    response = client.post("/api/v1/receipts/scan", files={"image": ("empty.png", b"", "image/png")})
    assert response.status_code == 400


def test_scan_non_image_file_returns_422(client) -> None:
    response = client.post("/api/v1/receipts/scan", files={"image": ("note.txt", b"not an image", "text/plain")})
    assert response.status_code == 422


def test_scan_anonymous_is_not_saved(client) -> None:
    with patch("app.services.receipt_scanner.create_message", return_value=_mock_llm_extraction()):
        response = client.post("/api/v1/receipts/scan", files={"image": ("receipt.png", _synthetic_receipt_png(), "image/png")})
    assert response.status_code == 200
    body = response.json()
    assert body["saved"] is False
    assert body["total_minor"] == 999


def test_scan_signed_in_is_saved_and_listed(as_user, make_user) -> None:
    user = make_user()
    api = as_user(user)
    with patch("app.services.receipt_scanner.create_message", return_value=_mock_llm_extraction()):
        scan_response = api.post("/api/v1/receipts/scan", files={"image": ("receipt.png", _synthetic_receipt_png(), "image/png")})
    assert scan_response.status_code == 200
    assert scan_response.json()["saved"] is True

    listed = api.get("/api/v1/receipts")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["store_name"] == "Test Store"


def test_rescanning_the_same_photo_does_not_duplicate_history(as_user, make_user) -> None:
    """Re-uploading the exact same receipt photo (e.g. an accidental double-submit) must not create a second
    history row - it should hand back the already-saved receipt instead."""
    api = as_user(make_user())
    photo = _synthetic_receipt_png()
    with patch("app.services.receipt_scanner.create_message", return_value=_mock_llm_extraction()) as mock_llm:
        first = api.post("/api/v1/receipts/scan", files={"image": ("receipt.png", photo, "image/png")})
        second = api.post("/api/v1/receipts/scan", files={"image": ("receipt.png", photo, "image/png")})
    assert first.status_code == 200 and second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["saved"] is True
    mock_llm.assert_called_once()  # the second upload short-circuits before the OCR/LLM pipeline runs again

    listed = api.get("/api/v1/receipts")
    assert len(listed.json()) == 1


def test_same_photo_scanned_by_two_users_is_not_deduplicated(as_user, make_user) -> None:
    """The dedup key is scoped per user - one shopper's scan must never be handed back as another's."""
    first_user, second_user = make_user(email="first@example.com"), make_user(email="second@example.com")
    photo = _synthetic_receipt_png()
    with patch("app.services.receipt_scanner.create_message", return_value=_mock_llm_extraction()):
        first = as_user(first_user).post("/api/v1/receipts/scan", files={"image": ("receipt.png", photo, "image/png")})
        second = as_user(second_user).post("/api/v1/receipts/scan", files={"image": ("receipt.png", photo, "image/png")})
    assert first.json()["id"] != second.json()["id"]
    assert len(as_user(first_user).get("/api/v1/receipts").json()) == 1
    assert len(as_user(second_user).get("/api/v1/receipts").json()) == 1


def test_rescanning_a_different_photo_of_the_same_receipt_is_not_deduplicated(as_user, make_user) -> None:
    """Dedup is keyed on exact image bytes, not extracted fields - a different photo of what happens to be the
    same purchase (different crop, lighting, re-take) is intentionally treated as a separate scan."""
    api = as_user(make_user())
    with patch("app.services.receipt_scanner.create_message", return_value=_mock_llm_extraction()):
        first = api.post("/api/v1/receipts/scan", files={"image": ("receipt-a.png", _synthetic_receipt_png(), "image/png")})
        second = api.post("/api/v1/receipts/scan", files={"image": ("receipt-b.png", _synthetic_receipt_png() + b"\x00", "image/png")})
    assert first.json()["id"] != second.json()["id"]
    assert len(api.get("/api/v1/receipts").json()) == 2


def test_anonymous_rescans_are_never_deduplicated(client) -> None:
    """Anonymous scans aren't persisted at all, so there's nothing to dedup against - each call must run the
    full pipeline independently."""
    photo = _synthetic_receipt_png()
    with patch("app.services.receipt_scanner.create_message", return_value=_mock_llm_extraction()) as mock_llm:
        first = client.post("/api/v1/receipts/scan", files={"image": ("receipt.png", photo, "image/png")})
        second = client.post("/api/v1/receipts/scan", files={"image": ("receipt.png", photo, "image/png")})
    assert first.status_code == 200 and second.status_code == 200
    assert first.json()["saved"] is False and second.json()["saved"] is False
    assert mock_llm.call_count == 2


def test_list_receipts_requires_authentication(client) -> None:
    assert client.get("/api/v1/receipts").status_code == 401


def test_cannot_view_another_users_receipt(as_user, make_user) -> None:
    owner = make_user(email="owner@example.com")
    attacker = make_user(email="attacker@example.com")
    with patch("app.services.receipt_scanner.create_message", return_value=_mock_llm_extraction()):
        scan_response = as_user(owner).post("/api/v1/receipts/scan", files={"image": ("receipt.png", _synthetic_receipt_png(), "image/png")})
    receipt_id = scan_response.json()["id"]

    response = as_user(attacker).get(f"/api/v1/receipts/{receipt_id}")
    assert response.status_code == 404


def test_scan_when_gemini_api_call_fails_is_service_unavailable_not_a_crash(client) -> None:
    """A real Gemini API-level failure (billing, rate limit, connectivity, a Gemini-side outage) - distinct
    from a missing API key - must surface as a clean 503, never an unhandled 500. Goes through the real
    create_message() wrapper (only the underlying client's own API call is faked), so this exercises the
    actual try/except doing the translation, not just a mocked-away shortcut."""
    fake_client = MagicMock()
    fake_client.models.generate_content.side_effect = RuntimeError("Gemini API is temporarily down")
    with patch("app.infrastructure.llm._client", return_value=fake_client):
        response = client.post("/api/v1/receipts/scan", files={"image": ("receipt.png", _synthetic_receipt_png(), "image/png")})
    assert response.status_code == 503


@pytest.mark.parametrize("bad_currency", ["usd", "US", "USDD"])
def test_llm_returning_a_malformed_currency_is_sanitized_not_trusted(client, bad_currency) -> None:
    """The scanner strips non-letters and upper-cases whatever the LLM returns rather than trusting it
    verbatim - a defensive measure since this value flows into a 3-char DB column."""
    with patch("app.services.receipt_scanner.create_message", return_value=_mock_llm_extraction(currency=bad_currency)):
        response = client.post("/api/v1/receipts/scan", files={"image": ("receipt.png", _synthetic_receipt_png(), "image/png")})
    assert response.status_code == 200
    assert len(response.json()["currency"]) <= 3


def test_warranty_expiry_is_computed_from_purchase_date_and_duration(as_user, make_user) -> None:
    api = as_user(make_user())
    overrides = {"purchase_date": "2025-01-01", "warranty_duration_days": 365, "warranty_text": "1 year warranty"}
    with patch("app.services.receipt_scanner.create_message", return_value=_mock_llm_extraction(**overrides)):
        response = api.post("/api/v1/receipts/scan", files={"image": ("receipt.png", _synthetic_receipt_png(), "image/png")})
    assert response.status_code == 200
    assert response.json()["warranty_expires_at"] == "2026-01-01"


def test_warranty_expiry_is_null_without_a_purchase_date(as_user, make_user) -> None:
    """Date arithmetic needs a starting point - no legible purchase date means no computed expiry, even
    when a warranty duration is stated."""
    api = as_user(make_user())
    overrides = {"purchase_date": None, "warranty_duration_days": 365}
    with patch("app.services.receipt_scanner.create_message", return_value=_mock_llm_extraction(**overrides)):
        response = api.post("/api/v1/receipts/scan", files={"image": ("receipt.png", _synthetic_receipt_png(), "image/png")})
    assert response.status_code == 200
    assert response.json()["warranty_expires_at"] is None


def test_warranty_expiry_is_null_without_a_stated_duration(as_user, make_user) -> None:
    api = as_user(make_user())
    overrides = {"purchase_date": "2025-01-01", "warranty_duration_days": None}
    with patch("app.services.receipt_scanner.create_message", return_value=_mock_llm_extraction(**overrides)):
        response = api.post("/api/v1/receipts/scan", files={"image": ("receipt.png", _synthetic_receipt_png(), "image/png")})
    assert response.status_code == 200
    assert response.json()["warranty_expires_at"] is None


def test_delete_requires_authentication(client) -> None:
    assert client.delete("/api/v1/receipts/00000000-0000-0000-0000-000000000000").status_code == 401


def test_owner_can_delete_their_receipt(as_user, make_user) -> None:
    api = as_user(make_user())
    with patch("app.services.receipt_scanner.create_message", return_value=_mock_llm_extraction()):
        scan_response = api.post("/api/v1/receipts/scan", files={"image": ("receipt.png", _synthetic_receipt_png(), "image/png")})
    receipt_id = scan_response.json()["id"]

    delete_response = api.delete(f"/api/v1/receipts/{receipt_id}")
    assert delete_response.status_code == 204
    assert api.get("/api/v1/receipts").json() == []


def test_cannot_delete_another_users_receipt(as_user, make_user) -> None:
    owner = make_user(email="owner-del@example.com")
    attacker = make_user(email="attacker-del@example.com")
    with patch("app.services.receipt_scanner.create_message", return_value=_mock_llm_extraction()):
        scan_response = as_user(owner).post("/api/v1/receipts/scan", files={"image": ("receipt.png", _synthetic_receipt_png(), "image/png")})
    receipt_id = scan_response.json()["id"]

    response = as_user(attacker).delete(f"/api/v1/receipts/{receipt_id}")
    assert response.status_code == 404
    assert len(as_user(owner).get("/api/v1/receipts").json()) == 1
