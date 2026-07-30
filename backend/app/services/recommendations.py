"""AI recommendation engine: LLM query understanding -> embedding -> pgvector similarity search -> LLM ranking with explanations."""
import json
import logging
from dataclasses import dataclass
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ServiceUnavailableError
from app.infrastructure.embeddings import embed_query
from app.infrastructure.llm import create_message
from app.models import Product, Recommendation, RecommendationReason
from app.schemas.recommendations import RecommendationItem, RecommendationRequest, RecommendationResponse

logger = logging.getLogger(__name__)
CANDIDATE_POOL_SIZE = 20
TOP_PICKS = 5


@dataclass(frozen=True)
class QueryUnderstanding:
    """Structured output of step 1: a hard-filter plus an embeddable description of the shopper's ideal product."""
    ideal_product_description: str
    max_price_minor: int | None
    brand: str | None


def _understand_query(request: RecommendationRequest) -> QueryUnderstanding:
    """Step 1 (prompt engineering + LLM): turn free-form budget/purpose/brand/features into a structured filter and a rich, embeddable product description."""
    settings = get_settings()
    schema = {
        "type": "object",
        "properties": {
            "ideal_product_description": {
                "type": "string",
                "description": "A concrete, richly descriptive paragraph of the single ideal product for this shopper, written like a product listing (concrete nouns, attributes, use-cases) for semantic embedding search - not shown to the user verbatim as a recommendation.",
            },
            "max_price_minor": {
                "type": ["integer", "null"],
                "description": f"Hard price ceiling in minor units of {request.currency} (e.g. paise/cents). Null only if no budget was implied.",
            },
            "brand": {
                "type": ["string", "null"],
                "description": "A single normalized brand name if the shopper expressed a preference, else null. Never invent a brand.",
            },
        },
        "required": ["ideal_product_description", "max_price_minor", "brand"],
        "additionalProperties": False,
    }
    prompt = (
        f"Budget: {request.budget if request.budget is not None else 'not specified'} {request.currency}\n"
        f"Purpose: {request.purpose}\n"
        f"Brand preference: {request.brand_preference or 'none'}\n"
        f"Desired features: {', '.join(request.features) or 'none specified'}"
    )
    response = create_message(
        model=settings.recommendation_model,
        max_tokens=1024,
        system=(
            "You are a shopping intelligence assistant. Convert a shopper's stated budget, purpose, brand "
            "preference, and desired features into a structured query for a product search engine. Never invent "
            "a brand or a price ceiling the shopper did not imply."
        ),
        messages=[{"role": "user", "content": prompt}],
        output_config={"format": {"type": "json_schema", "schema": schema}},
    )
    if response.stop_reason == "refusal":
        raise ServiceUnavailableError("The assistant declined to process this request")
    payload = json.loads(response.content[0].text)
    max_price_minor = payload["max_price_minor"]
    if max_price_minor is None and request.budget is not None:
        max_price_minor = round(request.budget * 100)
    return QueryUnderstanding(ideal_product_description=payload["ideal_product_description"], max_price_minor=max_price_minor, brand=payload["brand"])


def _find_candidates(db: Session, understanding: QueryUnderstanding, query_embedding: list[float]) -> tuple[list[Product], bool]:
    """Step 3 (vector database + similarity search): cosine-nearest indexed products, with hard filters applied in
    SQL before ranking. Returns (candidates, brand_unmatched) - brand_unmatched is True when a stated brand
    preference matched nothing indexed and had to be dropped, so the caller can make the ranker (and the
    shopper) aware the substitution happened rather than passing it through silently."""
    base = select(Product).where(Product.embedding.is_not(None))
    if understanding.max_price_minor is not None:
        base = base.where(Product.current_price_minor <= understanding.max_price_minor)
    filtered = base
    if understanding.brand:
        filtered = filtered.where(Product.brand.ilike(f"%{understanding.brand}%"))
    filtered = filtered.order_by(Product.embedding.cosine_distance(query_embedding)).limit(CANDIDATE_POOL_SIZE)
    candidates = list(db.scalars(filtered))
    if candidates or not understanding.brand:
        return candidates, False
    # Brand filter matched nothing indexed: fall back to price-only similarity rather than returning an empty result.
    logger.info("brand_filter_fallback requested_brand=%s", understanding.brand)
    fallback = base.order_by(Product.embedding.cosine_distance(query_embedding)).limit(CANDIDATE_POOL_SIZE)
    return list(db.scalars(fallback)), True


