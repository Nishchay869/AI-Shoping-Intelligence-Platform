"""Unit tests: Supabase JWT verification. No DB, no network - conftest.py's autouse _mock_supabase_jwks
fixture points the JWKS client at a locally-generated test keypair, so these exercise the real signature/
expiry/audience/issuer checks without ever calling a real Supabase project."""
import time

import jwt as pyjwt
import pytest

from app.core.config import get_settings
from app.core.security import verify_supabase_token


def _payload(**overrides) -> dict:
    now = int(time.time())
    payload = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "shopper@example.com",
        "aud": "authenticated",
        "role": "authenticated",
        "iss": f"{get_settings().supabase_url.rstrip('/')}/auth/v1",
        "iat": now,
        "exp": now + 3600,
    }
    payload.update(overrides)
    return payload


def test_valid_token_round_trips(supabase_test_keypair) -> None:
    token = pyjwt.encode(_payload(), supabase_test_keypair, algorithm="ES256")
    claims = verify_supabase_token(token)
    assert claims["sub"] == "11111111-1111-1111-1111-111111111111"
    assert claims["email"] == "shopper@example.com"


def test_expired_token_is_rejected(supabase_test_keypair) -> None:
    token = pyjwt.encode(_payload(exp=int(time.time()) - 10), supabase_test_keypair, algorithm="ES256")
    with pytest.raises(pyjwt.ExpiredSignatureError):
        verify_supabase_token(token)


def test_malformed_token_is_rejected() -> None:
    with pytest.raises(pyjwt.PyJWTError):
        verify_supabase_token("this.is.not.a.jwt")


def test_wrong_signature_is_rejected(other_keypair) -> None:
    """Signed with a *different* keypair than the one the mocked JWKS actually serves - proves verification
    checks the real signature against the real key, not just structural validity."""
    token = pyjwt.encode(_payload(), other_keypair, algorithm="ES256")
    with pytest.raises(pyjwt.InvalidSignatureError):
        verify_supabase_token(token)


def test_wrong_audience_is_rejected(supabase_test_keypair) -> None:
    token = pyjwt.encode(_payload(aud="something-else"), supabase_test_keypair, algorithm="ES256")
    with pytest.raises(pyjwt.InvalidAudienceError):
        verify_supabase_token(token)


def test_wrong_issuer_is_rejected(supabase_test_keypair) -> None:
    token = pyjwt.encode(_payload(iss="https://not-this-project.supabase.co/auth/v1"), supabase_test_keypair, algorithm="ES256")
    with pytest.raises(pyjwt.InvalidIssuerError):
        verify_supabase_token(token)


def test_algorithm_none_forgery_is_rejected() -> None:
    """The classic JWT vulnerability: a token self-declaring alg=none, unsigned. verify_supabase_token pins
    an explicit algorithm allowlist, so this must never be accepted regardless of the token's own header."""
    forged = pyjwt.encode(_payload(), "", algorithm="none")
    with pytest.raises(pyjwt.PyJWTError):
        verify_supabase_token(forged)


def test_token_signed_with_hs256_is_rejected() -> None:
    """A token signed with a symmetric algorithm must not verify against the EC public key expected for
    ES256 - the classic RS256/HS256 key-confusion attack, guarded against simply by pinning
    algorithms=["ES256"] and never accepting an algorithm the token itself gets to choose."""
    forged = pyjwt.encode(_payload(), "some-guessed-or-leaked-secret", algorithm="HS256")
    with pytest.raises(pyjwt.PyJWTError):
        verify_supabase_token(forged)
