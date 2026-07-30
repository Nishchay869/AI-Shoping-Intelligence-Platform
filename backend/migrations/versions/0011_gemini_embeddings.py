"""Switch text embeddings from Voyage AI (1024-dim) to Gemini (768-dim, MRL-truncated from
gemini-embedding-001) - the two model families produce incompatible vector spaces, so every existing
embedding is cleared here and must be regenerated (see scripts/backfill_embeddings.py) before search or
personalization will work again.

Revision ID: 0011_gemini_embeddings
Revises: 0010_supabase_auth
"""
from alembic import op
from pgvector.sqlalchemy import Vector

revision = "0011_gemini_embeddings"
down_revision = "0010_supabase_auth"
branch_labels = None
depends_on = None

OLD_DIMENSIONS = 1024
NEW_DIMENSIONS = 768


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_products_embedding_cosine")
    op.execute("DROP INDEX IF EXISTS ix_reviews_embedding_cosine")

    # USING NULL sidesteps pgvector's dimension check on the implicit cast - old 1024-dim vectors cannot be
    # reinterpreted as 768-dim, they must be regenerated from source text against the new model.
    op.alter_column("products", "embedding", type_=Vector(NEW_DIMENSIONS), postgresql_using="NULL")
    op.alter_column("reviews", "embedding", type_=Vector(NEW_DIMENSIONS), postgresql_using="NULL")
    op.alter_column("search_queries", "embedding", type_=Vector(NEW_DIMENSIONS), postgresql_using="NULL")

    op.execute("CREATE INDEX IF NOT EXISTS ix_products_embedding_cosine ON products USING hnsw (embedding vector_cosine_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_reviews_embedding_cosine ON reviews USING hnsw (embedding vector_cosine_ops)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_products_embedding_cosine")
    op.execute("DROP INDEX IF EXISTS ix_reviews_embedding_cosine")

    op.alter_column("products", "embedding", type_=Vector(OLD_DIMENSIONS), postgresql_using="NULL")
    op.alter_column("reviews", "embedding", type_=Vector(OLD_DIMENSIONS), postgresql_using="NULL")
    op.alter_column("search_queries", "embedding", type_=Vector(OLD_DIMENSIONS), postgresql_using="NULL")

    op.execute("CREATE INDEX IF NOT EXISTS ix_products_embedding_cosine ON products USING hnsw (embedding vector_cosine_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_reviews_embedding_cosine ON reviews USING hnsw (embedding vector_cosine_ops)")
