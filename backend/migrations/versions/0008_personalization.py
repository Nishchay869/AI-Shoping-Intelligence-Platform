"""Add search_queries, product_clicks, purchases (personalization signals) and a 'behavioral' recommendation reason.

Revision ID: 0008_personalization
Revises: 0007_receipts
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision = "0008_personalization"
down_revision = "0007_receipts"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
EMBEDDING_DIMENSIONS = 1024


def upgrade() -> None:
    op.execute("ALTER TYPE recommendation_reason ADD VALUE IF NOT EXISTS 'behavioral'")

    op.create_table(
        "search_queries",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("query", sa.String(300), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSIONS), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_search_queries_user_id", "search_queries", ["user_id"])

    op.create_table(
        "product_clicks",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", UUID, sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_product_clicks_user_id", "product_clicks", ["user_id"])

    op.create_table(
        "purchases",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", UUID, sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("price_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_purchases_user_id", "purchases", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_purchases_user_id", table_name="purchases")
    op.drop_table("purchases")
    op.drop_index("ix_product_clicks_user_id", table_name="product_clicks")
    op.drop_table("product_clicks")
    op.drop_index("ix_search_queries_user_id", table_name="search_queries")
    op.drop_table("search_queries")
    # Postgres cannot drop a value from an existing enum type; 'behavioral' remains defined after downgrade.
