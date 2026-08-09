"""Alerts shoppers via WhatsApp when a scanned receipt's warranty is about to expire.

No scheduler exists anywhere in this backend - see scripts/send_warranty_alerts.py for the runnable entry
point and how to actually schedule it. This module only owns the detection + sending logic.
"""
import logging
from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.exceptions import ServiceUnavailableError
from app.models import Receipt, User, UserPreferences
from app.services import whatsapp

logger = logging.getLogger(__name__)


def send_expiring_warranty_alerts(db: Session, within_days: int = 7) -> list[Receipt]:
    """Alert every shopper whose receipt's warranty expires within the window and who has opted into
    (verified) WhatsApp alerts. Skips receipts already alerted, and ones with no computed expiry - a
    failed send still marks the receipt alerted, so one bad phone number can't retry-spam forever.
    """
    today = date.today()
    threshold = today + timedelta(days=within_days)
    matches = db.execute(
        select(Receipt, User, UserPreferences)
        .join(User, User.id == Receipt.user_id)
        .join(UserPreferences, UserPreferences.user_id == User.id)
        .where(
            Receipt.warranty_expires_at.is_not(None),
            Receipt.warranty_expires_at >= today,
            Receipt.warranty_expires_at <= threshold,
            Receipt.warranty_alert_sent.is_(False),
            UserPreferences.notify_whatsapp.is_(True),
            UserPreferences.phone_verified.is_(True),
            UserPreferences.phone_number.is_not(None),
        )
    ).all()
    if not matches:
        return []

    notified: list[Receipt] = []
    for receipt, _user, prefs in matches:
        try:
            whatsapp.send_warranty_expiring_alert(
                phone_e164=prefs.phone_number,
                product_or_store_name=receipt.store_name or "your purchase",
                expires_on=receipt.warranty_expires_at,
                days_remaining=(receipt.warranty_expires_at - today).days,
            )
        except ServiceUnavailableError as error:
            logger.warning("warranty_alert_send_failed receipt_id=%s error=%s", receipt.id, error)
        receipt.warranty_alert_sent = True
        notified.append(receipt)

    db.commit()
    return notified
