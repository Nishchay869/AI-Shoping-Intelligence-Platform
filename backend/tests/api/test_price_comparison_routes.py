"""API tests: /api/v1/products/compare-prices (Tavily web search + Gemini extraction, both mocked)."""
import json
from unittest.mock import MagicMock, patch

from app.infrastructure.web_search import WebResult


def _fake_results() -> list[WebResult]:
    return [
        WebResult(label="W1", title="Sony WH-1000XM5 - Amazon.in", url="https://amazon.in/wh1000xm5", snippet="Buy for ₹24,990"),
        WebResult(label="W2", title="Sony WH-1000XM5 - Flipkart", url="https://flipkart.com/wh1000xm5", snippet="Price ₹23,499"),
        WebResult(label="W3", title="Best noise cancelling headphones 2026 - review blog", url="https://blog.example.com/best-anc", snippet="Our top pick is the Sony WH-1000XM5 for its comfort."),
    ]


def test_compare_prices_returns_listings_sorted_cheapest_first(client) -> None:
    extraction_payload = {
        "listings": [
            {"retailer": "Amazon", "price": 24990, "currency": "INR", "url": "https://amazon.in/wh1000xm5"},
            {"retailer": "Flipkart", "price": 23499, "currency": "INR", "url": "https://flipkart.com/wh1000xm5"},
        ]
    }
    with patch("app.services.price_comparison.search_web", return_value=_fake_results()), \
         patch("app.services.price_comparison.create_message", return_value=MagicMock(stop_reason="end_turn", content=[MagicMock(text=json.dumps(extraction_payload))])):
        response = client.post("/api/v1/products/compare-prices", json={"product_name": "Sony WH-1000XM5"})

    assert response.status_code == 200
    body = response.json()
    assert [listing["retailer"] for listing in body["listings"]] == ["Flipkart", "Amazon"]
    assert body["listings"][0]["price"] == 23499


def test_compare_prices_keeps_only_the_cheapest_listing_per_retailer(client) -> None:
    extraction_payload = {
        "listings": [
            {"retailer": "Amazon", "price": 25990, "currency": "INR", "url": "https://amazon.in/a"},
            {"retailer": "Amazon", "price": 24990, "currency": "INR", "url": "https://amazon.in/b"},
        ]
    }
    with patch("app.services.price_comparison.search_web", return_value=_fake_results()), \
         patch("app.services.price_comparison.create_message", return_value=MagicMock(stop_reason="end_turn", content=[MagicMock(text=json.dumps(extraction_payload))])):
        response = client.post("/api/v1/products/compare-prices", json={"product_name": "Sony WH-1000XM5"})

    assert response.status_code == 200
    body = response.json()
    assert len(body["listings"]) == 1
    assert body["listings"][0]["price"] == 24990


def test_compare_prices_with_no_web_results_returns_empty_listings(client) -> None:
    with patch("app.services.price_comparison.search_web", return_value=[]):
        response = client.post("/api/v1/products/compare-prices", json={"product_name": "a completely obscure product"})

    assert response.status_code == 200
    assert response.json()["listings"] == []
