"""Response contracts for image-based product search."""
from pydantic import BaseModel
from app.schemas.catalog import ProductResponse
from app.schemas.price_comparison import PriceListingResponse


class ImageSearchResult(BaseModel):
    product: ProductResponse
    similarity: float


class ImageSearchResponse(BaseModel):
    results: list[ImageSearchResult]
    identified_as: str | None = None
    web_listings: list[PriceListingResponse] = []
