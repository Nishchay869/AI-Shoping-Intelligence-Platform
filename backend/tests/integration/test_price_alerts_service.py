"""Integration tests: services/price_alerts.py against a real Postgres database."""
from app.core.exceptions import ServiceUnavailableError
from app.models import WhatsappMessageStatus
from app.schemas.wishlist import AddWishlistItemRequest, CreateWishlistRequest
from app.services import preferences, price_alerts, wishlist


def _opt_in_whatsapp(db_session, user, phone: str = "+15551234567"):
    prefs = preferences.get_or_create(db_session, user)
    prefs.notify_whatsapp = True
    prefs.phone_verified = True
    prefs.phone_number = phone
    db_session.commit()
    return prefs


def _tracked_item(db_session, user, product, target_price_minor: int):
    my_list = wishlist.create_wishlist(db_session, user, CreateWishlistRequest())
    return wishlist.add_item(db_session, user, my_list.id, AddWishlistItemRequest(product_id=product.id, target_price_minor=target_price_minor))


def test_sends_alert_when_price_hits_target(db_session, make_user, make_product, make_offer, monkeypatch) -> None:
    user = make_user()
    _opt_in_whatsapp(db_session, user)
    product = make_product()
    offer = make_offer(product=product, price_minor=10000)
    item = _tracked_item(db_session, user, product, target_price_minor=9000)
    monkeypatch.setattr("app.services.whatsapp.send_price_drop_alert", lambda **kwargs: "wamid.TEST123")

    sent = price_alerts.evaluate_and_notify(db_session, offer, 8500)

    assert len(sent) == 1
    assert sent[0].status == WhatsappMessageStatus.SENT
    assert sent[0].wa_message_id == "wamid.TEST123"
    db_session.refresh(item)
    assert item.last_alerted_price_minor == 8500


def test_does_not_alert_above_target_price(db_session, make_user, make_product, make_offer, monkeypatch) -> None:
    user = make_user()
    _opt_in_whatsapp(db_session, user)
    product = make_product()
    offer = make_offer(product=product, price_minor=10000)
    _tracked_item(db_session, user, product, target_price_minor=5000)
    monkeypatch.setattr("app.services.whatsapp.send_price_drop_alert", lambda **kwargs: "wamid.TEST")

    sent = price_alerts.evaluate_and_notify(db_session, offer, 8000)  # still above the 5000 target

    assert sent == []


def test_does_not_alert_without_whatsapp_opt_in(db_session, make_user, make_product, make_offer, monkeypatch) -> None:
    user = make_user()  # no preferences configured - notify_whatsapp/phone_verified default False
    product = make_product()
    offer = make_offer(product=product, price_minor=10000)
    _tracked_item(db_session, user, product, target_price_minor=9000)
    monkeypatch.setattr("app.services.whatsapp.send_price_drop_alert", lambda **kwargs: "wamid.TEST")

    sent = price_alerts.evaluate_and_notify(db_session, offer, 8000)

    assert sent == []


def test_does_not_re_alert_at_the_same_or_higher_price(db_session, make_user, make_product, make_offer, monkeypatch) -> None:
    user = make_user()
    _opt_in_whatsapp(db_session, user)
    product = make_product()
    offer = make_offer(product=product, price_minor=10000)
    item = _tracked_item(db_session, user, product, target_price_minor=9000)
    item.last_alerted_price_minor = 8000
    db_session.commit()
    monkeypatch.setattr("app.services.whatsapp.send_price_drop_alert", lambda **kwargs: "wamid.TEST")

    unchanged = price_alerts.evaluate_and_notify(db_session, offer, 8000)  # already alerted at this exact price
    assert unchanged == []

    dropped_further = price_alerts.evaluate_and_notify(db_session, offer, 7500)  # a genuinely lower price re-alerts
    assert len(dropped_further) == 1


def test_failed_send_is_recorded_but_still_marks_the_item_alerted(db_session, make_user, make_product, make_offer, monkeypatch) -> None:
    user = make_user()
    _opt_in_whatsapp(db_session, user)
    product = make_product()
    offer = make_offer(product=product, price_minor=10000)
    item = _tracked_item(db_session, user, product, target_price_minor=9000)

    def _raise(**kwargs):
        raise ServiceUnavailableError("boom")

    monkeypatch.setattr("app.services.whatsapp.send_price_drop_alert", _raise)

    sent = price_alerts.evaluate_and_notify(db_session, offer, 8000)

    assert len(sent) == 1
    assert sent[0].status == WhatsappMessageStatus.FAILED
    assert sent[0].error_detail == "boom"
    db_session.refresh(item)
    assert item.last_alerted_price_minor == 8000  # one bad send must not retry-spam every subsequent tick


def test_only_alerts_shoppers_tracking_this_product(db_session, make_user, make_product, make_offer, monkeypatch) -> None:
    tracker = make_user(email="tracker@example.com")
    _opt_in_whatsapp(db_session, tracker, phone="+15551111111")
    bystander = make_user(email="bystander@example.com")
    _opt_in_whatsapp(db_session, bystander, phone="+15552222222")
    product = make_product()
    other_product = make_product(title="A different product")
    offer = make_offer(product=product, price_minor=10000)
    _tracked_item(db_session, tracker, product, target_price_minor=9000)
    _tracked_item(db_session, bystander, other_product, target_price_minor=9000)
    monkeypatch.setattr("app.services.whatsapp.send_price_drop_alert", lambda **kwargs: "wamid.TEST")

    sent = price_alerts.evaluate_and_notify(db_session, offer, 8000)

    assert len(sent) == 1
    assert sent[0].user_id == tracker.id
