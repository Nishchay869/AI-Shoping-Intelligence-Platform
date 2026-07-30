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
        "subtotal": None, "tax": None, "total": 9.99, "currency": "USD", "warranty_text": None,
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
