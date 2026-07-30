"""Personalized Shopping Recommendation Engine: builds each shopper's "taste vector" purely from the embeddings
of their own past behavior - search queries, wishlist, purchases, clicks - then finds nearby catalog products via
pgvector cosine search.

Deliberately LLM-free, unlike the explicit budget/purpose engine (services/recommendations.py): there, every
signal starts as free text that has to be interpreted before it can be embedded. Here every signal is already
structured - a product id, or a query embedded once at capture time in log_search - so there is no free text
left to interpret. Personalization is pure vector arithmetic, which keeps it cheap enough to recompute on every
page load rather than only on an explicit request.

Architecture:
  1. Track (log_search / log_click / log_purchase, plus the existing wishlist endpoints): every shopper action
     is written once, as it happens. A search embeds immediately so no embedding call is needed later.
  2. Collect (_collect_signals): pull each user's recent searches, wishlist items, purchases, and clicks, each
     carrying its own embedding (the product's, for anything tied to a product) plus an intent weight and a
     recency weight (exponential half-life - a purchase from a year ago should matter less than one from
     yesterday, but should never hit exactly zero).
  3. Build (_profile_vector): a single weighted average of every signal's embedding, L2-normalized back onto
     the unit sphere the rest of the catalog's embeddings live on, since cosine search only cares about
     direction.
  4. Retrieve (generate_personalized_recommendations): pgvector cosine search against Product.embedding,
     excluding products the user already owns/wishlisted, same index the catalog search and the explicit
     recommendation engine already use.
  5. Explain (_nearest_signal / _explain): for each pick, cite whichever of the user's own signals is closest
     to it in embedding space - real, inspectable evidence, not a generated sentence.
"""
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session, joinedload
from app.core.exceptions import NotFoundError
from app.infrastructure.embeddings import embed_query
from app.models import Product, ProductClick, Purchase, Recommendation, RecommendationReason, SearchQuery, Wishlist, WishlistItem
from app.schemas.personalization import PersonalizedRecommendationItem, PersonalizedRecommendationResponse

RECENCY_HALF_LIFE_DAYS = 30.0
SIGNAL_WEIGHTS = {"purchase": 5.0, "wishlist": 3.0, "search": 2.0, "click": 1.0}
MAX_SIGNALS_PER_TYPE = 50
CANDIDATE_POOL_SIZE = 30
TOP_PICKS = 10


@dataclass(frozen=True)
class Signal:
    vector: list[float]
    weight: float
    kind: str
    label: str
    product_id: UUID | None


def log_search(db: Session, user_id: UUID, query: str) -> None:
    """Record a shopper's search, embedding it once now so recommendation generation never calls the embedding API."""
    embedding = embed_query(query)
    db.add(SearchQuery(user_id=user_id, query=query, embedding=embedding))
    db.commit()


def log_click(db: Session, user_id: UUID, product_id: UUID) -> None:
    """Record a shopper viewing/clicking a product - the lowest-intent personalization signal."""
    db.add(ProductClick(user_id=user_id, product_id=product_id))
    db.commit()


def log_purchase(db: Session, user_id: UUID, product_id: UUID, price_minor: int, currency: str) -> None:
    """Record a shopper's purchase - the strongest-intent personalization signal."""
    db.add(Purchase(user_id=user_id, product_id=product_id, price_minor=price_minor, currency=currency))
    db.commit()


def _recency_weight(occurred_at: datetime) -> float:
    """Exponential decay with a 30-day half-life: recent activity dominates, old activity fades but never vanishes."""
    age_days = (datetime.now(timezone.utc) - occurred_at.replace(tzinfo=timezone.utc)).total_seconds() / 86400
    return math.pow(0.5, max(age_days, 0.0) / RECENCY_HALF_LIFE_DAYS)


def _collect_signals(db: Session, user_id: UUID) -> list[Signal]:
    signals: list[Signal] = []

    searches = list(db.scalars(select(SearchQuery).where(SearchQuery.user_id == user_id, SearchQuery.embedding.is_not(None)).order_by(SearchQuery.created_at.desc()).limit(MAX_SIGNALS_PER_TYPE)))
    signals += [Signal(vector=row.embedding, weight=SIGNAL_WEIGHTS["search"] * _recency_weight(row.created_at), kind="search", label=row.query, product_id=None) for row in searches]

    wishlist_items = list(db.scalars(select(WishlistItem).join(Wishlist).where(Wishlist.user_id == user_id).options(joinedload(WishlistItem.product))))
    signals += [Signal(vector=item.product.embedding, weight=SIGNAL_WEIGHTS["wishlist"], kind="wishlist", label=item.product.title, product_id=item.product_id) for item in wishlist_items if item.product.embedding is not None]

    purchases = list(db.scalars(select(Purchase).where(Purchase.user_id == user_id).options(joinedload(Purchase.product)).order_by(Purchase.created_at.desc()).limit(MAX_SIGNALS_PER_TYPE)))
    signals += [Signal(vector=row.product.embedding, weight=SIGNAL_WEIGHTS["purchase"] * _recency_weight(row.created_at), kind="purchase", label=row.product.title, product_id=row.product_id) for row in purchases if row.product.embedding is not None]

    clicks = list(db.scalars(select(ProductClick).where(ProductClick.user_id == user_id).options(joinedload(ProductClick.product)).order_by(ProductClick.created_at.desc()).limit(MAX_SIGNALS_PER_TYPE)))
    signals += [Signal(vector=row.product.embedding, weight=SIGNAL_WEIGHTS["click"] * _recency_weight(row.created_at), kind="click", label=row.product.title, product_id=row.product_id) for row in clicks if row.product.embedding is not None]

    return signals


