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
            {"retailer": "Amazon", "price": 24990, "currency": "INR", "url": "https://amazon.in/dp/wh1000xm5"},
            {"retailer": "Flipkart", "price": 23499, "currency": "INR", "url": "https://flipkart.com/wh1000xm5/p/itm123"},
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
            {"retailer": "Amazon", "price": 25990, "currency": "INR", "url": "https://amazon.in/dp/a"},
            {"retailer": "Amazon", "price": 24990, "currency": "INR", "url": "https://amazon.in/dp/b"},
        ]
    }
    with patch("app.services.price_comparison.search_web", return_value=_fake_results()), \
         patch("app.services.price_comparison.create_message", return_value=MagicMock(stop_reason="end_turn", content=[MagicMock(text=json.dumps(extraction_payload))])):
        response = client.post("/api/v1/products/compare-prices", json={"product_name": "Sony WH-1000XM5"})

    assert response.status_code == 200
    body = response.json()
    assert len(body["listings"]) == 1
    assert body["listings"][0]["price"] == 24990


def test_compare_prices_retailer_label_comes_from_the_url_not_the_llm_field() -> None:
    """Confirmed live: a news article can get mislabelled by the LLM as "Flipkart" (since it mentions a
    Flipkart price) while its own url is the article itself - not a page a shopper can buy from. The
    displayed retailer must always match where the link actually goes, regardless of what the model said."""
    from app.services.price_comparison import compare_prices

    extraction_payload = {"listings": [{"retailer": "Flipkart", "price": 11799, "currency": "INR", "url": "https://www.croma.com/some-tablet/p/123"}]}
    with patch("app.services.price_comparison.search_web", return_value=_fake_results()), \
         patch("app.services.price_comparison.create_message", return_value=MagicMock(stop_reason="end_turn", content=[MagicMock(text=json.dumps(extraction_payload))])):
        listings = compare_prices("Some Tablet")

    assert listings[0].retailer == "Croma"


def test_compare_prices_with_no_web_results_returns_empty_listings(client) -> None:
    with patch("app.services.price_comparison.search_web", return_value=[]):
        response = client.post("/api/v1/products/compare-prices", json={"product_name": "a completely obscure product"})

    assert response.status_code == 200
    assert response.json()["listings"] == []


def test_compare_prices_searches_major_retailer_domains_first() -> None:
    """Confirmed live: without biasing toward the major retailers, an unrestricted search could rank a
    small/unfamiliar site above (or entirely miss) Flipkart/Amazon/Meesho for a query those retailers
    clearly do stock - both undermining the "prefer major retailers" prompt instruction (nothing to prefer
    if they're not even in the candidate pool) and risking a stale/wrong price being shown as the best deal."""
    from app.services.price_comparison import compare_prices
    from app.services.web_product_search import INDIAN_RETAIL_DOMAINS

    with patch("app.services.price_comparison.search_web", return_value=_fake_results()) as mock_search, \
         patch("app.services.price_comparison.create_message", return_value=MagicMock(stop_reason="end_turn", content=[MagicMock(text=json.dumps({"listings": []}))])):
        compare_prices("Sony WH-1000XM5")

    mock_search.assert_called_once()
    assert mock_search.call_args.kwargs["include_domains"] == INDIAN_RETAIL_DOMAINS


def test_compare_prices_rejects_category_pages_even_if_the_model_picks_one() -> None:
    """Confirmed live: asked for "red saree", the model chose Myntra's category page
    (myntra.com/red-saree) over a genuine single-product Flipkart listing that was right there in the same
    search results - the "reject category pages" prompt instruction alone isn't reliably followed. Each
    major retailer's real single-product urls have a structural marker a category page never has (Flipkart/
    Meesho/Croma/Shopsy: "/p/", Amazon: "/dp/", Myntra: a numeric id + "/buy") - a listing that doesn't match
    is dropped regardless of what the model returned."""
    from app.services.price_comparison import compare_prices

    extraction_payload = {
        "listings": [
            {"retailer": "Myntra", "price": 440, "currency": "INR", "url": "https://www.myntra.com/red-saree"},
            {"retailer": "Flipkart", "price": 599, "currency": "INR", "url": "https://www.flipkart.com/red-saree-striped-daily-wear-cotton-silk/p/itm2fb3600ad222f"},
            {"retailer": "Myntra", "price": 899, "currency": "INR", "url": "https://www.myntra.com/sarees/mitera/mitera-red-embellished-saree/26199116/buy"},
        ]
    }
    with patch("app.services.price_comparison.search_web", return_value=_fake_results()), \
         patch("app.services.price_comparison.create_message", return_value=MagicMock(stop_reason="end_turn", content=[MagicMock(text=json.dumps(extraction_payload))])):
        listings = compare_prices("red saree")

    urls = [listing.url for listing in listings]
    assert "https://www.myntra.com/red-saree" not in urls
    assert "https://www.flipkart.com/red-saree-striped-daily-wear-cotton-silk/p/itm2fb3600ad222f" in urls
    assert "https://www.myntra.com/sarees/mitera/mitera-red-embellished-saree/26199116/buy" in urls


def test_compare_prices_falls_back_to_unrestricted_search_when_major_retailers_have_nothing() -> None:
    from app.services.price_comparison import compare_prices
    from app.services.web_product_search import INDIAN_RETAIL_DOMAINS

    with patch("app.services.price_comparison.search_web", side_effect=[[], _fake_results()]) as mock_search, \
         patch("app.services.price_comparison.create_message", return_value=MagicMock(stop_reason="end_turn", content=[MagicMock(text=json.dumps({"listings": []}))])):
        compare_prices("A niche product no major retailer stocks")

    assert mock_search.call_count == 2
    assert mock_search.call_args_list[0].kwargs["include_domains"] == INDIAN_RETAIL_DOMAINS
    assert "include_domains" not in mock_search.call_args_list[1].kwargs
