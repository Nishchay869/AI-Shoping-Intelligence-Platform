"""Request/response contracts for the AI Receipt Scanner (OCR + LLM structured extraction)."""
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class ReceiptItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_name: str
    price_minor: int
    quantity: int


class ReceiptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    store_name: str | None
    purchase_date: date | None
    subtotal_minor: int | None
    tax_minor: int | None
    total_minor: int | None
    currency: str
    warranty_text: str | None
    ocr_confidence: float | None
    items: list[ReceiptItemResponse]
    created_at: datetime


class ReceiptScanResponse(ReceiptResponse):
    """Same fields as a stored receipt, plus whether this scan was actually saved to the shopper's history."""
    saved: bool
