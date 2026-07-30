"""Drop the local password hash - auth is fully delegated to Supabase Auth; `users` becomes a
JIT-provisioned identity-linked profile table (see app.services.auth.provision_or_get_user). Every existing
row is wiped first: none of them can ever map to a Supabase user id, and leaving them in place risks a
future email-uniqueness collision the moment a real user signs up through Supabase with a matching email.

Revision ID: 0010_supabase_auth
Revises: 0009_product_rating_columns
"""
from alembic import op

revision = "0010_supabase_auth"
down_revision = "0009_product_rating_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Cascades to wishlists/wishlist_items/reviews/recommendations/receipts/search_queries/product_clicks/
    # purchases/chat history - every one of those FKs is ondelete="CASCADE". Confirmed before writing this
    # migration that only disposable local test accounts existed; this is not a decision to repeat blindly
    # against a database with real users.
    op.execute("TRUNCATE TABLE users CASCADE")
    op.drop_column("users", "password_hash")


def downgrade() -> None:
    import sqlalchemy as sa

    op.add_column("users", sa.Column("password_hash", sa.String(255), nullable=False, server_default=""))
