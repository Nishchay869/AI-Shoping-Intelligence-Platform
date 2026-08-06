"""Add user_preferences - alert trigger rules, AI shopping persona, and smart-rule toggles the profile
page's expanded settings UI reads and writes. One row per user, JIT-created on first access (see
app.services.preferences.get_or_create), same pattern as the users table itself.

Revision ID: 0012_user_preferences
Revises: 0011_gemini_embeddings
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0012_user_preferences"
down_revision = "0011_gemini_embeddings"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
now = sa.text("now()")


def upgrade() -> None:
    op.create_table(
        "user_preferences",
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("notify_email", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notify_push", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notify_sms", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notify_whatsapp", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("phone_number", sa.String(20)),
        sa.Column("phone_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("phone_otp_hash", sa.String(64)),
        sa.Column("phone_otp_expires_at", sa.DateTime(timezone=True)),
        sa.Column("min_discount_percentage", sa.Numeric(5, 2)),
        sa.Column("alert_all_time_low", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("alert_below_90d_average", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notification_frequency", sa.Enum("instant", "daily_digest", "weekly_summary", name="notification_frequency"), nullable=False, server_default="instant"),
        sa.Column("favorite_brands", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("blacklisted_brands", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("preferred_retailers", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("budget_tier", sa.Enum("budget", "balanced", "premium", name="budget_tier")),
        sa.Column("sizing_profile", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("include_refurbished", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("restock_alerts_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("auto_buy_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=now),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=now),
    )


def downgrade() -> None:
    op.drop_table("user_preferences")
    op.execute("DROP TYPE IF EXISTS notification_frequency")
    op.execute("DROP TYPE IF EXISTS budget_tier")
