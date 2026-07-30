"""Request/response contracts for the personalized (embeddings-only, LLM-free) recommendation engine."""
from uuid import UUID
from pydantic import BaseModel, Field
from app.schemas.catalog import ProductResponse


class LogSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=300)


class LogClickRequest(BaseModel):
    product_id: UUID


class LogPurchaseRequest(BaseModel):
    product_id: UUID
    price_minor: int | None = Field(default=None, ge=0, description="Defaults to the product's current listed price if omitted")
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$", description="ISO 4217 currency code, e.g. USD")


class PersonalizedRecommendationItem(BaseModel):
    rank: int
    product: ProductResponse
    similarity: float
    reason: str


class PersonalizedRecommendationResponse(BaseModel):
    """Stable envelope: ranked picks plus how many of each signal type fed the taste vector, for UI transparency."""
    items: list[PersonalizedRecommendationItem]
    signal_counts: dict[str, int]
