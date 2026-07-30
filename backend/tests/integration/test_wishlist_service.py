"""Integration tests: services/wishlist.py against a real Postgres database."""
import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.schemas.wishlist import AddWishlistItemRequest, CreateWishlistRequest
from app.services import wishlist


def test_create_wishlist_persists_and_defaults_name(db_session, make_user) -> None:
    user = make_user()
    created = wishlist.create_wishlist(db_session, user, CreateWishlistRequest())
    assert created.id is not None
    assert created.name == "My Wishlist"
    assert created.user_id == user.id


def test_list_wishlists_only_returns_the_current_users_own(db_session, make_user) -> None:
    owner = make_user(email="owner@example.com")
    other = make_user(email="other@example.com")
    wishlist.create_wishlist(db_session, owner, CreateWishlistRequest(name="Owner's List"))
    wishlist.create_wishlist(db_session, other, CreateWishlistRequest(name="Other's List"))

    owner_lists = wishlist.list_wishlists(db_session, owner)
    assert len(owner_lists) == 1
    assert owner_lists[0].name == "Owner's List"


def test_add_item_persists_and_resolves_product(db_session, make_user, make_product) -> None:
    user = make_user()
    product = make_product(title="Wireless Headphones")
    my_list = wishlist.create_wishlist(db_session, user, CreateWishlistRequest())

    item = wishlist.add_item(db_session, user, my_list.id, AddWishlistItemRequest(product_id=product.id))
    assert item.product_id == product.id

    [refreshed] = wishlist.list_wishlists(db_session, user)
    assert refreshed.items[0].product.title == "Wireless Headphones"


def test_add_same_product_twice_raises_conflict(db_session, make_user, make_product) -> None:
    user = make_user()
    product = make_product()
    my_list = wishlist.create_wishlist(db_session, user, CreateWishlistRequest())
    wishlist.add_item(db_session, user, my_list.id, AddWishlistItemRequest(product_id=product.id))
    with pytest.raises(ConflictError):
        wishlist.add_item(db_session, user, my_list.id, AddWishlistItemRequest(product_id=product.id))


def test_add_nonexistent_product_raises_not_found(db_session, make_user) -> None:
    user = make_user()
    my_list = wishlist.create_wishlist(db_session, user, CreateWishlistRequest())
    with pytest.raises(NotFoundError):
        wishlist.add_item(db_session, user, my_list.id, AddWishlistItemRequest(product_id="00000000-0000-0000-0000-000000000000"))


def test_add_item_to_someone_elses_wishlist_raises_not_found(db_session, make_user, make_product) -> None:
    """Ownership check: wishlist_id must belong to the acting user, not just exist."""
    owner = make_user(email="owner@example.com")
    attacker = make_user(email="attacker@example.com")
    product = make_product()
    owners_list = wishlist.create_wishlist(db_session, owner, CreateWishlistRequest())

    with pytest.raises(NotFoundError):
        wishlist.add_item(db_session, attacker, owners_list.id, AddWishlistItemRequest(product_id=product.id))


def test_remove_item_deletes_it(db_session, make_user, make_product) -> None:
    user = make_user()
    product = make_product()
    my_list = wishlist.create_wishlist(db_session, user, CreateWishlistRequest())
    item = wishlist.add_item(db_session, user, my_list.id, AddWishlistItemRequest(product_id=product.id))

    wishlist.remove_item(db_session, user, my_list.id, item.id)

    [refreshed] = wishlist.list_wishlists(db_session, user)
    assert refreshed.items == []


def test_remove_someone_elses_item_raises_not_found(db_session, make_user, make_product) -> None:
    """The exact IDOR this ownership check exists to prevent: attacker guesses/knows a valid item_id and
    wishlist_id combination that belongs to a different user."""
    owner = make_user(email="owner@example.com")
    attacker = make_user(email="attacker@example.com")
    product = make_product()
    owners_list = wishlist.create_wishlist(db_session, owner, CreateWishlistRequest())
    item = wishlist.add_item(db_session, owner, owners_list.id, AddWishlistItemRequest(product_id=product.id))

    with pytest.raises(NotFoundError):
        wishlist.remove_item(db_session, attacker, owners_list.id, item.id)
