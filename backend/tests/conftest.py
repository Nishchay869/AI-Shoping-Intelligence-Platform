"""Shared pytest fixtures: a real Postgres+pgvector test database (transactional, rolled back per test),
a FastAPI TestClient wired to it, and factories for the objects most tests need (users, auth headers,
embedded products). Real DB, real crypto, real HTTP layer - only genuinely external services (Gemini,
Voyage, CLIP/OCR at the network/model boundary, and Supabase's JWKS endpoint) are mocked, and only where a
test says so.
"""
import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://localhost:5432/pricewise_test")
os.environ.setdefault("SUPABASE_URL", "https://test-project.supabase.co")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")  # index 1: isolated from a real dev Redis on index 0
# Force-cleared, not just defaulted: a real, working key in the developer's own backend/.env would otherwise
# take priority over an unset os.environ var (pydantic-settings' env_file is a fallback under real env vars,
# not the other way around) - and tests that specifically exercise the "no key configured" 503 path must
# never accidentally make a real, billed network call just because the developer happens to have a working
# key sitting in .env.
os.environ["GEMINI_API_KEY"] = ""
os.environ["WHATSAPP_ACCESS_TOKEN"] = ""  # same reasoning: never let a real backend/.env token cause a real, billed WhatsApp send in tests

import random
import time
from uuid import uuid4

import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from redis import Redis
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.api.deps import get_current_user, get_current_user_optional, get_db
from app.core.config import get_settings
from app.main import app
from app.models import Product, ProductOffer, Retailer, User


@pytest.fixture(scope="session")
def db_engine():
    """One engine for the whole test run; migrations are applied out-of-band (see README in this directory)."""
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    """A session bound to a SAVEPOINT inside one real transaction, rolled back after the test.

    Service code calls db.commit() internally (see e.g. services/auth.py) - a plain outer rollback alone
    wouldn't undo those. The standard SQLAlchemy recipe for this is to run the whole test inside one
    connection-level transaction, give the Session a nested SAVEPOINT, and restart the SAVEPOINT every time
    the Session's own commit() closes it - so app-level commits become invisible SAVEPOINT releases, and only
    the fixture's own final rollback() actually discards anything.
    """
    connection = db_engine.connect()
    outer_transaction = connection.begin()
    session_factory = sessionmaker(bind=connection, autoflush=False, autocommit=False, expire_on_commit=False)
    session = session_factory()
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, transaction):
        if transaction.nested and not transaction._parent.nested:
            sess.begin_nested()

    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    """TestClient wired to the real app, with only the DB session swapped for the transactional test one."""
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _clean_redis():
    """Rate-limit state is per-test-run noise otherwise; flush the isolated test Redis DB (index 1) before
    and after every test so tests can't leak rate-limit counters into each other."""
    try:
        redis_client = Redis.from_url(get_settings().redis_url)
        redis_client.flushdb()
    except Exception:
        pass  # Redis-dependent tests will fail on their own if it's genuinely unavailable
    yield
    try:
        Redis.from_url(get_settings().redis_url).flushdb()
    except Exception:
        pass


@pytest.fixture(scope="session")
def supabase_test_keypair():
    """A locally-generated EC keypair standing in for Supabase's real per-project signing key - lets tests
    mint tokens with a real, verifiable ES256 signature without any network call to a real Supabase project."""
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture(scope="session")
def other_keypair():
    """A second, unrelated EC keypair - for proving a token signed with the wrong key is rejected, not just
    structurally well-formed tokens accepted."""
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture(autouse=True)
def _mock_supabase_jwks(monkeypatch, supabase_test_keypair):
    """Point verify_supabase_token's JWKS client at the local test keypair's public half instead of making a
    real network call to Supabase - every test's tokens get verified against this same fixed key."""
    public_key = supabase_test_keypair.public_key()

    class _FakeJWKClient:
        def get_signing_key_from_jwt(self, token: str):
            return type("SigningKey", (), {"key": public_key})()

    monkeypatch.setattr("app.core.security._jwks_client", lambda: _FakeJWKClient())


