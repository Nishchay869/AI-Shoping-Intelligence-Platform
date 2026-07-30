"""Initial users, products, and private wishlist tables."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("users", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("email", sa.String(320), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("display_name", sa.String(80), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False), sa.Column("is_admin", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.UniqueConstraint("email"))
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table("products", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("title", sa.String(500), nullable=False), sa.Column("brand", sa.String(120)), sa.Column("category", sa.String(120)), sa.Column("image_url", sa.Text()), sa.Column("currency", sa.String(3), nullable=False), sa.Column("current_price_minor", sa.Integer(), nullable=False), sa.Column("retailer", sa.String(64), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_index("ix_products_title", "products", ["title"]); op.create_index("ix_products_category", "products", ["category"])
    op.create_table("wishlists", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("name", sa.String(80), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False)); op.create_index("ix_wishlists_user_id", "wishlists", ["user_id"])
    op.create_table("wishlist_items", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("wishlist_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("wishlists.id", ondelete="CASCADE"), nullable=False), sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False), sa.Column("target_price_minor", sa.Integer()), sa.UniqueConstraint("wishlist_id", "product_id", name="uq_wishlist_product"))


def downgrade() -> None:
    op.drop_table("wishlist_items"); op.drop_index("ix_wishlists_user_id", table_name="wishlists"); op.drop_table("wishlists"); op.drop_index("ix_products_category", table_name="products"); op.drop_index("ix_products_title", table_name="products"); op.drop_table("products"); op.drop_index("ix_users_email", table_name="users"); op.drop_table("users")
