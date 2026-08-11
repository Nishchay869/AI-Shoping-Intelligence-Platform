"""API tests: /api/v1/products/{id}/reviews - submission and the aggregate rating it maintains.

Regression coverage for a real bug this suite caught: services/reviews.recompute_rating() writes
Product.average_rating/review_count, but no migration had ever actually created those columns until
migrations/versions/0009_product_rating_columns.py - every review submission would have 500'd against a
real database. embed_documents (Gemini) is not mocked here: services/reviews._embed_review already treats an
embedding failure as best-effort (logs and continues), so with no GEMINI_API_KEY configured in this test
environment, review creation still succeeds exactly as it should in that real degraded-mode scenario.
"""


def test_create_review_requires_authentication(client, make_product) -> None:
    product = make_product()
    response = client.post(f"/api/v1/products/{product.id}/reviews", json={"rating": 5})
    assert response.status_code == 401


def test_create_review_persists_and_returns_it(as_user, make_user, make_product) -> None:
    user = make_user()
    product = make_product()
    response = as_user(user).post(f"/api/v1/products/{product.id}/reviews", json={"rating": 4, "title": "Pretty good", "body": "Works as expected."})
    assert response.status_code == 201
    body = response.json()
    assert body["rating"] == 4
    assert body["title"] == "Pretty good"


def test_create_review_updates_product_average_rating_and_count(as_user, make_user, make_product, db_session) -> None:
    """The exact regression this file exists for: this must not 500 with UndefinedColumn."""
    from app.models import Product

    alice = make_user(email="alice@example.com")
    bob = make_user(email="bob@example.com")
    product = make_product()

    as_user(alice).post(f"/api/v1/products/{product.id}/reviews", json={"rating": 5})
    as_user(bob).post(f"/api/v1/products/{product.id}/reviews", json={"rating": 3})

    db_session.expire_all()
    refreshed = db_session.get(Product, product.id)
    assert refreshed.review_count == 2
    assert float(refreshed.average_rating) == 4.0


def test_cannot_review_the_same_product_twice(as_user, make_user, make_product) -> None:
    user = make_user()
    product = make_product()
    api = as_user(user)
    assert api.post(f"/api/v1/products/{product.id}/reviews", json={"rating": 5}).status_code == 201
    response = api.post(f"/api/v1/products/{product.id}/reviews", json={"rating": 1})
    assert response.status_code == 409


def test_create_review_rejects_out_of_range_rating(as_user, make_user, make_product) -> None:
    api = as_user(make_user())
    product = make_product()
    assert api.post(f"/api/v1/products/{product.id}/reviews", json={"rating": 6}).status_code == 422
    assert api.post(f"/api/v1/products/{product.id}/reviews", json={"rating": 0}).status_code == 422


def test_create_review_for_nonexistent_product_returns_404(as_user, make_user) -> None:
    api = as_user(make_user())
    response = api.post("/api/v1/products/00000000-0000-0000-0000-000000000000/reviews", json={"rating": 5})
    assert response.status_code == 404


def test_review_summary_with_no_reviews_returns_404(client, make_product) -> None:
    product = make_product()
    response = client.get(f"/api/v1/products/{product.id}/reviews/summary")
    assert response.status_code == 404


def test_review_summary_without_an_llm_key_fails_as_service_unavailable_not_a_crash(as_user, make_user, make_product) -> None:
    """Honest, unmocked behavior in this environment: no GEMINI_API_KEY configured, so the summarizer's
    own create_message() raises ServiceUnavailableError - which must surface as a clean 503, never an
    unhandled 500."""
    user = make_user()
    product = make_product()
    as_user(user).post(f"/api/v1/products/{product.id}/reviews", json={"rating": 5, "body": "Great product overall."})

    response = as_user(user).get(f"/api/v1/products/{product.id}/reviews/summary")
    assert response.status_code == 503


def test_create_review_response_includes_trust_fields(as_user, make_user, make_product) -> None:
    from unittest.mock import patch
    user = make_user()
    product = make_product()
    with patch("app.services.reviews.score_texts", return_value=[0.9]):
        response = as_user(user).post(f"/api/v1/products/{product.id}/reviews", json={"rating": 5, "body": "Amazing!!!"})
    body = response.json()
    assert body["trust_score"] == 0.9
    assert body["trust_tier"] == "likely_fake"


def test_list_reviews_returns_visible_reviews_for_the_product(as_user, make_user, make_product) -> None:
    from unittest.mock import patch
    product = make_product()
    with patch("app.services.reviews.score_texts", return_value=[0.1]):
        as_user(make_user()).post(f"/api/v1/products/{product.id}/reviews", json={"rating": 5, "body": "Solid."})
    response = as_user(make_user()).get(f"/api/v1/products/{product.id}/reviews")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_reviews_for_a_product_with_no_reviews_returns_empty_list(client, make_product) -> None:
    product = make_product()
    assert client.get(f"/api/v1/products/{product.id}/reviews").json() == []
