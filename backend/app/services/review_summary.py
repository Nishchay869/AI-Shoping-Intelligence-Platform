"""AI review summarizer: NLP preprocessing -> map (per-chunk LLM extraction, parallelized) -> reduce (LLM synthesis).

5000 reviews cannot be handed to one LLM call reliably or cheaply - long reviews alone could push past a
sane single-request token/latency budget, and asking one call to hold a global tally across thousands of
items invites it to guess rather than count. Instead this follows the standard map-reduce shape:
  1. Deterministic NLP pass (review_nlp.py): clean, deduplicate, and compute rating/keyword statistics.
  2. Map: split into small batches, extract structured pros/cons/complaints/sentiment per batch in parallel.
  3. Reduce: merge the batches' candidate lists (counts summed in code, wording merged by one final LLM
     call) into the five sections the caller asked for, grounded in the real aggregate numbers.
"""
import json
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ServiceUnavailableError
from app.infrastructure.cache import get_json, review_summary_key, set_json
from app.infrastructure.llm import create_message
from app.models import Product, Review
from app.schemas.reviews import CommonComplaint, OverallSentiment, Recommendation, ReviewSummaryResponse
from app.services.review_nlp import compute_rating_breakdown, deduplicate, extract_top_keywords

logger = logging.getLogger(__name__)
MAX_REVIEWS = 5000
CHUNK_SIZE = 100
MAX_WORKERS = 8
CACHE_TTL_SECONDS = 6 * 60 * 60

_CHUNK_SCHEMA = {
    "type": "object",
    "properties": {
        "pros": {"type": "array", "items": {"type": "object", "properties": {"point": {"type": "string"}, "mentions": {"type": "integer"}}, "required": ["point", "mentions"], "additionalProperties": False}},
        "cons": {"type": "array", "items": {"type": "object", "properties": {"point": {"type": "string"}, "mentions": {"type": "integer"}}, "required": ["point", "mentions"], "additionalProperties": False}},
        "complaints": {"type": "array", "items": {"type": "object", "properties": {"point": {"type": "string"}, "mentions": {"type": "integer"}}, "required": ["point", "mentions"], "additionalProperties": False}},
        "sentiment_counts": {"type": "object", "properties": {"positive": {"type": "integer"}, "neutral": {"type": "integer"}, "negative": {"type": "integer"}}, "required": ["positive", "neutral", "negative"], "additionalProperties": False},
    },
    "required": ["pros", "cons", "complaints", "sentiment_counts"],
    "additionalProperties": False,
}

_REDUCE_SCHEMA = {
    "type": "object",
    "properties": {
        "pros": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
        "cons": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
        "common_complaints": {"type": "array", "maxItems": 8, "items": {"type": "object", "properties": {"complaint": {"type": "string"}, "mention_count": {"type": "integer"}}, "required": ["complaint", "mention_count"], "additionalProperties": False}},
        "overall_sentiment": {"type": "object", "properties": {"label": {"type": "string", "enum": ["very_positive", "positive", "mixed", "negative", "very_negative"]}, "summary": {"type": "string"}}, "required": ["label", "summary"], "additionalProperties": False},
        "recommendation": {"type": "object", "properties": {"verdict": {"type": "string", "enum": ["recommended", "recommended_with_caveats", "not_recommended"]}, "rationale": {"type": "string"}}, "required": ["verdict", "rationale"], "additionalProperties": False},
    },
    "required": ["pros", "cons", "common_complaints", "overall_sentiment", "recommendation"],
    "additionalProperties": False,
}


def _chunk(reviews: list[Review], size: int) -> list[list[Review]]:
    return [reviews[i:i + size] for i in range(0, len(reviews), size)]


def _render_batch(batch: list[Review]) -> str:
    lines = []
    for review in batch:
        body = (review.body or "").replace("\n", " ").strip()
        lines.append(f"[{review.rating} stars] {review.title or ''} {body}".strip())
    return "\n".join(f"- {line}" for line in lines)


def _summarize_chunk(batch: list[Review]) -> dict:
    """Map step: extract recurring pros/cons/complaints and a sentiment tally from one batch of reviews."""
    settings = get_settings()
    prompt = f"Analyze this batch of {len(batch)} product reviews (each prefixed with its star rating):\n\n{_render_batch(batch)}"
    response = create_message(
        model=settings.recommendation_model,
        max_tokens=2048,
        system=(
            "You extract recurring patterns from a batch of product reviews. Report only things that actually "
            "recur in this batch - each pro/con/complaint as a short phrase plus how many reviews in this batch "
            "mention it. Distinguish cons (general product weaknesses or trade-offs, e.g. 'premium price') from "
            "complaints (specific things going wrong for customers, e.g. 'battery degrades within months'). "
            "Classify every review's sentiment by reading its text, not just echoing its star rating, and make "
            "sure positive+neutral+negative sums to the batch size."
        ),
        messages=[{"role": "user", "content": prompt}],
        output_config={"format": {"type": "json_schema", "schema": _CHUNK_SCHEMA}},
    )
    if response.stop_reason == "refusal":
        raise ServiceUnavailableError("The assistant declined to process a batch of reviews")
    return json.loads(response.content[0].text)


