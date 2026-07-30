"""Normalize commerce data and add history, orders, recommendations, search, and chat.

Revision ID: 0002_shopping_intelligence_schema
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_commerce_schema"  # kept <=32 chars: alembic_version.version_num is VARCHAR(32) by default
down_revision = "0001_initial"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
now = sa.text("now()")
uuid_default = sa.text("gen_random_uuid()")


def id_column() -> sa.Column:
    """Use database-generated UUIDs so all writers receive collision-safe identifiers."""
    return sa.Column("id", UUID, primary_key=True, server_default=uuid_default)


def timestamps() -> list[sa.Column]:
    """Provide UTC creation/update audit fields on mutable aggregate tables."""
    return [sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=now), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=now)]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    # Each enum below is created exactly once, by the single column that uses it (sa.Enum(*values, name=...)
    # with its default create_type=True) - not via a separate raw CREATE TYPE statement. Doing both, as an
    # earlier version of this migration did, makes Postgres reject the second attempt with "type already
    # exists" the first time this migration is ever run against a real database (create_type=False on a
    # column that isn't bound to a shared MetaData does not suppress this in SQLAlchemy 2.0 - the column's
    # own DDL hook still fires).

    op.create_table("categories", id_column(), sa.Column("name", sa.String(120), nullable=False), sa.Column("slug", sa.String(140), nullable=False), *timestamps(), sa.UniqueConstraint("slug", name="uq_categories_slug"))
    op.create_table("product_categories", sa.Column("product_id", UUID, sa.ForeignKey("products.id", ondelete="CASCADE"), primary_key=True), sa.Column("category_id", UUID, sa.ForeignKey("categories.id", ondelete="RESTRICT"), primary_key=True))
    op.create_index("ix_product_categories_category", "product_categories", ["category_id", "product_id"])

    op.create_table("retailers", id_column(), sa.Column("name", sa.String(120), nullable=False), sa.Column("code", sa.String(64), nullable=False), sa.Column("website_url", sa.Text(), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), *timestamps(), sa.UniqueConstraint("code", name="uq_retailers_code"))
    op.create_table("product_offers", id_column(), sa.Column("product_id", UUID, sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False), sa.Column("retailer_id", UUID, sa.ForeignKey("retailers.id", ondelete="RESTRICT"), nullable=False), sa.Column("external_listing_id", sa.String(255), nullable=False), sa.Column("listing_url", sa.Text(), nullable=False), sa.Column("currency", sa.String(3), nullable=False), sa.Column("current_price_minor", sa.BigInteger(), nullable=False), sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.true()), *timestamps(), sa.CheckConstraint("current_price_minor >= 0", name="ck_offer_nonnegative_price"), sa.CheckConstraint("currency ~ '^[A-Z]{3}$'", name="ck_offer_iso_currency"), sa.UniqueConstraint("retailer_id", "external_listing_id", name="uq_offer_retailer_listing"))
    op.create_index("ix_product_offers_product_price", "product_offers", ["product_id", "current_price_minor"])
    op.create_index("ix_product_offers_retailer_available", "product_offers", ["retailer_id", "is_available"])

    op.create_table("reviews", id_column(), sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("product_id", UUID, sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False), sa.Column("rating", sa.SmallInteger(), nullable=False), sa.Column("title", sa.String(160)), sa.Column("body", sa.Text()), sa.Column("is_verified_purchase", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("is_visible", sa.Boolean(), nullable=False, server_default=sa.true()), *timestamps(), sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating_range"), sa.UniqueConstraint("user_id", "product_id", name="uq_review_user_product"))
    op.create_index("ix_reviews_product_visible_created", "reviews", ["product_id", "is_visible", sa.text("created_at DESC")])

    op.create_table("orders", id_column(), sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("order_number", sa.String(40), nullable=False), sa.Column("status", sa.Enum("pending", "confirmed", "paid", "cancelled", "refunded", name="order_status"), nullable=False, server_default="pending"), sa.Column("currency", sa.String(3), nullable=False), sa.Column("subtotal_minor", sa.BigInteger(), nullable=False), sa.Column("discount_minor", sa.BigInteger(), nullable=False, server_default="0"), sa.Column("total_minor", sa.BigInteger(), nullable=False), sa.Column("placed_at", sa.DateTime(timezone=True)), *timestamps(), sa.CheckConstraint("subtotal_minor >= 0 AND discount_minor >= 0 AND total_minor >= 0", name="ck_orders_nonnegative_amounts"), sa.CheckConstraint("currency ~ '^[A-Z]{3}$'", name="ck_orders_iso_currency"), sa.UniqueConstraint("order_number", name="uq_orders_number"))
    op.create_index("ix_orders_user_created", "orders", ["user_id", sa.text("created_at DESC")])
    op.create_table("order_items", id_column(), sa.Column("order_id", UUID, sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False), sa.Column("product_id", UUID, sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False), sa.Column("offer_id", UUID, sa.ForeignKey("product_offers.id", ondelete="SET NULL")), sa.Column("product_title_snapshot", sa.String(500), nullable=False), sa.Column("unit_price_minor", sa.BigInteger(), nullable=False), sa.Column("quantity", sa.Integer(), nullable=False), sa.Column("line_total_minor", sa.BigInteger(), nullable=False), sa.CheckConstraint("unit_price_minor >= 0 AND quantity > 0 AND line_total_minor >= 0", name="ck_order_items_valid_amounts"))
    op.create_index("ix_order_items_order", "order_items", ["order_id"])

    op.create_table("price_history", id_column(), sa.Column("offer_id", UUID, sa.ForeignKey("product_offers.id", ondelete="CASCADE"), nullable=False), sa.Column("price_minor", sa.BigInteger(), nullable=False), sa.Column("currency", sa.String(3), nullable=False), sa.Column("is_available", sa.Boolean(), nullable=False), sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False, server_default=now), sa.CheckConstraint("price_minor >= 0", name="ck_price_history_nonnegative"), sa.CheckConstraint("currency ~ '^[A-Z]{3}$'", name="ck_price_history_iso_currency"), sa.UniqueConstraint("offer_id", "observed_at", name="uq_price_history_offer_observed"))
    op.create_index("ix_price_history_offer_observed", "price_history", ["offer_id", sa.text("observed_at DESC")])
    op.create_index("ix_price_history_observed", "price_history", [sa.text("observed_at DESC")])

    op.create_table("recommendations", id_column(), sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("product_id", UUID, sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False), sa.Column("reason", sa.Enum("similar_product", "price_drop", "wishlist_match", "ai_personalized", name="recommendation_reason"), nullable=False), sa.Column("score", sa.Numeric(5, 4), nullable=False), sa.Column("explanation", sa.Text()), sa.Column("is_dismissed", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("expires_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=now), sa.CheckConstraint("score >= 0 AND score <= 1", name="ck_recommendations_score"), sa.UniqueConstraint("user_id", "product_id", "reason", name="uq_recommendation_user_product_reason"))
    op.create_index("ix_recommendations_feed", "recommendations", ["user_id", "is_dismissed", sa.text("score DESC"), sa.text("created_at DESC")])

    op.create_table("search_history", id_column(), sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE")), sa.Column("query", sa.String(500), nullable=False), sa.Column("filters", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")), sa.Column("result_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("searched_at", sa.DateTime(timezone=True), nullable=False, server_default=now), sa.CheckConstraint("char_length(btrim(query)) > 0", name="ck_search_history_nonempty_query"), sa.CheckConstraint("result_count >= 0", name="ck_search_history_nonnegative_results"))
    op.create_index("ix_search_history_user_time", "search_history", ["user_id", sa.text("searched_at DESC")])
    op.create_index("ix_search_history_filters", "search_history", ["filters"], postgresql_using="gin")

    op.create_table("chat_conversations", id_column(), sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("title", sa.String(160)), sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=False, server_default=now), *timestamps())
    op.create_index("ix_chat_conversations_user_last", "chat_conversations", ["user_id", sa.text("last_message_at DESC")])
    op.create_table("chat_messages", id_column(), sa.Column("conversation_id", UUID, sa.ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False), sa.Column("role", sa.Enum("system", "user", "assistant", name="chat_role"), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=now), sa.CheckConstraint("char_length(btrim(content)) > 0", name="ck_chat_messages_nonempty_content"))
    op.create_index("ix_chat_messages_conversation_time", "chat_messages", ["conversation_id", "created_at"])


def downgrade() -> None:
    for table, index in [("chat_messages", "ix_chat_messages_conversation_time"), ("chat_conversations", "ix_chat_conversations_user_last"), ("search_history", "ix_search_history_filters"), ("search_history", "ix_search_history_user_time"), ("recommendations", "ix_recommendations_feed"), ("price_history", "ix_price_history_observed"), ("price_history", "ix_price_history_offer_observed"), ("order_items", "ix_order_items_order"), ("orders", "ix_orders_user_created"), ("reviews", "ix_reviews_product_visible_created"), ("product_offers", "ix_product_offers_retailer_available"), ("product_offers", "ix_product_offers_product_price"), ("product_categories", "ix_product_categories_category")]: op.drop_index(index, table_name=table)
    for table in ["chat_messages", "chat_conversations", "search_history", "recommendations", "price_history", "order_items", "orders", "reviews", "product_offers", "retailers", "product_categories", "categories"]: op.drop_table(table)
    # IF EXISTS: dropping each table above may already auto-drop its enum type via the same column-owned
    # DDL lifecycle that creates it in upgrade() - see the comment there. Idempotent either way.
    op.execute("DROP TYPE IF EXISTS chat_role"); op.execute("DROP TYPE IF EXISTS recommendation_reason"); op.execute("DROP TYPE IF EXISTS order_status")
