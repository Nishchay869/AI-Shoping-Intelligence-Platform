"""Response contracts for image-based product search."""
from pydantic import BaseModel
from app.schemas.catalog import ProductResponse


class ImageSearchResult(BaseModel):
    product: ProductResponse
    similarity: float


class ImageSearchResponse(BaseModel):
    results: list[ImageSearchResult]
