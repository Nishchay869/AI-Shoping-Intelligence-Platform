from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, rate_limit
from app.db.session import get_db
from app.models import Product, User
from app.schemas.personalization import LogClickRequest, LogPurchaseRequest, LogSearchRequest
from app.services.personalization import log_click, log_purchase, log_search

router = APIRouter(prefix="/activity", tags=["activity"])


@router.post("/search", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(rate_limit(60, 60))])
def track_search(payload: LogSearchRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    """Record a shopper's search query - embedded once now, feeding the personalized recommendation engine."""
    log_search(db, user.id, payload.query.strip())
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/click", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(rate_limit(120, 60))])
def track_click(payload: LogClickRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    """Record a shopper viewing/clicking a product - the lowest-intent personalization signal."""
    if not db.get(Product, payload.product_id): raise HTTPException(status_code=404, detail="Product not found")
    log_click(db, user.id, payload.product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/purchase", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(rate_limit(30, 60))])
def track_purchase(payload: LogPurchaseRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    """Record a shopper's purchase - the strongest-intent personalization signal."""
    product = db.get(Product, payload.product_id)
    if not product: raise HTTPException(status_code=404, detail="Product not found")
    log_purchase(db, user.id, payload.product_id, payload.price_minor if payload.price_minor is not None else product.current_price_minor, payload.currency or product.currency)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
