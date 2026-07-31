"""API tests: /api/v1/recommendations (explicit LLM engine, mocked) and /recommendations/personalized
(embeddings-only engine, real pgvector search, only the search-logging embed call mocked)."""
from unittest.mock import patch


def test_explicit_recommendations_ranks_web_listings_with_best_pick_and_reviews(client) -> None:
    """The engine sources every recommendation live from the web, ranked best-fit-first by the LLM's own
    ordering (not just cheapest first) - and only the #1 ranked listing gets real reviews attached."""
    from app.services.web_product_search import ReviewSnippet, WebProductListing

    best = WebProductListing(title="Sony WH-1000XM5", brand="Sony", retailer="Amazon.in", price=26990.0, currency="INR", image_url="https://example.com/sony.jpg", url="https://amazon.in/sony-wh1000xm5", reason="Class-leading noise cancellation within budget.")
    second = WebProductListing(title="Bose QuietComfort 45", brand="Bose", retailer="Flipkart", price=24990.0, currency="INR", image_url=None, url="https://flipkart.com/bose-qc45", reason="Cheaper alternative with strong ANC.")
    review = ReviewSnippet(source="GSMArena", quote="Excellent noise cancellation for the price.", url="https://gsmarena.com/sony-wh1000xm5-review")

    with patch("app.services.recommendations.search_web_products", return_value=[best, second]), \
         patch("app.services.recommendations.search_reviews", return_value=[review]) as mock_reviews:
        response = client.post("/api/v1/recommendations", json={"purpose": "noise cancelling headphones for my commute", "budget": 30000})

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["items"][0]["title"] == "Sony WH-1000XM5"
    assert body["items"][0]["rank"] == 1
    assert body["items"][0]["is_best_pick"] is True
    assert body["items"][0]["reviews"] == [{"source": "GSMArena", "quote": "Excellent noise cancellation for the price.", "url": "https://gsmarena.com/sony-wh1000xm5-review"}]
    assert body["items"][1]["rank"] == 2
    assert body["items"][1]["is_best_pick"] is False
    assert body["items"][1]["reviews"] == []
    mock_reviews.assert_called_once_with("Sony WH-1000XM5", "Sony")


def test_explicit_recommendations_with_no_web_results_is_404(client) -> None:
    with patch("app.services.recommendations.search_web_products", return_value=[]):
        response = client.post("/api/v1/recommendations", json={"purpose": "a completely obscure product"})

    assert response.status_code == 404


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
