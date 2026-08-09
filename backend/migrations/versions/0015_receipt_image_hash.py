"""Add receipts.image_hash (SHA-256 of the uploaded photo's bytes) plus a per-user unique constraint, so
re-uploading a receipt photo you've already scanned returns the existing saved receipt instead of creating
a duplicate history row.

Revision ID: 0015_receipt_image_hash
Revises: 0014_warranty_expiry
"""
from alembic import op
import sqlalchemy as sa

revision = "0015_receipt_image_hash"
down_revision = "0014_warranty_expiry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("receipts", sa.Column("image_hash", sa.String(64)))
    op.create_unique_constraint("uq_receipts_user_image_hash", "receipts", ["user_id", "image_hash"])


def downgrade() -> None:
    op.drop_constraint("uq_receipts_user_image_hash", "receipts", type_="unique")
    op.drop_column("receipts", "image_hash")
