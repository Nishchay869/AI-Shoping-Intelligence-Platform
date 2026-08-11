"""Integration tests: services/reviews.py against a real Postgres database."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from app.models import Review
from app.schemas.reviews import CreateReviewRequest
from app.services import reviews as reviews_service


def test_create_review_persists_trust_score_from_the_ensemble(db_session, make_user, make_product) -> None:
    user = make_user()
    product = make_product()
    with patch("app.services.reviews.score_texts", return_value=[0.82]):
        review = reviews_service.create_review(db_session, user, product.id, CreateReviewRequest(rating=5, body="Amazing, buy now!!!"))
    assert float(review.trust_score) == 0.82


def test_create_review_leaves_trust_score_null_if_scoring_fails(db_session, make_user, make_product) -> None:
    user = make_user()
    product = make_product()
    with patch("app.services.reviews.score_texts", side_effect=RuntimeError("model unavailable")):
        review = reviews_service.create_review(db_session, user, product.id, CreateReviewRequest(rating=5, body="Fine."))
    assert review.trust_score is None


def test_list_reviews_returns_newest_first(db_session, make_user, make_product) -> None:
    product = make_product()
    older = Review(user_id=make_user().id, product_id=product.id, rating=5, body="old", created_at=datetime.now(timezone.utc) - timedelta(days=2))
    newer = Review(user_id=make_user().id, product_id=product.id, rating=4, body="new", created_at=datetime.now(timezone.utc) - timedelta(days=1))
    db_session.add_all([older, newer])
    db_session.commit()

    result = reviews_service.list_reviews(db_session, product.id)
    assert [r.id for r in result] == [newer.id, older.id]


def test_list_reviews_excludes_invisible_reviews(db_session, make_user, make_product) -> None:
    product = make_product()
    db_session.add(Review(user_id=make_user().id, product_id=product.id, rating=1, body="hidden", is_visible=False))
    db_session.commit()
    assert reviews_service.list_reviews(db_session, product.id) == []


def test_list_reviews_respects_limit_and_offset(db_session, make_user, make_product) -> None:
    product = make_product()
    for i in range(3):
        db_session.add(Review(user_id=make_user().id, product_id=product.id, rating=5, body=f"r{i}", created_at=datetime.now(timezone.utc) - timedelta(minutes=i)))
    db_session.commit()
    page = reviews_service.list_reviews(db_session, product.id, limit=2, offset=1)
    assert len(page) == 2
