"""Typed settings; environment variables are the only source of deployment configuration."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Pricewise API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    supabase_url: str
    cors_origins: str = "http://localhost:3000"
    gemini_api_key: str = ""
    tavily_api_key: str = ""
    recommendation_model: str = "gemini-3.1-flash-lite"
    embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 768
    assistant_chat_model: str = "gemini-3.1-flash-lite"
    assistant_embedding_model: str = "models/gemini-embedding-001"
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = ""
    whatsapp_app_secret: str = ""
    whatsapp_api_version: str = "v21.0"
    whatsapp_price_alert_template: str = "price_drop_alert"
    whatsapp_warranty_alert_template: str = "warranty_expiring_alert"
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        """Convert the comma-separated deployment setting into FastAPI's expected list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cache parsed configuration so each request uses consistent validated settings."""
    return Settings()
