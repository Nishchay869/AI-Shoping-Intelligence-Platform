from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    brand: str | None
    category: str | None
    image_url: str | None
    currency: str
    current_price_minor: int
    retailer: str
    average_rating: float | None
    review_count: int
    created_at: datetime


class ProductQuery(BaseModel):
    q: str | None = Field(default=None, min_length=1, max_length=120)
    category: str | None = Field(default=None, max_length=120)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ProductSearchResponse(BaseModel):
    """Stable pagination envelope so clients never infer total results from one page."""
    items: list[ProductResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