def _weighted_average(vectors: list[list[float]], weights: list[float]) -> list[float]:
    total_weight = sum(weights) or 1.0
    dims = len(vectors[0])
    return [sum(vector[d] * weight for vector, weight in zip(vectors, weights)) / total_weight for d in range(dims)]


def _l2_normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vector))
    return [x / norm for x in vector] if norm > 0 else vector


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b) if norm_a > 0 and norm_b > 0 else 0.0


def _profile_vector(signals: list[Signal]) -> list[float]:
    weighted = _weighted_average([s.vector for s in signals], [s.weight for s in signals])
    return _l2_normalize(weighted)


def _nearest_signal(candidate_vector: list[float], signals: list[Signal]) -> Signal:
    """Explain a recommendation without an LLM call: cite whichever of the user's own signals is closest to it."""
    return max(signals, key=lambda s: _cosine_similarity(candidate_vector, s.vector))


def _explain(signal: Signal) -> str:
    if signal.kind == "search": return f'Because you searched for "{signal.label}"'
    if signal.kind == "wishlist": return f"Because you wishlisted {signal.label}"
    if signal.kind == "purchase": return f"Because you purchased {signal.label}"
    return f"Because you viewed {signal.label}"


def _persist_feed(db: Session, user_id: UUID, items: list[tuple[UUID, float, str]]) -> None:
    """Record the generated picks as the shopper's behavioral recommendation feed, upserting on repeat requests."""
    for product_id, score, explanation in items:
        stmt = pg_insert(Recommendation).values(user_id=user_id, product_id=product_id, reason=RecommendationReason.BEHAVIORAL, score=score, explanation=explanation, is_dismissed=False)
        stmt = stmt.on_conflict_do_update(constraint="uq_recommendation_user_product_reason", set_={"score": stmt.excluded.score, "explanation": stmt.excluded.explanation, "is_dismissed": False})
        db.execute(stmt)
    db.commit()


def generate_personalized_recommendations(db: Session, user_id: UUID) -> PersonalizedRecommendationResponse:
    """Full pipeline entry point: gather this user's own behavioral embeddings, build one taste vector, retrieve."""
    signals = _collect_signals(db, user_id)
    if not signals:
        raise NotFoundError("Not enough activity yet - search, wishlist, click, or buy a few products to unlock personalized picks")

    profile = _profile_vector(signals)
    already_seen = {s.product_id for s in signals if s.product_id is not None}

    query = (
        select(Product, (1 - Product.embedding.cosine_distance(profile)).label("similarity"))
        .where(Product.embedding.is_not(None))
        .order_by(Product.embedding.cosine_distance(profile))
        .limit(CANDIDATE_POOL_SIZE)
    )
    candidates = [(product, float(similarity)) for product, similarity in db.execute(query).all() if product.id not in already_seen][:TOP_PICKS]
    if not candidates:
        raise NotFoundError("No new products to recommend right now")

    items: list[PersonalizedRecommendationItem] = []
    persisted: list[tuple[UUID, float, str]] = []
    for rank, (product, similarity) in enumerate(candidates, start=1):
        nearest = _nearest_signal(product.embedding, signals)
        explanation = _explain(nearest)
        # Cosine similarity ranges [-1, 1]; the shared `recommendations` table's score column (also written
        # by the explicit engine in services/recommendations.py) has a CHECK (score BETWEEN 0 AND 1). A
        # candidate that only weakly/negatively matches the taste vector still made the top-K pool here, so
        # clamp rather than exclude it - order is unaffected, and it reads as "~0% match" instead of crashing
        # the whole request with a constraint violation the one time a real candidate's similarity dips
        # negative (caught by tests/integration/test_personalization_service.py against a real database).
        clamped_score = round(max(similarity, 0.0), 4)
        items.append(PersonalizedRecommendationItem(rank=rank, product=product, similarity=clamped_score, reason=explanation))
        persisted.append((product.id, clamped_score, explanation))

    _persist_feed(db, user_id, persisted)
    signal_counts = {kind: sum(1 for s in signals if s.kind == kind) for kind in SIGNAL_WEIGHTS}
    return PersonalizedRecommendationResponse(items=items, signal_counts=signal_counts)
