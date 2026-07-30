from uuid import UUID
from pydantic import BaseModel, Field
from app.schemas.catalog import ProductResponse


class CreateWishlistRequest(BaseModel):
    name: str = Field(default="My Wishlist", min_length=1, max_length=80)


class AddWishlistItemRequest(BaseModel):
    product_id: UUID
    target_price_minor: int | None = Field(default=None, ge=0)


class WishlistItemResponse(BaseModel):
    id: UUID
    product: ProductResponse
    target_price_minor: int | None


class WishlistResponse(BaseModel):
    id: UUID
    name: str
    items: list[WishlistItemResponse]