@pytest.fixture()
def make_user(db_session):
    """Factory: create and persist a user row, as if JIT-provisioned by a real Supabase sign-in."""

    def _make(email: str | None = None, is_admin: bool = False) -> User:
        user = User(email=email or f"user-{uuid4().hex[:12]}@example.com", display_name="Test User", is_admin=is_admin)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make


@pytest.fixture()
def make_supabase_token(supabase_test_keypair):
    """Factory: a real, verifiable-signature Supabase-shaped access token for a given user - signed with the
    same test keypair _mock_supabase_jwks exposes as the "project" JWKS."""

    def _make(user: User, **claim_overrides) -> str:
        now = int(time.time())
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "aud": "authenticated",
            "role": "authenticated",
            "iss": f"{get_settings().supabase_url.rstrip('/')}/auth/v1",
            "iat": now,
            "exp": now + 3600,
        }
        payload.update(claim_overrides)
        return pyjwt.encode(payload, supabase_test_keypair, algorithm="ES256")

    return _make


@pytest.fixture()
def auth_headers(make_supabase_token):
    """Factory: a valid bearer-token Authorization header for any given user."""

    def _headers(user: User) -> dict[str, str]:
        return {"Authorization": f"Bearer {make_supabase_token(user)}"}

    return _headers


@pytest.fixture()
def as_user(client, db_session):
    """Factory: override auth entirely (no real JWT round-trip) when a test only cares about "acting as this
    user", not about token mechanics themselves - JWT mechanics have their own dedicated tests.

    Overrides both dependency variants - routes use whichever fits their access model (get_current_user for
    auth-required endpoints, get_current_user_optional for endpoints that behave differently for anonymous
    callers, e.g. receipts/scan) - so a test doesn't need to know or care which one the route it's hitting
    happens to use.
    """

    def _as(user: User) -> TestClient:
        app.dependency_overrides[get_current_user] = lambda: user
        app.dependency_overrides[get_current_user_optional] = lambda: user
        return client

    return _as


def _random_vector(dimensions: int) -> list[float]:
    return [random.uniform(-1, 1) for _ in range(dimensions)]


@pytest.fixture()
def make_product(db_session):
    """Factory: create a persisted catalog product, optionally with real-shaped (random) embeddings so
    pgvector similarity queries have something genuine to search over."""

    def _make(*, title: str = "Test Product", price_minor: int = 9999, with_embedding: bool = False, with_image_embedding: bool = False, **overrides) -> Product:
        default_embedding = _random_vector(768) if with_embedding else None
        default_image_embedding = _random_vector(512) if with_image_embedding else None
        product = Product(
            title=title,
            brand=overrides.pop("brand", "TestBrand"),
            category=overrides.pop("category", "Electronics"),
            currency=overrides.pop("currency", "USD"),
            current_price_minor=price_minor,
            retailer=overrides.pop("retailer", "TestRetailer"),
            embedding=overrides.pop("embedding", default_embedding),
            image_embedding=overrides.pop("image_embedding", default_image_embedding),
            **overrides,
        )
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)
        return product

    return _make


@pytest.fixture()
def make_offer(db_session, make_product):
    """Factory: create a persisted retailer + product offer, for price-observation/alert tests."""

    def _make(*, product: Product | None = None, price_minor: int = 9999, currency: str = "USD", available: bool = True, **overrides) -> ProductOffer:
        product = product or make_product()
        retailer = Retailer(name="Test Retailer", code=f"retailer-{uuid4().hex[:8]}", website_url="https://example.com")
        db_session.add(retailer)
        db_session.commit()
        db_session.refresh(retailer)
        offer = ProductOffer(
            product_id=product.id,
            retailer_id=retailer.id,
            external_listing_id=overrides.pop("external_listing_id", uuid4().hex),
            listing_url=overrides.pop("listing_url", "https://example.com/listing"),
            currency=currency,
            current_price_minor=price_minor,
            is_available=available,
        )
        db_session.add(offer)
        db_session.commit()
        db_session.refresh(offer)
        return offer

    return _make
