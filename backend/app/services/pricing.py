"""The single write path for a retailer offer's price. No real price-ingestion job exists yet (see
workers/price-check.ts's Inngest stub - deferred pending retailer API credentials); this is the function
one will call once it does, and it's the natural hook point for evaluating price-drop alerts."""
from sqlalchemy.orm import Session
from app.models import PriceHistory, ProductOffer
from app.services import price_alerts


def record_price_observation(db: Session, offer: ProductOffer, price_minor: int, available: bool) -> PriceHistory:
    """Record one observed price point for an offer, update its current price/availability, and evaluate
    price-drop alerts if this is actually a drop (cheap short-circuit - the real dedup guarantee lives in
    price_alerts.evaluate_and_notify's last_alerted_price_minor check, this just skips the join/scan on
    every non-drop observation)."""
    previous_price_minor = offer.current_price_minor
    observation = PriceHistory(offer_id=offer.id, price_minor=price_minor, currency=offer.currency, is_available=available)
    db.add(observation)
    offer.current_price_minor = price_minor
    offer.is_available = available
    db.commit()
    db.refresh(observation)

    if available and price_minor < previous_price_minor:
        price_alerts.evaluate_and_notify(db, offer, price_minor)

    return observation
