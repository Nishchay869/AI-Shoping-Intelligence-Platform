from pydantic import BaseModel, ConfigDict, Field
from app.models import BudgetTier, NotificationFrequency


class UserPreferencesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    notify_email: bool
    notify_push: bool
    notify_sms: bool
    notify_whatsapp: bool
    phone_number: str | None
    phone_verified: bool
    min_discount_percentage: float | None
    alert_all_time_low: bool
    alert_below_90d_average: bool
    notification_frequency: NotificationFrequency
    favorite_brands: list[str]
    blacklisted_brands: list[str]
    preferred_retailers: list[str]
    budget_tier: BudgetTier | None
    sizing_profile: dict[str, str]
    include_refurbished: bool
    restock_alerts_enabled: bool
    auto_buy_enabled: bool


class UpdateUserPreferencesRequest(BaseModel):
    """Every field optional - the service applies only what's actually set (`exclude_unset=True`), so a
    client can PATCH a single toggle without resending the whole preference set."""
    notify_email: bool | None = None
    notify_push: bool | None = None
    notify_sms: bool | None = None
    notify_whatsapp: bool | None = None
    min_discount_percentage: float | None = Field(default=None, ge=0, le=95)
    alert_all_time_low: bool | None = None
    alert_below_90d_average: bool | None = None
    notification_frequency: NotificationFrequency | None = None
    favorite_brands: list[str] | None = Field(default=None, max_length=50)
    blacklisted_brands: list[str] | None = Field(default=None, max_length=50)
    preferred_retailers: list[str] | None = Field(default=None, max_length=20)
    budget_tier: BudgetTier | None = None
    sizing_profile: dict[str, str] | None = None
    include_refurbished: bool | None = None
    restock_alerts_enabled: bool | None = None
    auto_buy_enabled: bool | None = None


class RequestPhoneVerification(BaseModel):
    phone_number: str = Field(min_length=6, max_length=20)


class ConfirmPhoneVerification(BaseModel):
    code: str = Field(min_length=6, max_length=6)
