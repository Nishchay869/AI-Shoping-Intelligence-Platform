"""Add receipts and receipt_items - AI Receipt Scanner (OCR + LLM structured extraction) storage.

Revision ID: 0007_receipts
Revises: 0006_product_image_embeddings
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0007_receipts"
down_revision = "0006_product_image_embeddings"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "receipts",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("store_name", sa.String(160), nullable=True),
        sa.Column("purchase_date", sa.Date(), nullable=True),
        sa.Column("subtotal_minor", sa.Integer(), nullable=True),
        sa.Column("tax_minor", sa.Integer(), nullable=True),
        sa.Column("total_minor", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("warranty_text", sa.Text(), nullable=True),
        sa.Column("raw_ocr_text", sa.Text(), nullable=False),
        sa.Column("ocr_confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_receipts_user_id", "receipts", ["user_id"])

    op.create_table(
        "receipt_items",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("receipt_id", UUID, sa.ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_name", sa.String(300), nullable=False),
        sa.Column("price_minor", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_receipt_items_receipt_id", "receipt_items", ["receipt_id"])


def downgrade() -> None:
    op.drop_index("ix_receipt_items_receipt_id", table_name="receipt_items")
    op.drop_table("receipt_items")
    op.drop_index("ix_receipts_user_id", table_name="receipts")
    op.drop_table("receipts")
