"""Request/response contracts for the AI recommendation engine. Every result is a real, live listing found on
the web - there is no internal catalog fallback here, so a shopper can always actually go buy what's shown."""
from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    budget: float | None = Field(default=None, ge=0, description="Maximum budget in major currency units, e.g. rupees")
    purpose: str = Field(min_length=3, max_length=300, description="What the product is for, e.g. 'gaming laptop for college'")
    brand_preference: str | None = Field(default=None, max_length=120)
    features: list[str] = Field(default_factory=list, max_length=10, description="Must-have features, e.g. ['long battery life', 'lightweight']")
    currency: str = Field(default="INR", pattern=r"^[A-Z]{3}$", description="ISO 4217 currency code, e.g. INR")
    category: str | None = Field(default=None, max_length=60, description="Product category to search within, e.g. 'Laptops' - narrows the web search so results aren't cross-category noise.")


class ReviewSnippet(BaseModel):
    """A real excerpt pulled from a live review search - never LLM-generated praise."""
    source: str
    quote: str
    url: str


class RecommendationItem(BaseModel):
    """A real, live product listing found on the web - no internal product_id, so it links out to its own
    source URL rather than an internal review/wishlist page."""
    rank: int
    title: str
    brand: str | None
    retailer: str
    price: float
    currency: str
    image_url: str | None
    url: str
    reason: str
    is_best_pick: bool = False
    reviews: list[ReviewSnippet] = Field(default_factory=list, description="Real review excerpts - only fetched for the best pick.")


class RecommendationResponse(BaseModel):
    interpreted_intent: str
    items: list[RecommendationItem]
