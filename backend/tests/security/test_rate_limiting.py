"""Security tests: rate limiting, real Redis-backed, across multiple endpoints with different limits."""


def test_wishlist_create_rate_limit_returns_429_after_threshold(as_user, make_user) -> None:
    """Limit is 20/60s."""
    api = as_user(make_user())
    statuses = []
    for i in range(22):
        response = api.post("/api/v1/wishlists", json={"name": f"List {i}"})
        statuses.append(response.status_code)
    assert statuses[:20] == [201] * 20
    assert statuses[20:] == [429, 429]


def test_rate_limit_is_scoped_per_ip_not_shared_globally(client) -> None:
    """TestClient requests all share one fake client IP, so this documents the *mechanism* precisely: the
    limiter key includes client_ip, meaning two different real users behind two different IPs each get their
    own budget - verified here by confirming the key format directly."""
    from app.api.deps import rate_limit
    import inspect

    source = inspect.getsource(rate_limit)
    assert "client_ip" in source and 'f"rate:{request.url.path}:{client_ip}"' in source


def test_rate_limit_returns_retry_after_header(as_user, make_user) -> None:
    api = as_user(make_user())
    response = None
    for i in range(21):
        response = api.post("/api/v1/wishlists", json={"name": f"List {i}"})
    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_rate_limit_is_enforced_separately_per_endpoint(as_user, make_user, make_product) -> None:
    """Exhausting /api/v1/wishlists' budget (20/60s) must not affect /api/v1/activity/click's separate
    budget (120/60s)."""
    api = as_user(make_user())
    for i in range(21):
        api.post("/api/v1/wishlists", json={"name": f"List {i}"})

    product = make_product()
    response = api.post("/api/v1/activity/click", json={"product_id": str(product.id)})
    assert response.status_code == 204
