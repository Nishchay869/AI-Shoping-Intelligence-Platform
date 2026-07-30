"""API tests: /api/v1/recommendations (explicit LLM engine, mocked) and /recommendations/personalized
(embeddings-only engine, real pgvector search, only the search-logging embed call mocked)."""
import json
from unittest.mock import MagicMock, patch

import pytest


def test_explicit_recommendations_end_to_end_with_mocked_llm_and_embeddings(client, make_product) -> None:
    product = make_product(title="Noise Cancelling Headphones", price_minor=15000, with_embedding=True)

    understanding_payload = {"ideal_product_description": "noise cancelling headphones for commuting", "max_price_minor": 20000, "brand": None}
    ranking_payload = {"picks": [{"product_id": str(product.id), "reason": "Matches the stated budget and use case."}]}

    with patch("app.services.recommendations.create_message", side_effect=[
             MagicMock(stop_reason="end_turn", content=[MagicMock(text=json.dumps(understanding_payload))]),
             MagicMock(stop_reason="end_turn", content=[MagicMock(text=json.dumps(ranking_payload))]),
         ]), \
         patch("app.services.recommendations.embed_query", return_value=[0.1] * 768):
        response = client.post("/api/v1/recommendations", json={"purpose": "noise cancelling headphones for my commute", "budget": 200, "currency": "USD"})

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["product"]["title"] == "Noise Cancelling Headphones"


def test_explicit_recommendations_rejects_bad_currency(client) -> None:
    response = client.post("/api/v1/recommendations", json={"purpose": "a gaming laptop", "currency": "usd"})
    assert response.status_code == 422


def test_explicit_recommendations_rejects_too_short_purpose(client) -> None:
    response = client.post("/api/v1/recommendations", json={"purpose": "ab"})
    assert response.status_code == 422


def test_personalized_recommendations_requires_authentication(client) -> None:
    assert client.get("/api/v1/recommendations/personalized").status_code == 401


def test_personalized_recommendations_with_no_activity_returns_404(as_user, make_user) -> None:
    response = as_user(make_user()).get("/api/v1/recommendations/personalized")
    assert response.status_code == 404


def test_personalized_recommendations_end_to_end_real_pgvector(as_user, make_user, make_product) -> None:
    """Real DB, real pgvector cosine search, real vector math - only the one Gemini embedding call inside
    log_search is mocked (no live API key in this environment)."""
    user = make_user()
    api = as_user(user)

    base = [0.5] * 768
    purchased = make_product(title="Wireless Headphones", embedding=base)
    similar = make_product(title="Wireless Earbuds", embedding=[x + 0.001 for x in base])

    with patch("app.services.personalization.embed_query", return_value=[0.4] * 768):
        assert api.post("/api/v1/activity/search", json={"query": "wireless headphones"}).status_code == 204
    assert api.post("/api/v1/activity/purchase", json={"product_id": str(purchased.id)}).status_code == 204

    response = api.get("/api/v1/recommendations/personalized")
    assert response.status_code == 200
    body = response.json()
    titles = [item["product"]["title"] for item in body["items"]]
    assert similar.title in titles
    assert purchased.title not in titles
    assert body["signal_counts"] == {"purchase": 1, "wishlist": 0, "search": 1, "click": 0}


def test_activity_click_rejects_nonexistent_product(as_user, make_user) -> None:
    response = as_user(make_user()).post("/api/v1/activity/click", json={"product_id": "00000000-0000-0000-0000-000000000000"})
    assert response.status_code == 404


def test_activity_purchase_defaults_price_to_products_current_price(as_user, make_user, make_product, db_session) -> None:
    from app.models import Purchase

    user = make_user()
    product = make_product(price_minor=4999, currency="USD")
    response = as_user(user).post("/api/v1/activity/purchase", json={"product_id": str(product.id)})
    assert response.status_code == 204

    purchase = db_session.query(Purchase).filter_by(user_id=user.id, product_id=product.id).one()
    assert purchase.price_minor == 4999
    assert purchase.currency == "USD"
