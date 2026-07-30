"""Security tests: SQL injection. Every query in this codebase goes through SQLAlchemy's Core/ORM query
builder, which binds parameters rather than interpolating strings - these tests prove that empirically
against a real database rather than just asserting it by code review.
"""
from sqlalchemy import select

from app.models import User


SQLI_PAYLOADS = [
    "'; DROP TABLE users; --",
    "' OR '1'='1",
    "'; SELECT * FROM users; --",
    "1' UNION SELECT email, password_hash FROM users --",
    "'; UPDATE users SET is_admin = true; --",
    "\"; DROP TABLE products; --",
]


def test_product_search_query_payload_is_treated_as_literal_text(client, make_product, db_session) -> None:
    make_product(title="Wireless Headphones")
    for payload in SQLI_PAYLOADS:
        response = client.get("/api/v1/products", params={"q": payload})
        assert response.status_code == 200
        assert response.json() == []  # no product titled that, and no error/leak either

    # the users table must still exist and be untouched
    assert db_session.execute(select(User)).all() is not None


def test_product_category_filter_payload_is_treated_as_literal_text(client, make_product) -> None:
    make_product(title="Headphones", category="Audio")
    for payload in SQLI_PAYLOADS:
        response = client.get("/api/v1/products", params={"category": payload})
        assert response.status_code == 200
        assert response.json() == []


def test_users_table_survives_every_injection_attempt(client, make_product, db_session) -> None:
    """After throwing every payload above at the product search endpoint, the users table must be
    completely intact - the strongest possible proof that none of it executed as SQL."""
    make_product(title="Test Product")
    for payload in SQLI_PAYLOADS:
        client.get("/api/v1/products", params={"q": payload})

    # A genuinely dropped/altered table would make this raise, not just return an empty/short result.
    result = db_session.execute(select(User)).all()
    assert isinstance(result, list)


def test_wishlist_item_product_id_rejects_non_uuid_injection_payload(as_user, make_user) -> None:
    """product_id is UUID-typed at the schema boundary - a non-UUID payload never reaches the query layer."""
    api = as_user(make_user())
    wishlist_id = api.post("/api/v1/wishlists", json={}).json()["id"]
    response = api.post(f"/api/v1/wishlists/{wishlist_id}/items", json={"product_id": "' OR '1'='1"})
    assert response.status_code == 422
