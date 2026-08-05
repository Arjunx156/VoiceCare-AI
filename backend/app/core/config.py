"""
CommerceMind VoiceCare AI — Application Configuration
Loads environment variables with validation via Pydantic Settings.
"""

from functools import lru_cache
from typing import Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_REQUIRED_IN_PRODUCTION = ["database_url", "gemini_api_key", "nextauth_secret"]

# Known shipped defaults — any deployed environment must replace these.
DEFAULT_JWT_SECRET = "dev-secret-change-in-production"
DEFAULT_ADMIN_PASSWORD = "change_this_in_production"

# Environments where default secrets are tolerated. Anything else (production,
# staging, or an unset/typo'd ENVIRONMENT on a real deploy) is held to
# production rules.
DEV_LIKE_ENVIRONMENTS = ("development", "test")


def _is_production_like(environment: str) -> bool:
    return str(environment).lower() not in DEV_LIKE_ENVIRONMENTS


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

    # ---- Groq (Whisper STT only — no longer used as LLM fallback) ----
    groq_api_key: str = ""

    # ---- Chroma ----
    chroma_persist_dir: str = "./chroma_data"

    # ---- Auth ----
    nextauth_secret: str = DEFAULT_JWT_SECRET
    admin_email: str = "admin@voicecare.ai"
    admin_password: str = DEFAULT_ADMIN_PASSWORD

    # ---- CORS ----
    # When true, any https://*.vercel.app origin is allowed even in production.
    # Off by default (tighter), but handy when the frontend lives on a Vercel
    # preview/production URL that changes between deploys.
    cors_allow_vercel_previews: bool = False

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
    voice_rate_limit_ip_per_minute: int = 10  # per-IP cap, applies to anonymous callers too
    login_rate_limit_per_15min: int = 5  # admin login attempts per IP per 15 minutes
    ws_max_connections_per_ip: int = 3  # concurrent voice WebSocket connections per IP

    # ---- Privacy ----
    # gTTS fallback sends the response text to translate.google.com when
    # Bhashini TTS fails. Set false for privacy-sensitive deployments
    # (response is then delivered text-only when Bhashini is down).
    allow_gtts_fallback: bool = True

    # ---- Latency ----
    # The browser sends its own Web Speech API transcript alongside the audio.
    # Trusting it skips a Groq Whisper round trip (0.8-2.5s, mostly the webm
    # upload). Set false to always re-transcribe server-side if browser
    # transcript quality proves inadequate for your languages.
    trust_browser_transcript: bool = True

    # ----------------------------------------------------------------
    # Validators
    # ----------------------------------------------------------------

    @field_validator("admin_password")
    @classmethod
    def validate_admin_password(cls, v: str, info) -> str:
        """Prevent default/weak passwords in any deployed (non-dev) environment."""
        environment = (info.data or {}).get("environment", "development")
        if "change_this" in v.lower() and _is_production_like(environment):
            raise ValueError(
                "Admin password must be changed from the default value "
                f"(environment={environment!r})."
            )
        return v

    @field_validator("nextauth_secret")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        """Prevent the default dev JWT secret in any deployed (non-dev) environment."""
        environment = (info.data or {}).get("environment", "development")
        if v == DEFAULT_JWT_SECRET and _is_production_like(environment):
            raise ValueError(
                "JWT secret must be changed from the default value "
                f"(environment={environment!r}). Set NEXTAUTH_SECRET to a strong random value."
            )
        return v

    @model_validator(mode="after")
    def validate_required_secrets(self) -> "Settings":
        """Fail fast in deployed environments if critical secrets are empty."""
        if _is_production_like(self.environment):
            missing = [
                k for k in _REQUIRED_IN_PRODUCTION
                if not getattr(self, k, None)
            ]
            if missing:
                raise ValueError(
                    f"Required secrets not set for {self.environment}: {', '.join(missing)}"
                )
        return self

    # ----------------------------------------------------------------
    # Computed properties
    # ----------------------------------------------------------------

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def has_default_secrets(self) -> bool:
        """True when either shipped default secret is still configured."""
        return (
            self.nextauth_secret == DEFAULT_JWT_SECRET
            or "change_this" in self.admin_password.lower()
        )

    @property
    def allowed_origins(self) -> list[str]:
        """Narrow CORS origin list based on environment.

        `frontend_url` may be a single origin or a comma-separated list, so a
        production deployment can allow several front-ends (e.g. the canonical
        Vercel domain plus a custom domain) without re-enabling a broad wildcard.
        """
        configured = [
            o.strip().rstrip("/")
            for o in self.frontend_url.split(",")
            if o.strip()
        ]
        if self.is_production:
            return configured
        return [*configured, "http://localhost:3000", "http://localhost:3001"]


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
