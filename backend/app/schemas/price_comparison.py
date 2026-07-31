"""Request/response contracts for cross-retailer price comparison."""
from pydantic import BaseModel, Field


class PriceComparisonRequest(BaseModel):
    product_name: str = Field(min_length=2, max_length=200, description="e.g. 'Sony WH-1000XM5 headphones'")


class PriceListingResponse(BaseModel):
    retailer: str
    price: float
    currency: str
    url: str


class PriceComparisonResponse(BaseModel):
    listings: list[PriceListingResponse]
