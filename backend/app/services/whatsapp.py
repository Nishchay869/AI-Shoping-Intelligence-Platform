"""Meta WhatsApp Cloud API client: sends pre-approved template messages (price_drop_alert,
warranty_expiring_alert).

Template messages (rather than free-form ones) are used specifically because that's Meta's mechanism for
messaging a user outside the 24-hour customer-service window - neither a price drop nor a warranty nearing
expiry is something the shopper just messaged about, so there's no open session to reply within. No extra
window-tracking logic is needed as a result; that's the whole point of using a template here.
"""
from datetime import date
import logging
import httpx
from app.core.config import get_settings
from app.core.exceptions import ServiceUnavailableError

logger = logging.getLogger(__name__)


def _send_template_message(phone_e164: str, template_name: str, parameters: list[tuple[str, str]]) -> str:
    """POST one template message to the Graph API; returns Meta's message id (wamid) on success.

    `parameters` is a list of (variable_name, value) pairs, sent by name rather than position - this
    account's WhatsApp Manager only accepts named template variables (e.g. {{product_title}}), not the
    older positional {{1}}/{{2}}/{{3}} style, so each parameter must carry a matching parameter_name.

    Raises ServiceUnavailableError (this codebase's existing classification for a failed/misconfigured
    external API dependency) on a missing access token or a non-2xx Graph API response.
    """
    settings = get_settings()
    if not settings.whatsapp_access_token or not settings.whatsapp_phone_number_id:
        raise ServiceUnavailableError("WhatsApp Cloud API is not configured")

    payload = {
        "messaging_product": "whatsapp",
        "to": phone_e164.lstrip("+"),
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en"},
            "components": [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "parameter_name": name, "text": value} for name, value in parameters],
                }
            ],
        },
    }

    try:
        response = httpx.post(
            f"https://graph.facebook.com/{settings.whatsapp_api_version}/{settings.whatsapp_phone_number_id}/messages",
            json=payload,
            headers={"Authorization": f"Bearer {settings.whatsapp_access_token}"},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        logger.warning("whatsapp_send_failed to=%s template=%s error=%s", phone_e164, template_name, error)
        raise ServiceUnavailableError("Could not send the WhatsApp message") from error

    return response.json()["messages"][0]["id"]


def send_price_drop_alert(phone_e164: str, product_title: str, price_minor: int, currency: str, listing_url: str) -> str:
    """Send the price_drop_alert template message. Variable names must match the template exactly as
    created in WhatsApp Manager: {{product_title}}, {{new_price}}, {{listing_url}}."""
    formatted_price = f"{currency} {price_minor / 100:,.2f}"
    parameters = [("product_title", product_title), ("new_price", formatted_price), ("listing_url", listing_url)]
    return _send_template_message(phone_e164, get_settings().whatsapp_price_alert_template, parameters)


def send_warranty_expiring_alert(phone_e164: str, product_or_store_name: str, expires_on: date, days_remaining: int) -> str:
    """Send the warranty_expiring_alert template message. Variable names must match the template exactly
    as created in WhatsApp Manager: {{product_name}}, {{days_remaining}}, {{expiry_date}}."""
    parameters = [("product_name", product_or_store_name), ("days_remaining", str(days_remaining)), ("expiry_date", expires_on.isoformat())]
    return _send_template_message(phone_e164, get_settings().whatsapp_warranty_alert_template, parameters)
