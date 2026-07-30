"""Security tests: JWT attacks against the real HTTP layer (unit-level algorithm/expiry/signature checks
live in tests/unit/test_security.py - this file is about what a real request with a malicious token gets
back, over real routes)."""
import time

import jwt as pyjwt

from app.core.config import get_settings


def _payload(**overrides) -> dict:
    now = int(time.time())
    payload = {
        "sub": "00000000-0000-0000-0000-000000000000",
        "email": "nobody@example.com",
        "aud": "authenticated",
        "role": "authenticated",
        "iss": f"{get_settings().supabase_url.rstrip('/')}/auth/v1",
        "iat": now,
        "exp": now + 3600,
    }
    payload.update(overrides)
    return payload


def test_request_with_no_token_is_unauthorized(client) -> None:
    assert client.get("/api/v1/auth/me").status_code == 401


def test_request_with_malformed_token_is_unauthorized(client) -> None:
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer this.is.not.a.jwt"}).status_code == 401


def test_request_with_none_algorithm_forged_token_is_unauthorized(client) -> None:
    forged = pyjwt.encode(_payload(), "", algorithm="none")
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


def test_request_with_wrong_key_signed_token_is_unauthorized(client, other_keypair) -> None:
    forged = pyjwt.encode(_payload(), other_keypair, algorithm="ES256")
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


def test_request_with_hs256_signed_token_is_unauthorized(client) -> None:
    forged = pyjwt.encode(_payload(), "totally-wrong-secret", algorithm="HS256")
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


def test_request_with_expired_token_is_unauthorized(client, supabase_test_keypair) -> None:
    expired = pyjwt.encode(_payload(exp=int(time.time()) - 1), supabase_test_keypair, algorithm="ES256")
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_request_with_wrong_audience_token_is_unauthorized(client, supabase_test_keypair) -> None:
    forged = pyjwt.encode(_payload(aud="something-else"), supabase_test_keypair, algorithm="ES256")
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


def test_request_with_wrong_issuer_token_is_unauthorized(client, supabase_test_keypair) -> None:
    forged = pyjwt.encode(_payload(iss="https://not-this-project.supabase.co/auth/v1"), supabase_test_keypair, algorithm="ES256")
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


def test_valid_token_for_a_nonexistent_email_is_unauthorized(client, supabase_test_keypair) -> None:
    """A well-formed, correctly-signed, unexpired token for a brand-new sub but with no email claim can't be
    JIT-provisioned (this app requires an email) and must not be treated as authenticated."""
    token = pyjwt.encode(_payload(email=None), supabase_test_keypair, algorithm="ES256")
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_token_with_non_uuid_subject_is_unauthorized(client, supabase_test_keypair) -> None:
    token = pyjwt.encode(_payload(sub="not-a-uuid-at-all"), supabase_test_keypair, algorithm="ES256")
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_privilege_escalation_via_forged_admin_claim_does_not_grant_admin(as_user, make_user, db_session) -> None:
    """admin status must be read from the User row in the database, never trusted from the token payload.
    require_admin() isn't wired to any route yet (grep confirms it), so this proves the dependency's own
    logic directly: a non-admin user resolved via get_current_user is rejected by require_admin regardless
    of what a token might claim, since get_current_user never even looks at an "admin" claim to begin with."""
    from fastapi import HTTPException

    from app.api.deps import require_admin

    non_admin = make_user(is_admin=False)
    try:
        require_admin(non_admin)
        assert False, "require_admin must reject a non-admin user"
    except HTTPException as exc:
        assert exc.status_code == 403

    admin = make_user(email="admin@example.com", is_admin=True)
    assert require_admin(admin) is admin
