from uuid import UUID
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_current_user_optional, rate_limit
from app.db.session import get_db
from app.models import User
from app.schemas.receipts import ReceiptResponse, ReceiptScanResponse
from app.services.receipt_scanner import delete_my_receipt, get_my_receipt, list_my_receipts, scan_receipt

router = APIRouter(prefix="/receipts", tags=["receipts"])
MAX_IMAGE_BYTES = 10 * 1024 * 1024


@router.post("/scan", response_model=ReceiptScanResponse, dependencies=[Depends(rate_limit(20, 60))])
async def scan_uploaded_receipt(image: UploadFile = File(...), db: Session = Depends(get_db), user: User | None = Depends(get_current_user_optional)) -> ReceiptScanResponse:
    """Upload a receipt photo: OCR extracts raw text, an LLM structures it into JSON. Saved to history when signed in."""
    image_bytes = await image.read()
    if not image_bytes: raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(image_bytes) > MAX_IMAGE_BYTES: raise HTTPException(status_code=413, detail="Image is too large (10MB max)")
    try:
        return scan_receipt(db, image_bytes, user)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("", response_model=list[ReceiptResponse], dependencies=[Depends(rate_limit(60, 60))])
def list_scanned_receipts(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ReceiptResponse]:
    """List the current user's scanned receipt history, most recent first."""
    return list_my_receipts(db, user)


@router.get("/{receipt_id}", response_model=ReceiptResponse, dependencies=[Depends(rate_limit(60, 60))])
def get_scanned_receipt(receipt_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ReceiptResponse:
    """Fetch one previously scanned receipt owned by the current user."""
    return get_my_receipt(db, user, receipt_id)


@router.delete("/{receipt_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(rate_limit(60, 60))])
def delete_scanned_receipt(receipt_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    """Delete one owned receipt from history."""
    delete_my_receipt(db, user, receipt_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
