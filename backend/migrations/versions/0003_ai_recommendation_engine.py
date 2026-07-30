"""Add pgvector support and a product embedding column for the AI recommendation engine.

Revision ID: 0003_ai_recommendation_engine
Revises: 0002_shopping_intelligence_schema
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0003_ai_recommendation_engine"
down_revision = "0002_commerce_schema"
branch_labels = None
depends_on = None

EMBEDDING_DIMENSIONS = 1024


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column("products", sa.Column("embedding", Vector(EMBEDDING_DIMENSIONS), nullable=True))
    # HNSW needs no pre-existing data to build (unlike ivfflat), so it stays valid as the catalog grows from zero.
    op.execute("CREATE INDEX IF NOT EXISTS ix_products_embedding_cosine ON products USING hnsw (embedding vector_cosine_ops)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_products_embedding_cosine")
    op.drop_column("products", "embedding")
    op.execute("DROP EXTENSION IF EXISTS vector")
