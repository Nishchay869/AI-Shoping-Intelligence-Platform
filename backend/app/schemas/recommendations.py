"""Request/response contracts for the AI recommendation engine."""
from pydantic import BaseModel, Field
from app.schemas.catalog import ProductResponse


class RecommendationRequest(BaseModel):
    budget: float | None = Field(default=None, ge=0, description="Maximum budget in major currency units, e.g. rupees")
    purpose: str = Field(min_length=3, max_length=300, description="What the product is for, e.g. 'gaming laptop for college'")
    brand_preference: str | None = Field(default=None, max_length=120)
    features: list[str] = Field(default_factory=list, max_length=10, description="Must-have features, e.g. ['long battery life', 'lightweight']")
    currency: str = Field(default="INR", pattern=r"^[A-Z]{3}$", description="ISO 4217 currency code, e.g. INR")


class RecommendationItem(BaseModel):
    rank: int
    product: ProductResponse
    reason: str


class RecommendationResponse(BaseModel):
    """Stable envelope: the ranked picks plus the query-understanding step's synthesized intent, for UI transparency."""
    interpreted_intent: str
    items: list[RecommendationItem]
    unavailable_brand: str | None = Field(default=None, description="Set when the shopper's brand preference matched nothing in stock and these items are the closest alternatives instead.")
