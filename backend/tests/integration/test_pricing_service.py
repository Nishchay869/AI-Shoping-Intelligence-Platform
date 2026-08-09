"""Integration tests: services/pricing.py - the price-observation write path - against a real Postgres database."""
from app.schemas.wishlist import AddWishlistItemRequest, CreateWishlistRequest
from app.services import pricing, wishlist


def test_records_a_price_history_row_and_updates_the_offer(db_session, make_offer) -> None:
    offer = make_offer(price_minor=10000, available=True)

    observation = pricing.record_price_observation(db_session, offer, price_minor=8000, available=True)

    assert observation.price_minor == 8000
    db_session.refresh(offer)
    assert offer.current_price_minor == 8000
    assert offer.is_available is True


def test_marks_offer_unavailable(db_session, make_offer) -> None:
    offer = make_offer(price_minor=10000, available=True)

    pricing.record_price_observation(db_session, offer, price_minor=10000, available=False)

    db_session.refresh(offer)
    assert offer.is_available is False


def test_a_genuine_drop_triggers_alert_evaluation(db_session, make_user, make_offer, monkeypatch) -> None:
    from app.services import preferences

    user = make_user()
    prefs = preferences.get_or_create(db_session, user)
    prefs.notify_whatsapp = True
    prefs.phone_verified = True
    prefs.phone_number = "+15551234567"
    db_session.commit()

    offer = make_offer(price_minor=10000, available=True)
    my_list = wishlist.create_wishlist(db_session, user, CreateWishlistRequest())
    item = wishlist.add_item(db_session, user, my_list.id, AddWishlistItemRequest(product_id=offer.product_id, target_price_minor=9000))
    monkeypatch.setattr("app.services.whatsapp.send_price_drop_alert", lambda **kwargs: "wamid.PRICING_TEST")

    pricing.record_price_observation(db_session, offer, price_minor=8000, available=True)

    db_session.refresh(item)
    assert item.last_alerted_price_minor == 8000


def test_a_price_increase_does_not_trigger_alert_evaluation(db_session, make_user, make_offer, monkeypatch) -> None:
    from app.services import preferences

    user = make_user()
    prefs = preferences.get_or_create(db_session, user)
    prefs.notify_whatsapp = True
    prefs.phone_verified = True
    prefs.phone_number = "+15551234567"
    db_session.commit()

    offer = make_offer(price_minor=8000, available=True)
    my_list = wishlist.create_wishlist(db_session, user, CreateWishlistRequest())
    item = wishlist.add_item(db_session, user, my_list.id, AddWishlistItemRequest(product_id=offer.product_id, target_price_minor=9000))

    def _fail_if_called(**kwargs):
        raise AssertionError("should not be called for a price increase")

    monkeypatch.setattr("app.services.whatsapp.send_price_drop_alert", _fail_if_called)

    pricing.record_price_observation(db_session, offer, price_minor=9500, available=True)  # a rise, not a drop

    db_session.refresh(item)
    assert item.last_alerted_price_minor is None
