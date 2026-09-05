"""Real notification feed: price-drop alerts already sent to the user over WhatsApp (whatsapp_messages),
paired with the product they were about, newest first. There's no separate in-app notification store -
this is a read view over the same delivery log that also drives WhatsApp Cloud API sends, so it can never
drift from what the user actually received."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Product, User, WhatsappMessage, WhatsappMessageStatus, WishlistItem
from app.schemas.notifications import NotificationResponse


def _format_price(price_minor: int, currency: str) -> str:
    return f"{currency} {price_minor / 100:,.2f}"


def list_notifications(db: Session, user: User, limit: int = 20) -> list[NotificationResponse]:
    """Most recent price-drop alerts sent to this user, each paired with the product it was about."""
    rows = db.execute(
        select(WhatsappMessage, Product.title, Product.currency)
        .join(WishlistItem, WhatsappMessage.wishlist_item_id == WishlistItem.id)
        .join(Product, WishlistItem.product_id == Product.id)
        .where(WhatsappMessage.user_id == user.id)
        .order_by(WhatsappMessage.created_at.desc())
        .limit(limit)
    ).all()
    return [
        NotificationResponse(
            id=message.id,
            message=f"Price drop: {title} is now {_format_price(message.price_minor, currency)}",
            product_title=title,
            is_read=message.status == WhatsappMessageStatus.READ,
            created_at=message.created_at,
        )
        for message, title, currency in rows
    ]
