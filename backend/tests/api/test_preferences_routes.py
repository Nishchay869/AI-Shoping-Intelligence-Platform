"""API tests: /api/v1/preferences - defaults, partial updates, and phone verification over real HTTP + DB."""


def test_requires_authentication(client) -> None:
    assert client.get("/api/v1/preferences").status_code == 401
    assert client.patch("/api/v1/preferences", json={}).status_code == 401


def test_get_creates_defaults_on_first_access(as_user, make_user) -> None:
    api = as_user(make_user())
    response = api.get("/api/v1/preferences")
    assert response.status_code == 200
    body = response.json()
    assert body["notify_email"] is True
    assert body["notification_frequency"] == "instant"
    assert body["favorite_brands"] == []


def test_patch_updates_only_given_fields(as_user, make_user) -> None:
    api = as_user(make_user())
    api.patch("/api/v1/preferences", json={"favorite_brands": ["Sony"], "budget_tier": "balanced"})

    response = api.patch("/api/v1/preferences", json={"min_discount_percentage": 20})
    assert response.status_code == 200
    body = response.json()
    assert body["min_discount_percentage"] == 20
    assert body["favorite_brands"] == ["Sony"]
    assert body["budget_tier"] == "balanced"


def test_preferences_are_private_per_user(as_user, make_user) -> None:
    alice = make_user(email="alice-prefs@example.com")
    bob = make_user(email="bob-prefs@example.com")
    as_user(alice).patch("/api/v1/preferences", json={"favorite_brands": ["Alice's brand"]})

    bob_view = as_user(bob).get("/api/v1/preferences").json()
    assert bob_view["favorite_brands"] == []


def test_phone_verification_round_trip(as_user, make_user) -> None:
    api = as_user(make_user())
    sent = api.post("/api/v1/preferences/phone/verify", json={"phone_number": "+15551234567"})
    assert sent.status_code == 202
    code = sent.json()["dev_code"]

    confirmed = api.post("/api/v1/preferences/phone/confirm", json={"code": code})
    assert confirmed.status_code == 200
    assert confirmed.json()["phone_verified"] is True


def test_phone_confirm_with_wrong_code_fails(as_user, make_user) -> None:
    api = as_user(make_user())
    api.post("/api/v1/preferences/phone/verify", json={"phone_number": "+15551234567"})
    response = api.post("/api/v1/preferences/phone/confirm", json={"code": "000000"})
    assert response.status_code == 400
