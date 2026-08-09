"""API tests: /api/v1/products/image-search - catalog matches (real CLIP embedding call mocked) plus live
cross-retailer web listings for the identified product (Tavily search + Gemini extraction mocked)."""
import io
import json
from unittest.mock import MagicMock, patch

from PIL import Image

CLIP_DIM = 512


def _synthetic_photo_png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def test_empty_file_returns_400(client) -> None:
    response = client.post("/api/v1/products/image-search", files={"image": ("empty.png", b"", "image/png")})
    assert response.status_code == 400


def test_non_image_file_returns_422(client) -> None:
    """Real PIL parsing of genuinely non-image bytes (nothing mocked here) - CLIP never runs."""
    response = client.post("/api/v1/products/image-search", files={"image": ("note.txt", b"not an image", "text/plain")})
    assert response.status_code == 422


def test_returns_catalog_matches_by_visual_similarity(client, make_product) -> None:
    base = [0.5] * CLIP_DIM
    matching = make_product(title="Matching Product", image_embedding=base)
    make_product(title="Unrelated Product", image_embedding=[-x for x in base])

    with patch("app.services.image_search.embed_image", return_value=base), \
         patch("app.services.image_search.identify_product_photo", return_value=None):
        response = client.post("/api/v1/products/image-search", files={"image": ("photo.png", _synthetic_photo_png(), "image/png")})

    assert response.status_code == 200
    body = response.json()
    titles = [r["product"]["title"] for r in body["results"]]
    assert titles[0] == matching.title
    assert body["web_listings"] == []
    assert body["identified_as"] is None


def test_includes_live_web_listings_for_the_identified_product(client) -> None:
    fake_listing_payload = {"listings": [{"retailer": "Flipkart", "price": 4999, "currency": "INR", "url": "https://flipkart.com/some-product/p/itm123"}]}
    with patch("app.services.image_search.embed_image", return_value=[0.1] * CLIP_DIM), \
         patch("app.services.image_search.identify_product_photo", return_value="Sony WH-1000XM5 headphones"), \
         patch("app.services.price_comparison.search_web", return_value=[MagicMock(label="W1", title="Flipkart listing", url="https://flipkart.com/some-product/p/itm123", snippet="₹4,999")]), \
         patch("app.services.price_comparison.create_message", return_value=MagicMock(stop_reason="end_turn", content=[MagicMock(text=json.dumps(fake_listing_payload))])):
        response = client.post("/api/v1/products/image-search", files={"image": ("photo.png", _synthetic_photo_png(), "image/png")})

    assert response.status_code == 200
    body = response.json()
    assert body["identified_as"] == "Sony WH-1000XM5 headphones"
    assert body["web_listings"] == [{"retailer": "Flipkart", "price": 4999.0, "currency": "INR", "url": "https://flipkart.com/some-product/p/itm123"}]


def _vector_at_cosine_similarity(dim: int, similarity: float) -> list[float]:
    """A unit vector whose cosine similarity to the [1, 0, 0, ...] axis is exactly `similarity`."""
    return [similarity, (1 - similarity**2) ** 0.5] + [0.0] * (dim - 2)


def test_a_different_product_at_a_realistic_clip_similarity_is_excluded(client, make_product) -> None:
    """Confirmed live: a MacBook photo scored 0.70 cosine similarity against an unrelated iPhone catalog
    entry - CLIP similarity runs much hotter than intuition suggests, so a wrong product must not sneak
    past the threshold just because it's not a literal 0.0. 0.70 here mirrors that exact real reading."""
    base = [1.0] + [0.0] * (CLIP_DIM - 1)
    make_product(title="Unrelated Product", image_embedding=base)
    query = _vector_at_cosine_similarity(CLIP_DIM, 0.70)

    with patch("app.services.image_search.embed_image", return_value=query), \
         patch("app.services.image_search.identify_product_photo", return_value=None):
        response = client.post("/api/v1/products/image-search", files={"image": ("photo.png", _synthetic_photo_png(), "image/png")})

    assert response.json()["results"] == []


def test_a_genuinely_close_visual_match_still_passes(client, make_product) -> None:
    base = [1.0] + [0.0] * (CLIP_DIM - 1)
    matching = make_product(title="Matching Product", image_embedding=base)
    query = _vector_at_cosine_similarity(CLIP_DIM, 0.97)

    with patch("app.services.image_search.embed_image", return_value=query), \
         patch("app.services.image_search.identify_product_photo", return_value=None):
        response = client.post("/api/v1/products/image-search", files={"image": ("photo.png", _synthetic_photo_png(), "image/png")})

    titles = [r["product"]["title"] for r in response.json()["results"]]
    assert titles == [matching.title]


def test_a_failed_web_search_does_not_take_down_the_whole_response(client) -> None:
    """compare_prices() correctly raises on a real LLM failure (rate limit, transient error) so its own
    direct /compare-prices endpoint can show "temporarily unavailable" rather than a misleading "found
    nothing" - but a photo search that already has a real identification must not fail outright just
    because this one extra piece hit that same failure. Confirmed missing live: this endpoint returned a
    hard 503 for the entire request during heavy testing, hiding an identification that had already
    succeeded."""
    from app.core.exceptions import ServiceUnavailableError

    with patch("app.services.image_search.embed_image", return_value=[0.1] * CLIP_DIM), \
         patch("app.services.image_search.identify_product_photo", return_value="Sony WH-1000XM5 headphones"), \
         patch("app.services.image_search.compare_prices", side_effect=ServiceUnavailableError("rate limited")):
        response = client.post("/api/v1/products/image-search", files={"image": ("photo.png", _synthetic_photo_png(), "image/png")})

    assert response.status_code == 200
    body = response.json()
    assert body["identified_as"] == "Sony WH-1000XM5 headphones"
    assert body["web_listings"] == []


def test_unidentifiable_photo_still_returns_catalog_results_gracefully(client, make_product) -> None:
    """identify_product_photo returning None (a genuinely unidentifiable photo, or a failed vision call)
    must never take down the whole response - catalog matches this endpoint could already provide on their
    own are still returned, just with an empty web_listings list."""
    base = [0.5] * CLIP_DIM
    make_product(title="Matching Product", image_embedding=base)

    with patch("app.services.image_search.embed_image", return_value=base), \
         patch("app.services.image_search.identify_product_photo", return_value=None):
        response = client.post("/api/v1/products/image-search", files={"image": ("photo.png", _synthetic_photo_png(), "image/png")})

    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 1
    assert body["web_listings"] == []