def _rank_and_explain(request: RecommendationRequest, understanding: QueryUnderstanding, candidates: list[Product], brand_unmatched: bool) -> list[tuple[UUID, str]]:
    """Step 4 (LLM re-ranking, grounded in real data): pick and order the top picks from actual candidates, explaining each from its own attributes."""
    settings = get_settings()
    candidate_ids = [str(c.id) for c in candidates]
    catalog_text = "\n".join(
        f"- id={c.id} | {c.title} | brand={c.brand or 'unknown'} | category={c.category or 'unknown'} | "
        f"price={c.current_price_minor / 100:.2f} {c.currency} | rating={c.average_rating if c.average_rating is not None else 'n/a'} ({c.review_count} reviews)"
        for c in candidates
    )
    schema = {
        "type": "object",
        "properties": {
            "picks": {
                "type": "array",
                "minItems": 1,
                "maxItems": TOP_PICKS,
                "items": {
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "string", "enum": candidate_ids},
                        "reason": {"type": "string", "description": "2-3 concrete sentences on why this exact product fits this shopper, citing its actual price/brand/rating/category."},
                    },
                    "required": ["product_id", "reason"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["picks"],
        "additionalProperties": False,
    }
    brand_note = (
        f"\nIMPORTANT: the shopper asked for brand '{understanding.brand}', but nothing in stock matches it - these "
        f"candidates are the closest alternatives by budget/features instead. Every reason must open by disclosing "
        f"that '{understanding.brand}' isn't available before explaining why the alternative still fits.\n"
        if brand_unmatched and understanding.brand else ""
    )
    prompt = (
        f"Shopper wants: {understanding.ideal_product_description}\n\n"
        f"Stated purpose: {request.purpose}\n"
        f"Stated must-have features: {', '.join(request.features) or 'none specified'}\n"
        f"{brand_note}\n"
        f"Candidate products (already filtered by budget/brand and ordered by semantic similarity):\n{catalog_text}\n\n"
        f"Pick the best {TOP_PICKS} (fewer only if fewer genuinely fit) and order them best-first."
    )
    response = create_message(
        model=settings.recommendation_model,
        max_tokens=2048,
        system=(
            "You are a shopping assistant. Only recommend products from the provided candidate list - never invent "
            "a product_id. Ground every explanation in the candidate's actual attributes, not generic praise. Never "
            "imply a product matches a brand preference it doesn't actually meet."
        ),
        messages=[{"role": "user", "content": prompt}],
        output_config={"format": {"type": "json_schema", "schema": schema}},
    )
    if response.stop_reason == "refusal":
        raise ServiceUnavailableError("The assistant declined to process this request")
    payload = json.loads(response.content[0].text)
    return [(UUID(pick["product_id"]), pick["reason"]) for pick in payload["picks"]]


def _persist_feed(db: Session, user_id: UUID, ranked: list[tuple[UUID, str]]) -> None:
    """Record the generated picks as the shopper's AI-personalized recommendation feed, upserting on repeat requests."""
    total = len(ranked) or 1
    for index, (product_id, reason) in enumerate(ranked):
        score = round((total - index) / total, 4)
        stmt = pg_insert(Recommendation).values(user_id=user_id, product_id=product_id, reason=RecommendationReason.AI_PERSONALIZED, score=score, explanation=reason, is_dismissed=False)
        stmt = stmt.on_conflict_do_update(constraint="uq_recommendation_user_product_reason", set_={"score": stmt.excluded.score, "explanation": stmt.excluded.explanation, "is_dismissed": False})
        db.execute(stmt)
    db.commit()


def generate_recommendations(db: Session, request: RecommendationRequest, user_id: UUID | None) -> RecommendationResponse:
    """Run the full pipeline and return the top picks; persists to the user's feed only when the caller is authenticated."""
    understanding = _understand_query(request)
    query_embedding = embed_query(understanding.ideal_product_description)
    candidates, brand_unmatched = _find_candidates(db, understanding, query_embedding)
    if not candidates:
        raise NotFoundError("No indexed products matched this request yet")
    ranked = _rank_and_explain(request, understanding, candidates, brand_unmatched)
    by_id = {c.id: c for c in candidates}
    items = [RecommendationItem(rank=i + 1, product=product, reason=reason) for i, (product_id, reason) in enumerate(ranked) if (product := by_id.get(product_id)) is not None]
    if user_id is not None:
        _persist_feed(db, user_id, ranked)
    return RecommendationResponse(
        interpreted_intent=understanding.ideal_product_description,
        items=items,
        unavailable_brand=understanding.brand if brand_unmatched else None,
    )
