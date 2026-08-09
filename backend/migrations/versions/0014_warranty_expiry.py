"""Add receipts.warranty_expires_at (computed from purchase_date + the LLM-inferred warranty duration) and
receipts.warranty_alert_sent (dedup marker, same idea as wishlist_items.last_alerted_price_minor).

Revision ID: 0014_warranty_expiry
Revises: 0013_whatsapp_alerts
"""
from alembic import op
import sqlalchemy as sa

revision = "0014_warranty_expiry"
down_revision = "0013_whatsapp_alerts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("receipts", sa.Column("warranty_expires_at", sa.Date()))
    op.add_column("receipts", sa.Column("warranty_alert_sent", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("receipts", "warranty_alert_sent")
    op.drop_column("receipts", "warranty_expires_at")