def _map_chunks(chunks: list[list[Review]]) -> list[dict]:
    """Run the map step across chunks in parallel; a slow or failed batch shouldn't block the rest."""
    summaries: list[dict] = []
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(chunks))) as pool:
        futures = {pool.submit(_summarize_chunk, chunk): index for index, chunk in enumerate(chunks)}
        for future in as_completed(futures):
            try:
                summaries.append(future.result())
            except Exception:
                logger.exception("chunk_summarization_failed batch=%s", futures[future])
    if not summaries:
        raise ServiceUnavailableError("The assistant could not process any batch of reviews")
    return summaries


def _aggregate(chunk_summaries: list[dict]) -> tuple[dict[str, int], dict[str, int], dict[str, int], dict[str, int]]:
    """Reduce step, deterministic half: sum mention counts for identical phrasing and total the sentiment tally in code."""
    pros: dict[str, int] = defaultdict(int)
    cons: dict[str, int] = defaultdict(int)
    complaints: dict[str, int] = defaultdict(int)
    sentiment_totals = {"positive": 0, "neutral": 0, "negative": 0}
    for summary in chunk_summaries:
        for item in summary.get("pros", []): pros[item["point"]] += item["mentions"]
        for item in summary.get("cons", []): cons[item["point"]] += item["mentions"]
        for item in summary.get("complaints", []): complaints[item["point"]] += item["mentions"]
        for key in sentiment_totals: sentiment_totals[key] += summary.get("sentiment_counts", {}).get(key, 0)
    return pros, cons, complaints, sentiment_totals


def _top_candidates(counted: dict[str, int], limit: int = 30) -> str:
    ranked = sorted(counted.items(), key=lambda pair: pair[1], reverse=True)[:limit]
    return "\n".join(f"- {point} (mentioned {count}x across batches)" for point, count in ranked) or "(none found)"


def _synthesize(product_title: str, pros: dict[str, int], cons: dict[str, int], complaints: dict[str, int], sentiment_totals: dict[str, int], reviews_analyzed: int) -> dict:
    """Reduce step, LLM half: merge semantically duplicate candidates and write the final grounded sentiment/recommendation."""
    settings = get_settings()
    total_sentiment = sum(sentiment_totals.values()) or 1
    sentiment_pct = {key: round((value / total_sentiment) * 100, 1) for key, value in sentiment_totals.items()}
    prompt = (
        f"Product: {product_title}\n"
        f"Reviews analyzed: {reviews_analyzed}\n"
        f"Measured sentiment split: {sentiment_pct['positive']}% positive, {sentiment_pct['neutral']}% neutral, {sentiment_pct['negative']}% negative\n\n"
        f"Candidate pros (from batch-level extraction, may contain near-duplicates to merge):\n{_top_candidates(pros)}\n\n"
        f"Candidate cons:\n{_top_candidates(cons)}\n\n"
        f"Candidate complaints:\n{_top_candidates(complaints)}\n\n"
        "Merge near-duplicate phrasings (summing their mention counts), and return the final top pros, cons, and "
        "common complaints. Your overall_sentiment.label must be consistent with the measured sentiment split "
        "above, not just the tone of the strongest quotes."
    )
    response = create_message(
        model=settings.recommendation_model,
        max_tokens=2048,
        system=(
            "You synthesize a final review summary from pre-aggregated batch data covering thousands of reviews. "
            "Never invent a pro, con, or complaint that isn't among the candidates provided. Ground your "
            "recommendation verdict in the actual sentiment split and the severity/frequency of the complaints."
        ),
        messages=[{"role": "user", "content": prompt}],
        output_config={"format": {"type": "json_schema", "schema": _REDUCE_SCHEMA}},
    )
    if response.stop_reason == "refusal":
        raise ServiceUnavailableError("The assistant declined to synthesize the final review summary")
    return json.loads(response.content[0].text)


def summarize_product_reviews(db: Session, product_id: UUID) -> ReviewSummaryResponse:
    """Full pipeline entry point: fetch a product's reviews, run NLP + map-reduce LLM summarization, cache the result."""
    product = db.get(Product, product_id)
    if not product: raise NotFoundError("Product not found")
    raw_reviews = list(db.scalars(select(Review).where(Review.product_id == product_id, Review.is_visible.is_(True)).order_by(Review.created_at.desc()).limit(MAX_REVIEWS)))
    reviews = deduplicate(raw_reviews)
    if not reviews: raise NotFoundError("No reviews yet for this product")

    cache_key = review_summary_key(product_id, len(reviews))
    if cached := get_json(cache_key):
        return ReviewSummaryResponse(**cached)

    breakdown = compute_rating_breakdown(reviews)
    keywords = extract_top_keywords(reviews)
    chunk_summaries = _map_chunks(_chunk(reviews, CHUNK_SIZE))
    pros, cons, complaints, sentiment_totals = _aggregate(chunk_summaries)
    synthesized = _synthesize(product.title, pros, cons, complaints, sentiment_totals, len(reviews))

    response = ReviewSummaryResponse(
        product_id=product_id,
        reviews_analyzed=len(reviews),
        rating_breakdown=breakdown,
        top_keywords=keywords,
        pros=synthesized["pros"],
        cons=synthesized["cons"],
        common_complaints=[CommonComplaint(**item) for item in synthesized["common_complaints"]],
        overall_sentiment=OverallSentiment(**synthesized["overall_sentiment"]),
        recommendation=Recommendation(**synthesized["recommendation"]),
        generated_at=datetime.now(timezone.utc),
    )
    set_json(cache_key, response.model_dump(mode="json"), ttl_seconds=CACHE_TTL_SECONDS)
    return response
