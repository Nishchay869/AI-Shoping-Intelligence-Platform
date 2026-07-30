"""Add a CLIP image embedding column for image-based product search.

512-dim to match openai/clip-vit-base-patch32's projection_dim (verified against the actual model config,
not assumed) - a distinct vector space from Product.embedding (1024-dim Voyage text embeddings), so it gets
its own column and its own HNSW index rather than reusing the text one.

Revision ID: 0006_product_image_embeddings
Revises: 0005_product_specifications
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0006_product_image_embeddings"
down_revision = "0005_product_specifications"
branch_labels = None
depends_on = None

IMAGE_EMBEDDING_DIMENSIONS = 512


def upgrade() -> None:
    op.add_column("products", sa.Column("image_embedding", Vector(IMAGE_EMBEDDING_DIMENSIONS), nullable=True))
    op.execute("CREATE INDEX IF NOT EXISTS ix_products_image_embedding_cosine ON products USING hnsw (image_embedding vector_cosine_ops)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_products_image_embedding_cosine")
    op.drop_column("products", "image_embedding")
