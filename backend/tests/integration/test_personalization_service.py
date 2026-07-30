"""Integration tests: services/personalization.py against a real Postgres+pgvector database.

This is the one part of the whole platform that was never actually executed against a live pgvector index
before this test suite existed - every earlier verification of it was SQL-compiled or run with the DB
session mocked. Real cosine search, over a real HNSW index, is the point of this file.
"""
import random
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.models import SearchQuery
from app.services import personalization


def _vector_near(base: list[float], noise: float = 0.02) -> list[float]:
    """A vector pointing in nearly the same direction as base - should rank as "similar" under cosine search."""
    return [x + random.uniform(-noise, noise) for x in base]


def _random_vector(dimensions: int = 768) -> list[float]:
    return [random.uniform(-1, 1) for _ in range(dimensions)]


def test_log_click_and_log_purchase_persist_real_rows(db_session, make_user, make_product) -> None:
    from app.models import ProductClick, Purchase

    user = make_user()
    product = make_product()

    personalization.log_click(db_session, user.id, product.id)
    personalization.log_purchase(db_session, user.id, product.id, price_minor=1999, currency="USD")

    click = db_session.query(ProductClick).filter_by(user_id=user.id, product_id=product.id).one()
    purchase = db_session.query(Purchase).filter_by(user_id=user.id, product_id=product.id).one()
    assert click is not None
    assert purchase.price_minor == 1999 and purchase.currency == "USD"


def test_signals_without_a_product_embedding_are_excluded(db_session, make_user, make_product) -> None:
    """A click/purchase/wishlist on a product with no embedding yet (not backfilled) can't contribute a
    direction to the taste vector - it must be silently skipped, not crash the pipeline."""
    user = make_user()
    product = make_product(with_embedding=False)
    personalization.log_click(db_session, user.id, product.id)

    signals = personalization._collect_signals(db_session, user.id)
    assert signals == []


def test_generate_personalized_recommendations_raises_not_found_with_no_activity(db_session, make_user) -> None:
    user = make_user()
    with pytest.raises(NotFoundError):
        personalization.generate_personalized_recommendations(db_session, user.id)


def test_generate_personalized_recommendations_ranks_by_real_cosine_similarity(db_session, make_user, make_product) -> None:
    """Real end-to-end: purchase a product, then confirm pgvector's own cosine search - not our Python math -
    ranks a genuinely similar candidate above an unrelated one, and never recommends the purchased product back."""
    user = make_user()
    base = _random_vector()

    purchased = make_product(title="Wireless Headphones", embedding=base)
    similar_candidate = make_product(title="Similar Wireless Earbuds", embedding=_vector_near(base))
    unrelated_candidate = make_product(title="Unrelated Garden Hose", embedding=_random_vector())

    personalization.log_purchase(db_session, user.id, purchased.id, price_minor=9999, currency="USD")

    result = personalization.generate_personalized_recommendations(db_session, user.id)
    titles = [item.product.title for item in result.items]

    assert purchased.title not in titles  # never recommend back what the user already bought
    assert similar_candidate.title in titles
    assert titles.index(similar_candidate.title) < titles.index(unrelated_candidate.title)
    assert result.signal_counts["purchase"] == 1


def test_generate_personalized_recommendations_explains_from_the_nearest_real_signal(db_session, make_user, make_product) -> None:
    user = make_user()
    base = _random_vector()
    purchased = make_product(title="Espresso Machine", embedding=base)
    candidate = make_product(title="Espresso Cups", embedding=_vector_near(base))

    personalization.log_purchase(db_session, user.id, purchased.id, price_minor=25000, currency="USD")
    result = personalization.generate_personalized_recommendations(db_session, user.id)

    match = next(item for item in result.items if item.product.title == candidate.title)
    assert match.reason == "Because you purchased Espresso Machine"


def test_generate_personalized_recommendations_persists_to_the_recommendation_feed(db_session, make_user, make_product) -> None:
    from sqlalchemy import select

    from app.models import Recommendation, RecommendationReason

    user = make_user()
    base = _random_vector()
    purchased = make_product(embedding=base)
    make_product(embedding=_vector_near(base))
    personalization.log_purchase(db_session, user.id, purchased.id, price_minor=1000, currency="USD")

    personalization.generate_personalized_recommendations(db_session, user.id)

    persisted = list(db_session.scalars(select(Recommendation).where(Recommendation.user_id == user.id, Recommendation.reason == RecommendationReason.BEHAVIORAL)))
    assert len(persisted) >= 1


def test_wishlist_signal_feeds_the_taste_vector_via_real_join(db_session, make_user, make_product) -> None:
    """Wishlist isn't logged through personalization.py at all - it's read live from the existing
    Wishlist/WishlistItem tables, so this exercises that real join independently of the write path."""
    from app.schemas.wishlist import AddWishlistItemRequest, CreateWishlistRequest
    from app.services import wishlist as wishlist_service

    user = make_user()
    base = _random_vector()
    wishlisted = make_product(title="Standing Desk", embedding=base)
    similar_candidate = make_product(title="Similar Standing Desk", embedding=_vector_near(base))

    my_list = wishlist_service.create_wishlist(db_session, user, CreateWishlistRequest())
    wishlist_service.add_item(db_session, user, my_list.id, AddWishlistItemRequest(product_id=wishlisted.id))

    result = personalization.generate_personalized_recommendations(db_session, user.id)
    assert result.signal_counts["wishlist"] == 1
    assert similar_candidate.title in [item.product.title for item in result.items]


def test_log_search_embeds_and_persists(db_session, make_user) -> None:
    """log_search is the one write path that calls the real embedding API - mocked here since a live Gemini
    key isn't available in this environment; the point under test is that it's stored correctly, not that
    Gemini's embeddings are correct."""
    from unittest.mock import patch

    user = make_user()
    fake_embedding = _random_vector()
    with patch("app.services.personalization.embed_query", return_value=fake_embedding) as mocked:
        personalization.log_search(db_session, user.id, "wireless noise cancelling headphones")
        mocked.assert_called_once_with("wireless noise cancelling headphones")

    stored = db_session.query(SearchQuery).filter_by(user_id=user.id).one()
    assert stored.query == "wireless noise cancelling headphones"
    assert stored.embedding is not None
    assert len(stored.embedding) == 768
