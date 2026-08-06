"""Supabase Auth JWT verification. Signature/expiry/audience/issuer are checked locally against the
project's published JWKS - no per-request call to Supabase's Auth server. This project's JWKS was verified
(2026-07-28) to publish a single ES256 key; legacy HS256 shared-secret verification is intentionally not
implemented - a dual algorithm path would be dead code here and a key-confusion risk if ever exercised
carelessly.
"""
from functools import lru_cache
from ssl import SSLContext, create_default_context
from typing import Any
import certifi
import jwt
from app.core.config import get_settings


@lru_cache
def _jwks_client() -> jwt.PyJWKClient:
    """One process-lifetime JWKS client - caches fetched keys (~5 min) and auto-refreshes on an
    unrecognized kid, so this is roughly one call to Supabase per 5 minutes per process, not per request.

    The verify context is built from certifi's CA bundle explicitly rather than the OS default trust
    store: some local Python installs (notably python.org's macOS builds, unlike the Docker image this
    ships in) don't have a working default trust store, which fails this fetch with
    CERTIFICATE_VERIFY_FAILED. Pinning to certifi verifies against the exact same real CA set either
    way - it does not weaken verification, just makes it independent of host trust-store configuration.
    """
    settings = get_settings()
    verify_context: SSLContext = create_default_context(cafile=certifi.where())
    return jwt.PyJWKClient(f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json", ssl_context=verify_context)


def verify_supabase_token(token: str) -> dict[str, Any]:
    """Verify a Supabase-issued access token's signature, expiry, audience, and issuer.

    Raises jwt.PyJWTError (including jwt.PyJWKClientError) on any verification failure - callers must turn
    that into a 401, never a 500.
    """
    settings = get_settings()
    signing_key = _jwks_client().get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["ES256"],
        audience="authenticated",  # Supabase tokens always carry aud="authenticated"; PyJWT verifies aud by
        # default and rejects every valid token if this is omitted - do not remove.
        issuer=f"{settings.supabase_url.rstrip('/')}/auth/v1",
    )
