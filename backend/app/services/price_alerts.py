"""Evaluates a price drop against every shopper tracking that product and sends WhatsApp alerts to the
ones who should hear about it. Called by services/pricing.py whenever a real price observation lands."""
import logging
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from app.core.exceptions import ServiceUnavailableError
from app.models import Product, ProductOffer, User, UserPreferences, WhatsappMessage, WhatsappMessageStatus, Wishlist, WishlistItem
from app.services import whatsapp

logger = logging.getLogger(__name__)


def evaluate_and_notify(db: Session, offer: ProductOffer, new_price_minor: int) -> list[WhatsappMessage]:
    """Alert every wishlist item tracking this product whose target price was just reached, and who has
    opted into (verified) WhatsApp alerts. Skips items already alerted at this price or lower - a failed
    send still marks the item alerted, so one bad phone number can't retry-spam every subsequent price tick.
    """
    matches = db.execute(
        select(WishlistItem, User, UserPreferences)
        .join(Wishlist, Wishlist.id == WishlistItem.wishlist_id)
        .join(User, User.id == Wishlist.user_id)
        .join(UserPreferences, UserPreferences.user_id == User.id)
        .where(
            WishlistItem.product_id == offer.product_id,
            WishlistItem.target_price_minor.is_not(None),
            WishlistItem.target_price_minor >= new_price_minor,
            or_(WishlistItem.last_alerted_price_minor.is_(None), WishlistItem.last_alerted_price_minor > new_price_minor),
            UserPreferences.notify_whatsapp.is_(True),
            UserPreferences.phone_verified.is_(True),
            UserPreferences.phone_number.is_not(None),
        )
    ).all()
    if not matches:
        return []

    product = db.get(Product, offer.product_id)
    sent: list[WhatsappMessage] = []
    for item, user, prefs in matches:
        try:
            wa_message_id = whatsapp.send_price_drop_alert(
                phone_e164=prefs.phone_number,
                product_title=product.title,
                price_minor=new_price_minor,
                currency=offer.currency,
                listing_url=offer.listing_url,
            )
            message = WhatsappMessage(user_id=user.id, wishlist_item_id=item.id, price_minor=new_price_minor, wa_message_id=wa_message_id, status=WhatsappMessageStatus.SENT)
        except ServiceUnavailableError as error:
            logger.warning("price_alert_send_failed wishlist_item_id=%s error=%s", item.id, error)
            message = WhatsappMessage(user_id=user.id, wishlist_item_id=item.id, price_minor=new_price_minor, status=WhatsappMessageStatus.FAILED, error_detail=str(error))
        item.last_alerted_price_minor = new_price_minor
        db.add(message)
        sent.append(message)

    db.commit()
    for message in sent:
        db.refresh(message)
    return sent
