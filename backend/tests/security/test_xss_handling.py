"""Security tests: XSS. The actual defense is React's default escaping on the frontend (verified in the
frontend test suite - see tests/security/csp-middleware.test.ts) plus the Content-Security-Policy header.
What the *backend* must get right is narrower: never choke on, mangle, or selectively double-encode a
payload, and never execute or interpret it server-side - it's a data store, not a renderer.
"""

XSS_PAYLOADS = [
    "<script>alert('xss')</script>",
    "<img src=x onerror=alert(1)>",
    "<svg onload=alert(1)>",
    "javascript:alert(document.cookie)",
    "\"><script>alert(String.fromCharCode(88,83,83))</script>",
    "<iframe src=\"javascript:alert(1)\"></iframe>",
]


def test_review_body_and_title_are_stored_and_returned_verbatim(as_user, make_user, make_product) -> None:
    """The API must return exactly what was stored - it is the frontend's job to escape on render, not the
    API's job to guess at escaping (and if it did, the frontend would double-escape it)."""
    user = make_user()
    api = as_user(user)
    for payload in XSS_PAYLOADS:
        product = make_product()
        response = api.post(f"/api/v1/products/{product.id}/reviews", json={"rating": 5, "title": payload[:160], "body": payload})
        assert response.status_code == 201
        body = response.json()
        assert body["body"] == payload
        assert body["title"] == payload[:160]


def test_display_name_with_script_payload_is_stored_and_returned_verbatim(db_session) -> None:
    """display_name now only ever gets set via JIT provisioning off a verified Supabase token's
    user_metadata (see app.services.auth.provision_or_get_user) - exercised directly here rather than
    through the (now Supabase-owned) registration flow."""
    from app.services.auth import provision_or_get_user

    payload = "<script>alert('xss')</script>"
    claims = {"sub": "22222222-2222-2222-2222-222222222222", "email": "xsstest@example.com", "user_metadata": {"display_name": payload}}
    user = provision_or_get_user(db_session, claims)
    assert user.display_name == payload


def test_wishlist_name_with_xss_payload_does_not_break_the_request(as_user, make_user) -> None:
    api = as_user(make_user())
    for payload in XSS_PAYLOADS:
        response = api.post("/api/v1/wishlists", json={"name": payload[:80]})
        assert response.status_code == 201
        assert response.json()["name"] == payload[:80]


def test_search_query_with_xss_payload_is_handled_as_plain_text(client, make_product) -> None:
    make_product(title="Normal Product")
    for payload in XSS_PAYLOADS:
        response = client.get("/api/v1/products", params={"q": payload})
        assert response.status_code == 200  # never 500 - it's just a substring match against titles
