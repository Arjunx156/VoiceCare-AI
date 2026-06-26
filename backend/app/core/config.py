"""
CommerceMind VoiceCare AI — Application Configuration
Loads environment variables with validation via Pydantic Settings.
"""

from functools import lru_cache
from typing import Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_REQUIRED_IN_PRODUCTION = ["database_url", "gemini_api_key", "nextauth_secret"]


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- App ----
    app_name: str = "CommerceMind VoiceCare AI"
    environment: str = "development"
    log_level: str = "INFO"
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"

    # ---- Database (Neon Postgres) ----
    database_url: str = "postgresql+asyncpg://localhost/voicecare"
    database_url_sync: str = "postgresql://localhost/voicecare"

    # ---- Gemini ----
    gemini_api_key: str = ""

    # ---- Bhashini ----
    bhashini_user_id: str = ""
    bhashini_api_key: str = ""
    bhashini_pipeline_url: str = "https://dhruva-api.bhashini.gov.in/services/inference"

    # ---- Groq ----
    groq_api_key: str = ""

    # ---- Chroma ----
    chroma_persist_dir: str = "./chroma_data"

    # ---- Auth ----
    nextauth_secret: str = "dev-secret-change-in-production"
    admin_email: str = "admin@voicecare.ai"
    admin_password: str = "change_this_in_production"

    # ---- Upstash Redis (durable multi-turn memory) ----
    upstash_redis_rest_url: Optional[str] = None
    upstash_redis_rest_token: Optional[str] = None

    # ---- Observability ----
    sentry_dsn: Optional[str] = None  # set to enable Sentry error tracking

    # ---- Rate Limiting ----
    gemini_max_retries: int = 3
    gemini_base_delay: float = 1.0
    bhashini_timeout: float = 30.0
    voice_rate_limit_per_minute: int = 5  # max voice queries per phone per minute

    # ----------------------------------------------------------------
    # Validators
    # ----------------------------------------------------------------

    @field_validator("admin_password")
    @classmethod
    def validate_admin_password(cls, v: str, info) -> str:
        """Prevent default/weak passwords in production deployments."""
        environment = (info.data or {}).get("environment", "development")
        if "change_this" in v.lower() and environment == "production":
            raise ValueError(
                "Admin password must be changed from the default value in production!"
            )
        return v

    @model_validator(mode="after")
    def validate_required_secrets(self) -> "Settings":
        """Fail fast in production if critical secrets are empty."""
        if self.environment == "production":
            missing = [
                k for k in _REQUIRED_IN_PRODUCTION
                if not getattr(self, k, None)
            ]
            if missing:
                raise ValueError(
                    f"Required secrets not set for production: {', '.join(missing)}"
                )
        return self

    # ----------------------------------------------------------------
    # Computed properties
    # ----------------------------------------------------------------

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def allowed_origins(self) -> list[str]:
        """Narrow CORS origin list based on environment."""
        if self.is_production:
            return [self.frontend_url]
        return [self.frontend_url, "http://localhost:3000", "http://localhost:3001"]


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
