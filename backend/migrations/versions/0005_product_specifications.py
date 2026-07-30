"""Add product_specifications, structured spec fields the shopping assistant's tools read from.

Revision ID: 0005_product_specifications
Revises: 0004_review_embeddings
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_product_specifications"
down_revision = "0004_review_embeddings"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "product_specifications",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("product_id", UUID, sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("value", sa.String(500), nullable=False),
    )
    op.create_index("ix_product_specifications_product", "product_specifications", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_product_specifications_product", table_name="product_specifications")
    op.drop_table("product_specifications")
