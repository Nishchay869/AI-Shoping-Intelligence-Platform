"""Database engine and per-request session dependency."""
from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.core.config import get_settings

engine = create_engine(
    get_settings().database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    # Disables psycopg's server-side prepared statements. Required under Supabase's transaction-mode
    # pooler (Supavisor/PgBouncer): each transaction can land on a different backend connection, so a
    # statement prepared during one transaction may not exist for the next, causing intermittent
    # "prepared statement does not exist" errors. Harmless against a direct (non-pooled) connection too.
    connect_args={"prepare_threshold": None},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield one transaction-capable session and always close it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
