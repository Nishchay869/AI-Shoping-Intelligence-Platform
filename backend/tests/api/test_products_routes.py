"""API tests: /api/v1/products - catalog search, filtering, pagination, and per-product lookup."""


def test_list_products_returns_all_by_default(client, make_product) -> None:
    make_product(title="Wireless Headphones")
    make_product(title="Bluetooth Speaker")
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    titles = [p["title"] for p in response.json()]
    assert "Wireless Headphones" in titles
    assert "Bluetooth Speaker" in titles


def test_list_products_filters_by_title_query(client, make_product) -> None:
    make_product(title="Wireless Headphones")
    make_product(title="Garden Hose")
    response = client.get("/api/v1/products", params={"q": "headphones"})
    assert response.status_code == 200
    titles = [p["title"] for p in response.json()]
    assert titles == ["Wireless Headphones"]


def test_list_products_filter_is_case_insensitive(client, make_product) -> None:
    make_product(title="Wireless Headphones")
    response = client.get("/api/v1/products", params={"q": "WIRELESS"})
    assert len(response.json()) == 1


def test_list_products_filters_by_category(client, make_product) -> None:
    make_product(title="Headphones", category="Audio")
    make_product(title="Desk", category="Furniture")
    response = client.get("/api/v1/products", params={"category": "Audio"})
    titles = [p["title"] for p in response.json()]
    assert titles == ["Headphones"]


def test_list_products_respects_limit(client, make_product) -> None:
    for i in range(5):
        make_product(title=f"Product {i}")
    response = client.get("/api/v1/products", params={"limit": 2})
    assert len(response.json()) == 2


def test_list_products_rejects_out_of_range_limit(client) -> None:
    response = client.get("/api/v1/products", params={"limit": 1000})
    assert response.status_code == 422


def test_get_product_by_id(client, make_product) -> None:
    product = make_product(title="Specific Product")
    response = client.get(f"/api/v1/products/{product.id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Specific Product"


def test_get_nonexistent_product_returns_404(client) -> None:
    response = client.get("/api/v1/products/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_get_product_rejects_malformed_uuid(client) -> None:
    response = client.get("/api/v1/products/not-a-uuid")
    assert response.status_code == 422
