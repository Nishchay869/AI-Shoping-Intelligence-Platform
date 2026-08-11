"""Unit tests for ReviewResponse.trust_tier - pure threshold logic derived from trust_score."""
from datetime import datetime, timezone
from uuid import uuid4
from app.schemas.reviews import ReviewResponse


def _response(trust_score: float | None) -> ReviewResponse:
    return ReviewResponse(id=uuid4(), rating=5, title=None, body=None, is_verified_purchase=False, created_at=datetime.now(timezone.utc), trust_score=trust_score)


def test_trust_tier_none_when_unscored() -> None:
    assert _response(None).trust_tier is None


def test_trust_tier_trusted_below_033() -> None:
    assert _response(0.10).trust_tier == "trusted"


def test_trust_tier_uncertain_boundary_at_033() -> None:
    assert _response(0.33).trust_tier == "uncertain"


def test_trust_tier_likely_fake_boundary_at_066() -> None:
    assert _response(0.66).trust_tier == "likely_fake"
