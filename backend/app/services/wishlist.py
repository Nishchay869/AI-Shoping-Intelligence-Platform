"""Wishlist ownership and product membership rules."""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Product, User, Wishlist, WishlistItem
from app.schemas.wishlist import AddWishlistItemRequest, CreateWishlistRequest


def list_wishlists(db: Session, user: User) -> list[Wishlist]:
    """Return only wishlists belonging to the authenticated user, including products."""
    return list(db.scalars(select(Wishlist).where(Wishlist.user_id == user.id).options(joinedload(Wishlist.items).joinedload(WishlistItem.product))).unique())


def create_wishlist(db: Session, user: User, payload: CreateWishlistRequest) -> Wishlist:
    """Create a private wishlist owned by the current user."""
    wishlist = Wishlist(user_id=user.id, name=payload.name.strip())
    db.add(wishlist); db.commit(); db.refresh(wishlist)
    return wishlist


def add_item(db: Session, user: User, wishlist_id: UUID, payload: AddWishlistItemRequest) -> WishlistItem:
    """Add a real catalog product to a wishlist after verifying resource ownership."""
    wishlist = db.scalar(select(Wishlist).where(Wishlist.id == wishlist_id, Wishlist.user_id == user.id))
    if not wishlist: raise NotFoundError("Wishlist not found")
    if not db.get(Product, payload.product_id): raise NotFoundError("Product not found")
    if db.scalar(select(WishlistItem).where(WishlistItem.wishlist_id == wishlist_id, WishlistItem.product_id == payload.product_id)):
        raise ConflictError("Product is already in this wishlist")
    item = WishlistItem(wishlist_id=wishlist_id, product_id=payload.product_id, target_price_minor=payload.target_price_minor)
    db.add(item); db.commit(); db.refresh(item)
    return item


def remove_item(db: Session, user: User, wishlist_id: UUID, item_id: UUID) -> None:
    """Delete one item only when its parent wishlist belongs to the current user."""
    item = db.scalar(select(WishlistItem).join(Wishlist).where(WishlistItem.id == item_id, Wishlist.id == wishlist_id, Wishlist.user_id == user.id))
    if not item: raise NotFoundError("Wishlist item not found")
    db.delete(item); db.commit()
