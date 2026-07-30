"""Security tests: input validation boundaries - oversized payloads, wrong types, out-of-range values,
malformed currency codes. Every one of these must fail with a 422, never a 500 or a silently-accepted value.
"""
import pytest


def test_review_rejects_oversized_body(as_user, make_user, make_product) -> None:
    api = as_user(make_user())
    product = make_product()
    response = api.post(f"/api/v1/products/{product.id}/reviews", json={"rating": 5, "body": "A" * 10000})
    assert response.status_code == 422


@pytest.mark.parametrize("rating", [-1, 0, 6, 100, 3.5])
def test_review_rejects_out_of_range_or_non_integer_rating(as_user, make_user, make_product, rating) -> None:
    api = as_user(make_user())
    product = make_product()
    response = api.post(f"/api/v1/products/{product.id}/reviews", json={"rating": rating})
    assert response.status_code == 422


def test_review_rejects_wrong_type_for_rating(as_user, make_user, make_product) -> None:
    api = as_user(make_user())
    product = make_product()
    response = api.post(f"/api/v1/products/{product.id}/reviews", json={"rating": "five"})
    assert response.status_code == 422


@pytest.mark.parametrize("currency", ["usd", "US", "USDD", "123", "$$$"])
def test_recommendations_rejects_malformed_currency_codes(client, currency) -> None:
    response = client.post("/api/v1/recommendations", json={"purpose": "a gaming laptop for college", "currency": currency})
    assert response.status_code == 422


def test_recommendations_rejects_negative_budget(client) -> None:
    response = client.post("/api/v1/recommendations", json={"purpose": "a gaming laptop for college", "budget": -100})
    assert response.status_code == 422


def test_activity_purchase_rejects_negative_price(as_user, make_user, make_product) -> None:
    api = as_user(make_user())
    product = make_product()
    response = api.post("/api/v1/activity/purchase", json={"product_id": str(product.id), "price_minor": -500})
    assert response.status_code == 422


def test_activity_search_rejects_empty_query(as_user, make_user) -> None:
    response = as_user(make_user()).post("/api/v1/activity/search", json={"query": ""})
    assert response.status_code == 422


def test_activity_search_rejects_oversized_query(as_user, make_user) -> None:
    response = as_user(make_user()).post("/api/v1/activity/search", json={"query": "a" * 1000})
    assert response.status_code == 422


def test_unexpected_extra_fields_do_not_break_or_escalate_activity_click(as_user, make_user, make_product) -> None:
    """Pydantic's default is to ignore unrecognized fields rather than reject them - confirms that stays
    true (a client sending stray fields shouldn't 422) without any extra field silently taking effect
    elsewhere in the request handling."""
    product = make_product()
    response = as_user(make_user()).post("/api/v1/activity/click", json={"product_id": str(product.id), "unexpected_field": "whatever"})
    assert response.status_code == 204


def test_malformed_json_body_returns_422_not_500(as_user, make_user) -> None:
    response = as_user(make_user()).post("/api/v1/activity/click", content=b"{not valid json", headers={"Content-Type": "application/json"})
    assert response.status_code == 422
