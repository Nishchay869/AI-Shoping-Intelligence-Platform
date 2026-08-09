"""AI Receipt Scanner: OCR (Tesseract, local) -> LLM structured extraction (Gemini) -> JSON + persistence.

OCR turns pixels into characters; it has no idea that "SUBTOTAL" means subtotal, that "T0TAL" is a misread
"TOTAL", or which lines are purchased items versus a store's address block. That labeling step reuses the
same structured-extraction pattern as the review summarizer (app/services/review_summary.py): raw text in,
one JSON-schema-constrained Gemini call out, so the model cannot return anything outside the shape the
caller expects.
"""
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4
from PIL import UnidentifiedImageError
from pytesseract import TesseractNotFoundError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
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
        "warranty_duration_days": {"type": ["integer", "null"], "description": "Warranty length in days, converted from whatever unit is stated (e.g. '1 year' -> 365, '90 days' -> 90), or null if no warranty duration is stated"},
    },
    "required": ["store_name", "purchase_date", "items", "subtotal", "tax", "total", "currency", "warranty_text", "warranty_duration_days"],
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


def _scan_response(receipt: Receipt, saved: bool) -> ReceiptScanResponse:
    return ReceiptScanResponse(
        id=receipt.id,
        store_name=receipt.store_name,
        purchase_date=receipt.purchase_date,
        subtotal_minor=receipt.subtotal_minor,
        tax_minor=receipt.tax_minor,
        total_minor=receipt.total_minor,
        currency=receipt.currency,
        warranty_text=receipt.warranty_text,
        warranty_expires_at=receipt.warranty_expires_at,
        ocr_confidence=receipt.ocr_confidence,
        items=[ReceiptItemResponse.model_validate(item) for item in receipt.items],
        created_at=receipt.created_at,
        saved=saved,
    )


def _find_by_image_hash(db: Session, user_id: UUID, image_hash: str) -> Receipt | None:
    return db.scalar(select(Receipt).where(Receipt.user_id == user_id, Receipt.image_hash == image_hash))


def scan_receipt(db: Session, image_bytes: bytes, user: User | None) -> ReceiptScanResponse:
    """Full pipeline entry point: OCR the image, extract structured fields via LLM, persist when signed in.

    Re-uploading a photo you've already scanned (byte-for-byte identical, e.g. an accidental double-submit or
    re-uploading the same file) returns the existing saved receipt instead of creating a duplicate history row -
    keyed on a hash of the image bytes, scoped per user so the same receipt photo scanned by two different
    shoppers is not treated as a duplicate. Checked before OCR/the LLM run, so a repeat upload also skips that
    cost entirely.
    """
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    if user:
        existing = _find_by_image_hash(db, user.id, image_hash)
        if existing:
            return _scan_response(existing, saved=True)

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
    # Date arithmetic is done here, not by the LLM (unreliable at computing dates) - the model only has to
    # interpret the vague duration phrase into a number of days.
    warranty_duration_days = fields.get("warranty_duration_days")
    warranty_expires_at = purchase_date + timedelta(days=warranty_duration_days) if purchase_date and warranty_duration_days else None

    now = datetime.now(timezone.utc)
    receipt = Receipt(
        id=uuid4(),
        user_id=user.id if user else None,
        image_hash=image_hash if user else None,
        store_name=fields["store_name"],
        purchase_date=purchase_date,
        subtotal_minor=_to_minor(fields["subtotal"]),
        tax_minor=_to_minor(fields["tax"]),
        total_minor=_to_minor(fields["total"]),
        currency=currency,
        warranty_text=fields["warranty_text"],
        warranty_expires_at=warranty_expires_at,
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
        try:
            db.commit()
        except IntegrityError:
            # Lost a race against an identical concurrent upload (e.g. a double-tapped submit button) that
            # committed its own row for this image_hash between our lookup above and this commit.
            db.rollback()
            existing = _find_by_image_hash(db, user.id, image_hash)
            if existing:
                return _scan_response(existing, saved=True)
            raise
        db.refresh(receipt)

    return _scan_response(receipt, saved=user is not None)


def list_my_receipts(db: Session, user: User) -> list[Receipt]:
    """Return the current user's scanned receipt history, most recent first."""
    return list(db.scalars(select(Receipt).where(Receipt.user_id == user.id).order_by(Receipt.created_at.desc())))


def get_my_receipt(db: Session, user: User, receipt_id: UUID) -> Receipt:
    """Fetch one previously scanned receipt, only if it belongs to the current user."""
    receipt = db.scalar(select(Receipt).where(Receipt.id == receipt_id, Receipt.user_id == user.id))
    if not receipt:
        raise NotFoundError("Receipt not found")
    return receipt


def delete_my_receipt(db: Session, user: User, receipt_id: UUID) -> None:
    """Delete one owned receipt from history, without exposing whether a receipt owned by someone else exists."""
    receipt = db.scalar(select(Receipt).where(Receipt.id == receipt_id, Receipt.user_id == user.id))
    if not receipt:
        raise NotFoundError("Receipt not found")
    db.delete(receipt)
    db.commit()
