"""Relational persistence models for the first monolithic API release."""
import enum
from datetime import date, datetime
from uuid import UUID, uuid4
from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Boolean, Date, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, SmallInteger, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    wishlists: Mapped[list["Wishlist"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class NotificationFrequency(str, enum.Enum):
    INSTANT = "instant"
    DAILY_DIGEST = "daily_digest"
    WEEKLY_SUMMARY = "weekly_summary"


class BudgetTier(str, enum.Enum):
    BUDGET = "budget"
    BALANCED = "balanced"
    PREMIUM = "premium"


class UserPreferences(TimestampMixin, Base):
    """One row per user: alert trigger rules, AI shopping persona, and smart-rule toggles that drive the
    profile page's settings UI. JIT-created on first access (see services/preferences.get_or_create),
    same idea as how `users` itself is JIT-provisioned from a verified Supabase token."""
    __tablename__ = "user_preferences"
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    notify_email: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_push: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_sms: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notify_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(20))
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    phone_otp_hash: Mapped[str | None] = mapped_column(String(64))
    phone_otp_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    min_discount_percentage: Mapped[float | None] = mapped_column(Numeric(5, 2))
    alert_all_time_low: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    alert_below_90d_average: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notification_frequency: Mapped[NotificationFrequency] = mapped_column(SAEnum(NotificationFrequency, name="notification_frequency", create_type=False, values_callable=lambda enum_cls: [member.value for member in enum_cls]), default=NotificationFrequency.INSTANT, nullable=False)
    favorite_brands: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False)
    blacklisted_brands: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False)
    preferred_retailers: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"), nullable=False)
    budget_tier: Mapped[BudgetTier | None] = mapped_column(SAEnum(BudgetTier, name="budget_tier", create_type=False, values_callable=lambda enum_cls: [member.value for member in enum_cls]))
    sizing_profile: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)
    include_refurbished: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    restock_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_buy_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Product(TimestampMixin, Base):
    __tablename__ = "products"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(500), index=True, nullable=False)
    brand: Mapped[str | None] = mapped_column(String(120))
    category: Mapped[str | None] = mapped_column(String(120), index=True)
    image_url: Mapped[str | None] = mapped_column(Text)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    current_price_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    retailer: Mapped[str] = mapped_column(String(64), nullable=False)
    average_rating: Mapped[float | None] = mapped_column(Numeric(2, 1))
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))
    image_embedding: Mapped[list[float] | None] = mapped_column(Vector(512))
    wishlisted_by: Mapped[list["WishlistItem"]] = relationship(back_populates="product")
    specifications: Mapped[list["ProductSpecification"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class ProductSpecification(Base):
    """One structured spec field (e.g. 'Battery life: 30 hours') - what the shopping assistant's
    explain_specifications tool reads from, and what the RAG retriever's product text is missing today."""
    __tablename__ = "product_specifications"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    value: Mapped[str] = mapped_column(String(500), nullable=False)
    product: Mapped[Product] = relationship(back_populates="specifications")


class Wishlist(TimestampMixin, Base):
    __tablename__ = "wishlists"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), default="My Wishlist", nullable=False)
    user: Mapped[User] = relationship(back_populates="wishlists")
    items: Mapped[list["WishlistItem"]] = relationship(back_populates="wishlist", cascade="all, delete-orphan")


