"""API tests: /api/v1/wishlists - CRUD plus cross-user isolation (IDOR checks) over real HTTP + DB."""


def test_requires_authentication(client) -> None:
    assert client.get("/api/v1/wishlists").status_code == 401
    assert client.post("/api/v1/wishlists", json={}).status_code == 401


def test_create_and_list_wishlist(as_user, make_user) -> None:
    user = make_user()
    api = as_user(user)

    created = api.post("/api/v1/wishlists", json={"name": "Birthday Ideas"})
    assert created.status_code == 201
    assert created.json()["name"] == "Birthday Ideas"

    listed = api.get("/api/v1/wishlists")
    assert listed.status_code == 200
    assert [w["name"] for w in listed.json()] == ["Birthday Ideas"]


def test_add_item_and_see_it_in_the_list(as_user, make_user, make_product) -> None:
    user = make_user()
    product = make_product(title="Wireless Headphones")
    api = as_user(user)
    wishlist_id = api.post("/api/v1/wishlists", json={}).json()["id"]

    added = api.post(f"/api/v1/wishlists/{wishlist_id}/items", json={"product_id": str(product.id)})
    assert added.status_code == 201

    listed = api.get("/api/v1/wishlists").json()
    assert listed[0]["items"][0]["product"]["title"] == "Wireless Headphones"


def test_cannot_add_item_to_another_users_wishlist(as_user, make_user, make_product) -> None:
    owner = make_user(email="owner@example.com")
    attacker = make_user(email="attacker@example.com")
    product = make_product()

    owners_wishlist_id = as_user(owner).post("/api/v1/wishlists", json={}).json()["id"]
    response = as_user(attacker).post(f"/api/v1/wishlists/{owners_wishlist_id}/items", json={"product_id": str(product.id)})
    assert response.status_code == 404


def test_cannot_delete_another_users_item(as_user, make_user, make_product) -> None:
    owner = make_user(email="owner2@example.com")
    attacker = make_user(email="attacker2@example.com")
    product = make_product()

    owner_api = as_user(owner)
    wishlist_id = owner_api.post("/api/v1/wishlists", json={}).json()["id"]
    item_id = owner_api.post(f"/api/v1/wishlists/{wishlist_id}/items", json={"product_id": str(product.id)}).json()["id"]

    response = as_user(attacker).delete(f"/api/v1/wishlists/{wishlist_id}/items/{item_id}")
    assert response.status_code == 404


def test_users_only_see_their_own_wishlists(as_user, make_user) -> None:
    alice = make_user(email="alice@example.com")
    bob = make_user(email="bob@example.com")
    as_user(alice).post("/api/v1/wishlists", json={"name": "Alice's List"})
    as_user(bob).post("/api/v1/wishlists", json={"name": "Bob's List"})

    alice_lists = as_user(alice).get("/api/v1/wishlists").json()
    assert [w["name"] for w in alice_lists] == ["Alice's List"]
