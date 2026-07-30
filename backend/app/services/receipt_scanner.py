"""AI Receipt Scanner: OCR (Tesseract, local) -> LLM structured extraction (Gemini) -> JSON + persistence.

OCR turns pixels into characters; it has no idea that "SUBTOTAL" means subtotal, that "T0TAL" is a misread
"TOTAL", or which lines are purchased items versus a store's address block. That labeling step reuses the
same structured-extraction pattern as the review summarizer (app/services/review_summary.py): raw text in,
one JSON-schema-constrained Gemini call out, so the model cannot return anything outside the shape the
caller expects.
"""
import json
from datetime import date, datetime, timezone
from uuid import UUID, uuid4
from PIL import UnidentifiedImageError
from pytesseract import TesseractNotFoundError
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ServiceUnavailableError
from app.infrastructure.llm import create_message
from app.infrastructure.ocr import extract_text
from app.models import Receipt, ReceiptItem, User
from app.schemas.receipts import ReceiptItemResponse, ReceiptScanResponse

_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "store_name": {"type": ["string", "null"]},
        "purchase_date": {"type": ["string", "null"], "description": "ISO 8601 date (YYYY-MM-DD), or null if no legible date"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string"},
                    "price": {"type": "number", "description": "Line total for this item, plain decimal, no currency symbol"},
                    "quantity": {"type": "integer"},
                },
                "required": ["product_name", "price", "quantity"],
                "additionalProperties": False,
            },
        },
        "subtotal": {"type": ["number", "null"]},
        "tax": {"type": ["number", "null"]},
        "total": {"type": ["number", "null"]},
        "currency": {"type": "string", "description": "Best-guess ISO 4217 currency code from symbols/context, e.g. USD, INR, EUR"},
        "warranty_text": {"type": ["string", "null"], "description": "Any warranty or return-policy text printed on the receipt, or null if none is present"},
    },
    "required": ["store_name", "purchase_date", "items", "subtotal", "tax", "total", "currency", "warranty_text"],
    "additionalProperties": False,
}


def _to_minor(amount: float | None) -> int | None:
    return round(amount * 100) if amount is not None else None


def _extract_fields(raw_text: str) -> dict:
    """Ask Gemini to turn noisy OCR text into the receipt's structured fields, grounded strictly in what's there."""
    settings = get_settings()
    response = create_message(
        model=settings.recommendation_model,
        max_tokens=2048,
        system=(
            "You extract structured data from the raw OCR text of a shopper's purchase receipt. The text may "
            "contain OCR noise (misread characters, broken lines, stray symbols) - use context to correct obvious "
            "mistakes (e.g. 'T0TAL' means TOTAL, 'O' read for '0' in a price) but never invent a line item, price, "
            "date, or warranty detail that isn't actually present in the text. Prices are plain decimal numbers "
            "without currency symbols. If a field truly is not present or legible, use null for it."
        ),
        messages=[{"role": "user", "content": f"Raw OCR text of a purchase receipt:\n\n{raw_text}"}],
        output_config={"format": {"type": "json_schema", "schema": _EXTRACTION_SCHEMA}},
    )
    if response.stop_reason == "refusal":
        raise ServiceUnavailableError("The assistant declined to process this receipt")
    return json.loads(response.content[0].text)


def scan_receipt(db: Session, image_bytes: bytes, user: User | None) -> ReceiptScanResponse:
    """Full pipeline entry point: OCR the image, extract structured fields via LLM, persist when signed in."""
    try:
        raw_text, ocr_confidence = extract_text(image_bytes)
    except UnidentifiedImageError as exc:
        raise ValueError("The uploaded file is not a readable image") from exc
    except TesseractNotFoundError as exc:
        raise ServiceUnavailableError("OCR engine is not installed on this server") from exc
    if not raw_text.strip():
        raise ValueError("No legible text was found in this image")

    fields = _extract_fields(raw_text)
    try:
        purchase_date = date.fromisoformat(fields["purchase_date"]) if fields["purchase_date"] else None
    except ValueError:
        purchase_date = None
    currency = "".join(ch for ch in (fields.get("currency") or "USD") if ch.isalpha())[:3].upper() or "USD"

    now = datetime.now(timezone.utc)
    receipt = Receipt(
        id=uuid4(),
        user_id=user.id if user else None,
        store_name=fields["store_name"],
        purchase_date=purchase_date,
        subtotal_minor=_to_minor(fields["subtotal"]),
        tax_minor=_to_minor(fields["tax"]),
        total_minor=_to_minor(fields["total"]),
        currency=currency,
        warranty_text=fields["warranty_text"],
        raw_ocr_text=raw_text,
        ocr_confidence=round(ocr_confidence, 3),
        created_at=now,
        updated_at=now,
        items=[
            ReceiptItem(id=uuid4(), product_name=item["product_name"], price_minor=_to_minor(item["price"]) or 0, quantity=item.get("quantity") or 1)
            for item in fields["items"]
        ],
    )
    if user:
        db.add(receipt)
        db.commit()
        db.refresh(receipt)

    return ReceiptScanResponse(
        id=receipt.id,
        store_name=receipt.store_name,
        purchase_date=receipt.purchase_date,
        subtotal_minor=receipt.subtotal_minor,
        tax_minor=receipt.tax_minor,
        total_minor=receipt.total_minor,
        currency=receipt.currency,
        warranty_text=receipt.warranty_text,
        ocr_confidence=receipt.ocr_confidence,
        items=[ReceiptItemResponse.model_validate(item) for item in receipt.items],
        created_at=receipt.created_at,
        saved=user is not None,
    )


def list_my_receipts(db: Session, user: User) -> list[Receipt]:
    """Return the current user's scanned receipt history, most recent first."""
    return list(db.scalars(select(Receipt).where(Receipt.user_id == user.id).order_by(Receipt.created_at.desc())))


def get_my_receipt(db: Session, user: User, receipt_id: UUID) -> Receipt:
    """Fetch one previously scanned receipt, only if it belongs to the current user."""
    receipt = db.scalar(select(Receipt).where(Receipt.id == receipt_id, Receipt.user_id == user.id))
    if not receipt:
        raise NotFoundError("Receipt not found")
    return receipt
