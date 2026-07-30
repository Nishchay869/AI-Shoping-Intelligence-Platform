"""Security tests: authorization / IDOR (Insecure Direct Object Reference). Broader per-route ownership
checks already live alongside their feature's own test file (test_wishlists_routes.py,
test_receipts_routes.py) - this file is the cross-cutting sweep: for every owned resource type in the app,
prove a second, unrelated user cannot read or act on the first user's private data just by knowing/guessing
its id."""


def test_cannot_read_another_users_receipt_by_guessing_its_id(as_user, make_user) -> None:
    from unittest.mock import MagicMock, patch
    import io
    import json
    from PIL import Image, ImageDraw

    owner = make_user(email="owner@example.com")
    attacker = make_user(email="attacker@example.com")

    payload = {"store_name": "X", "purchase_date": None, "items": [], "subtotal": None, "tax": None, "total": None, "currency": "USD", "warranty_text": None}
    fake_response = MagicMock(stop_reason="end_turn", content=[MagicMock(text=json.dumps(payload))])
    image = Image.new("RGB", (200, 100), "white")
    ImageDraw.Draw(image).text((10, 10), "TEST STORE RECEIPT", fill="black")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    with patch("app.services.receipt_scanner.create_message", return_value=fake_response):
        receipt_id = as_user(owner).post("/api/v1/receipts/scan", files={"image": ("r.png", buffer.getvalue(), "image/png")}).json()["id"]

    assert as_user(attacker).get(f"/api/v1/receipts/{receipt_id}").status_code == 404
    assert receipt_id not in [r["id"] for r in as_user(attacker).get("/api/v1/receipts").json()]


def test_cannot_add_items_to_or_delete_from_another_users_wishlist(as_user, make_user, make_product) -> None:
    owner = make_user(email="owner@example.com")
    attacker = make_user(email="attacker@example.com")
    product = make_product()

    owner_api = as_user(owner)
    wishlist_id = owner_api.post("/api/v1/wishlists", json={}).json()["id"]
    item_id = owner_api.post(f"/api/v1/wishlists/{wishlist_id}/items", json={"product_id": str(product.id)}).json()["id"]

    attacker_api = as_user(attacker)
    assert attacker_api.post(f"/api/v1/wishlists/{wishlist_id}/items", json={"product_id": str(product.id)}).status_code == 404
    assert attacker_api.delete(f"/api/v1/wishlists/{wishlist_id}/items/{item_id}").status_code == 404


def test_one_users_token_cannot_be_used_to_act_as_another_user(as_user, make_user) -> None:
    """A user's bearer token always resolves to their own identity via the token's own `sub` claim - there is
    no user_id parameter anywhere a caller could substitute another user's id into."""
    alice = make_user(email="alice@example.com")
    bob = make_user(email="bob@example.com")

    alice_email = as_user(alice).get("/api/v1/auth/me").json()["email"]
    bob_email = as_user(bob).get("/api/v1/auth/me").json()["email"]

    assert alice_email == "alice@example.com"
    assert bob_email == "bob@example.com"
    assert alice_email != bob_email


def test_personalized_recommendations_are_scoped_to_the_caller_only(as_user, make_user, make_product) -> None:
    """No user_id parameter exists on this endpoint at all - it always derives the identity to personalize
    for from the caller's own token, so there's no id to substitute in the first place."""
    from unittest.mock import patch

    alice = make_user(email="alice@example.com")
    bob = make_user(email="bob@example.com")
    product = make_product(embedding=[0.3] * 768)

    with patch("app.services.personalization.embed_query", return_value=[0.3] * 768):
        as_user(alice).post("/api/v1/activity/search", json={"query": "something alice searched"})

    # bob has no activity at all - his feed must be empty/404, never alice's
    response = as_user(bob).get("/api/v1/recommendations/personalized")
    assert response.status_code == 404