class WishlistItem(Base):
    __tablename__ = "wishlist_items"
    __table_args__ = (UniqueConstraint("wishlist_id", "product_id", name="uq_wishlist_product"),)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    wishlist_id: Mapped[UUID] = mapped_column(ForeignKey("wishlists.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    target_price_minor: Mapped[int | None] = mapped_column(Integer)
    last_alerted_price_minor: Mapped[int | None] = mapped_column(Integer)
    wishlist: Mapped[Wishlist] = relationship(back_populates="items")
    product: Mapped[Product] = relationship(back_populates="wishlisted_by")


class WhatsappMessageStatus(str, enum.Enum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class WhatsappMessage(TimestampMixin, Base):
    """One outbound price-drop alert: a delivery/dedup log correlated with Meta's own message id so
    webhook status callbacks (sent/delivered/read/failed) can be matched back to the row that sent it."""
    __tablename__ = "whatsapp_messages"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    wishlist_item_id: Mapped[UUID] = mapped_column(ForeignKey("wishlist_items.id", ondelete="CASCADE"), nullable=False)
    price_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    wa_message_id: Mapped[str | None] = mapped_column(Text, unique=True)
    status: Mapped[WhatsappMessageStatus] = mapped_column(SAEnum(WhatsappMessageStatus, name="whatsapp_message_status", create_type=False, values_callable=lambda enum_cls: [member.value for member in enum_cls]), default=WhatsappMessageStatus.QUEUED, nullable=False)
    error_detail: Mapped[str | None] = mapped_column(Text)


class Review(TimestampMixin, Base):
    """One shopper's rating and free-text review of a product; feeds both the aggregate rating and the AI summarizer."""
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_review_user_product"),)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    title: Mapped[str | None] = mapped_column(String(160))
    body: Mapped[str | None] = mapped_column(Text)
    is_verified_purchase: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))
    trust_score: Mapped[float | None] = mapped_column(Numeric(5, 4))
    product: Mapped[Product] = relationship()


class Retailer(TimestampMixin, Base):
    """A storefront that lists offers for products; the price-prediction pipeline's time series is per-offer."""
    __tablename__ = "retailers"
    __table_args__ = (UniqueConstraint("code", name="uq_retailers_code"),)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    website_url: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ProductOffer(TimestampMixin, Base):
    """One retailer's current listing of a product; owns the price_history time series used for forecasting."""
    __tablename__ = "product_offers"
    __table_args__ = (UniqueConstraint("retailer_id", "external_listing_id", name="uq_offer_retailer_listing"),)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    retailer_id: Mapped[UUID] = mapped_column(ForeignKey("retailers.id", ondelete="RESTRICT"), nullable=False)
    external_listing_id: Mapped[str] = mapped_column(String(255), nullable=False)
    listing_url: Mapped[str] = mapped_column(Text, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    current_price_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    product: Mapped[Product] = relationship()
    retailer: Mapped[Retailer] = relationship()
    price_history: Mapped[list["PriceHistory"]] = relationship(back_populates="offer", cascade="all, delete-orphan", order_by="PriceHistory.observed_at")


class PriceHistory(Base):
    """One observed price point for an offer; the raw daily/periodic series the prediction pipeline consumes."""
    __tablename__ = "price_history"
    __table_args__ = (UniqueConstraint("offer_id", "observed_at", name="uq_price_history_offer_observed"),)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    offer_id: Mapped[UUID] = mapped_column(ForeignKey("product_offers.id", ondelete="CASCADE"), nullable=False)
    price_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    offer: Mapped[ProductOffer] = relationship(back_populates="price_history")


class RecommendationReason(str, enum.Enum):
    SIMILAR_PRODUCT = "similar_product"
    PRICE_DROP = "price_drop"
    WISHLIST_MATCH = "wishlist_match"
    AI_PERSONALIZED = "ai_personalized"
    BEHAVIORAL = "behavioral"


class Recommendation(Base):
    """A single stored recommendation feed entry; the AI engine writes ai_personalized rows here for signed-in shoppers."""
    __tablename__ = "recommendations"
    __table_args__ = (UniqueConstraint("user_id", "product_id", "reason", name="uq_recommendation_user_product_reason"),)
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[RecommendationReason] = mapped_column(SAEnum(RecommendationReason, name="recommendation_reason", create_type=False, values_callable=lambda enum_cls: [member.value for member in enum_cls]), nullable=False)
    score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    product: Mapped[Product] = relationship()


class Receipt(TimestampMixin, Base):
    """One scanned purchase receipt: raw OCR text plus the LLM-extracted structured fields.

    user_id is nullable - an anonymous shopper can still scan a receipt and get the structured JSON back,
    it just isn't saved to any history (see receipt_scanner.scan_receipt)."""
    __tablename__ = "receipts"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    store_name: Mapped[str | None] = mapped_column(String(160))
    purchase_date: Mapped[date | None] = mapped_column(Date)
    subtotal_minor: Mapped[int | None] = mapped_column(Integer)
    tax_minor: Mapped[int | None] = mapped_column(Integer)
    total_minor: Mapped[int | None] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    warranty_text: Mapped[str | None] = mapped_column(Text)
    warranty_expires_at: Mapped[date | None] = mapped_column(Date)
    warranty_alert_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_ocr_text: Mapped[str] = mapped_column(Text, nullable=False)
    ocr_confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    image_hash: Mapped[str | None] = mapped_column(String(64))
    items: Mapped[list["ReceiptItem"]] = relationship(back_populates="receipt", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("user_id", "image_hash", name="uq_receipts_user_image_hash"),)


class ReceiptItem(Base):
    """One line item parsed from a scanned receipt."""
    __tablename__ = "receipt_items"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    receipt_id: Mapped[UUID] = mapped_column(ForeignKey("receipts.id", ondelete="CASCADE"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(300), nullable=False)
    price_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    receipt: Mapped[Receipt] = relationship(back_populates="items")


class SearchQuery(Base):
    """One recorded shopper search. Embedded once at write time (see services/personalization.log_search) so the
    personalized recommendation engine never has to re-call the embedding API when building a user's taste vector."""
    __tablename__ = "search_queries"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    query: Mapped[str] = mapped_column(String(300), nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ProductClick(Base):
    """One recorded shopper click/view of a product - the lowest-intent personalization signal."""
    __tablename__ = "product_clicks"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    product: Mapped[Product] = relationship()


class Purchase(Base):
    """One recorded shopper purchase - the strongest-intent personalization signal."""
    __tablename__ = "purchases"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    price_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    product: Mapped[Product] = relationship()


class ChatRole(str, enum.Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatConversation(Base):
    """One RAG chat thread; groups turns so the assistant can see recent history, not just the latest question."""
    __tablename__ = "chat_conversations"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(160))
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="conversation", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    """One turn in a conversation; `metadata_` holds the retrieved-source citations for assistant turns."""
    __tablename__ = "chat_messages"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[ChatRole] = mapped_column(SAEnum(ChatRole, name="chat_role", create_type=False, values_callable=lambda enum_cls: [member.value for member in enum_cls]), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    conversation: Mapped[ChatConversation] = relationship(back_populates="messages")
