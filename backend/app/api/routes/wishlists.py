from uuid import UUID
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, rate_limit
from app.db.session import get_db
from app.models import User
from app.schemas.wishlist import AddWishlistItemRequest, CreateWishlistRequest, WishlistItemResponse, WishlistResponse
from app.services import wishlist

router = APIRouter(prefix="/wishlists", tags=["wishlists"])


@router.get("", response_model=list[WishlistResponse], dependencies=[Depends(rate_limit(60, 60))])
def list_my_wishlists(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List the current user's private wishlists and their resolved products."""
    return wishlist.list_wishlists(db, user)


@router.post("", response_model=WishlistResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit(20, 60))])
def create_my_wishlist(payload: CreateWishlistRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a private wishlist for the current user."""
    return wishlist.create_wishlist(db, user, payload)


@router.post("/{wishlist_id}/items", response_model=WishlistItemResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit(60, 60))])
def add_wishlist_item(wishlist_id: UUID, payload: AddWishlistItemRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Track a catalog product at an optional user-defined target price."""
    return wishlist.add_item(db, user, wishlist_id, payload)


@router.delete("/{wishlist_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(rate_limit(60, 60))])
def delete_wishlist_item(wishlist_id: UUID, item_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    """Remove one owned wishlist item without exposing cross-user resources."""
    wishlist.remove_item(db, user, wishlist_id, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
