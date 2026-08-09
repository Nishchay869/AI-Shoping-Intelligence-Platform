"""Add whatsapp_messages (delivery log + dedup for outbound price-drop alerts) and
wishlist_items.last_alerted_price_minor (dedup marker: only re-alert on a new, lower price).

Revision ID: 0013_whatsapp_alerts
Revises: 0012_user_preferences
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0013_whatsapp_alerts"
down_revision = "0012_user_preferences"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
now = sa.text("now()")


def upgrade() -> None:
    op.add_column("wishlist_items", sa.Column("last_alerted_price_minor", sa.Integer()))

    op.create_table(
        "whatsapp_messages",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("wishlist_item_id", UUID, sa.ForeignKey("wishlist_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("price_minor", sa.Integer(), nullable=False),
        sa.Column("wa_message_id", sa.Text(), unique=True),
        sa.Column("status", sa.Enum("queued", "sent", "delivered", "read", "failed", name="whatsapp_message_status"), nullable=False, server_default="queued"),
        sa.Column("error_detail", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=now),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=now),
    )
    op.create_index("ix_whatsapp_messages_user_id", "whatsapp_messages", ["user_id"])
    # wa_message_id already gets a unique index from unique=True above; webhook status lookups use that.


def downgrade() -> None:
    op.drop_table("whatsapp_messages")
    op.execute("DROP TYPE IF EXISTS whatsapp_message_status")
    op.drop_column("wishlist_items", "last_alerted_price_minor")
