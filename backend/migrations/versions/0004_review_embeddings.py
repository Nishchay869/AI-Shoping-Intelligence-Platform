"""Add a review embedding column so the RAG retriever can run similarity search over review text.

Revision ID: 0004_review_embeddings
Revises: 0003_ai_recommendation_engine
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0004_review_embeddings"
down_revision = "0003_ai_recommendation_engine"
branch_labels = None
depends_on = None

EMBEDDING_DIMENSIONS = 1024


def upgrade() -> None:
    op.add_column("reviews", sa.Column("embedding", Vector(EMBEDDING_DIMENSIONS), nullable=True))
    op.execute("CREATE INDEX IF NOT EXISTS ix_reviews_embedding_cosine ON reviews USING hnsw (embedding vector_cosine_ops)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_reviews_embedding_cosine")
    op.drop_column("reviews", "embedding")
