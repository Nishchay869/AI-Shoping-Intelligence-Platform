from uuid import UUID
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import rate_limit
from app.db.session import get_db
from app.models import Product
from app.schemas.catalog import ProductResponse
from app.schemas.image_search import ImageSearchResponse, ImageSearchResult
from app.services.image_search import search_by_image

router = APIRouter(prefix="/products", tags=["products"])
MAX_IMAGE_BYTES = 10 * 1024 * 1024


@router.get("", response_model=list[ProductResponse], dependencies=[Depends(rate_limit(120, 60))])
def list_products(q: str | None = Query(default=None, min_length=1, max_length=120), category: str | None = Query(default=None, max_length=120), limit: int = Query(default=20, ge=1, le=100), offset: int = Query(default=0, ge=0), db: Session = Depends(get_db)) -> list[Product]:
    """Search the catalog using parameterized SQLAlchemy filters and bounded pagination."""
    query = select(Product).order_by(Product.created_at.desc()).limit(limit).offset(offset)
    if q: query = query.where(Product.title.ilike(f"%{q.strip()}%"))
    if category: query = query.where(Product.category == category.strip())
    return list(db.scalars(query))


@router.get("/{product_id}", response_model=ProductResponse, dependencies=[Depends(rate_limit(120, 60))])
def get_product(product_id: UUID, db: Session = Depends(get_db)) -> Product:
    """Fetch a single canonical catalog product."""
    product = db.get(Product, product_id)
    if not product: raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/image-search", response_model=ImageSearchResponse, dependencies=[Depends(rate_limit(20, 60))])
async def search_products_by_image(image: UploadFile = File(...), top_k: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)) -> ImageSearchResponse:
    """Upload a photo to find visually similar catalog products - CLIP image embedding, pgvector cosine search."""
    image_bytes = await image.read()
    if not image_bytes: raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(image_bytes) > MAX_IMAGE_BYTES: raise HTTPException(status_code=413, detail="Image is too large (10MB max)")
    try:
        matches = search_by_image(db, image_bytes, top_k=top_k)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return ImageSearchResponse(results=[ImageSearchResult(product=product, similarity=similarity) for product, similarity in matches])
