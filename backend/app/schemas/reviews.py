"""Request/response contracts for review submission and the AI review summarizer."""
from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, computed_field


class CreateReviewRequest(BaseModel):
    rating: int = Field(ge=1, le=5)
    title: str | None = Field(default=None, max_length=160)
    body: str | None = Field(default=None, max_length=5000)
    is_verified_purchase: bool = False


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    rating: int
    title: str | None
    body: str | None
    is_verified_purchase: bool
    created_at: datetime
    trust_score: float | None = Field(default=None, description="Fake-review probability (0=genuine-looking, 1=fake-looking) from the RandomForest+XGBoost ensemble in ml/fake_review_detection. Null until scored.")

    @computed_field
    @property
    def trust_tier(self) -> Literal["trusted", "uncertain", "likely_fake"] | None:
        """Derived at read time from trust_score, not stored - a threshold on one number doesn't need its
        own column, and this way it can never drift out of sync with the score it comes from."""
        if self.trust_score is None:
            return None
        if self.trust_score >= 0.66:
            return "likely_fake"
        if self.trust_score >= 0.33:
            return "uncertain"
        return "trusted"


class RatingBreakdown(BaseModel):
    """Deterministic, code-computed statistics - independent of the LLM, used both as output and as grounding for it."""
    average_rating: float | None
    total_reviews: int
    histogram: dict[int, int]
    positive_pct: float
    neutral_pct: float
    negative_pct: float


class KeywordFrequency(BaseModel):
    keyword: str
    mentions: int


class CommonComplaint(BaseModel):
    complaint: str
    mention_count: int


class OverallSentiment(BaseModel):
    label: Literal["very_positive", "positive", "mixed", "negative", "very_negative"]
    summary: str


class Recommendation(BaseModel):
    verdict: Literal["recommended", "recommended_with_caveats", "not_recommended"]
    rationale: str


class ReviewSummaryResponse(BaseModel):
    product_id: UUID
    reviews_analyzed: int
    rating_breakdown: RatingBreakdown
    top_keywords: list[KeywordFrequency]
    pros: list[str]
    cons: list[str]
    common_complaints: list[CommonComplaint]
    overall_sentiment: OverallSentiment
    recommendation: Recommendation
    generated_at: datetime
