"""Meta WhatsApp Cloud API webhook: verification handshake, delivery-status callbacks, and inbound
STOP opt-outs. Called by Meta's servers, never a signed-in shopper - no get_current_user dependency;
trust comes from the verify-token handshake (GET) and HMAC signature (POST) instead."""
import logging
from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.webhooks import verify_meta_signature
from app.db.session import get_db
from app.models import UserPreferences, WhatsappMessage, WhatsappMessageStatus

router = APIRouter(prefix="/webhooks/whatsapp", tags=["whatsapp-webhook"])
logger = logging.getLogger(__name__)
_KNOWN_STATUSES = {member.value for member in WhatsappMessageStatus}


@router.get("")
def verify_subscription(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
) -> Response:
    """Meta's one-time subscription handshake: echo the challenge back only if the verify token matches."""
    settings = get_settings()
    if hub_mode == "subscribe" and settings.whatsapp_verify_token and hub_verify_token == settings.whatsapp_verify_token:
        return Response(content=hub_challenge, media_type="text/plain")
    return Response(status_code=status.HTTP_403_FORBIDDEN)


@router.post("")
async def receive_webhook_event(request: Request, db: Session = Depends(get_db)) -> Response:
    """Delivery-status callbacks (sent/delivered/read/failed) and inbound messages (STOP opt-out).

    Always acks 200 once the signature is valid - Meta disables webhooks that error or time out on
    well-formed deliveries, so malformed individual entries are logged and skipped, never raised.
    """
    raw_body = await request.body()
    settings = get_settings()
    if not verify_meta_signature(raw_body, request.headers.get("x-hub-signature-256"), settings.whatsapp_app_secret):
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    try:
        payload = await request.json()
    except ValueError:
        logger.warning("whatsapp_webhook_invalid_json")
        return Response(status_code=status.HTTP_200_OK)

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for status_update in value.get("statuses", []):
                _apply_status_update(db, status_update)
            for message in value.get("messages", []):
                _apply_inbound_message(db, message)

    return Response(status_code=status.HTTP_200_OK)


def _apply_status_update(db: Session, status_update: dict) -> None:
    """Match a delivery-status callback back to the row that sent it, by Meta's own message id."""
    wa_message_id = status_update.get("id")
    new_status = status_update.get("status")
    if not wa_message_id or new_status not in _KNOWN_STATUSES:
        logger.warning("whatsapp_webhook_unrecognized_status status=%s", new_status)
        return
    message = db.scalar(select(WhatsappMessage).where(WhatsappMessage.wa_message_id == wa_message_id))
    if not message:
        return  # a status callback for a message this instance didn't send (or already pruned) - not an error
    message.status = WhatsappMessageStatus(new_status)
    db.commit()


def _apply_inbound_message(db: Session, message: dict) -> None:
    """The real opt-out compliance path: a shopper texting STOP turns off WhatsApp alerts immediately."""
    body = (message.get("text", {}) or {}).get("body", "")
    sender = message.get("from")
    if not sender or body.strip().upper() != "STOP":
        return
    phone_e164 = f"+{sender.lstrip('+')}"
    prefs = db.scalar(select(UserPreferences).where(UserPreferences.phone_number == phone_e164))
    if not prefs:
        logger.warning("whatsapp_stop_unknown_phone")
        return
    prefs.notify_whatsapp = False
    db.commit()
