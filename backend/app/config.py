import os
import warnings
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "SelfPublisherForge"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # "development", "staging", "production"
    API_V1_PREFIX: str = "/api/v1"
    FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "http://localhost:3000")

    # Auth
    SECRET_KEY: str = "YOUR_SECRET_KEY_HERE"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/selfpublisherforge"
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://localhost:9200"

    # Storage
    S3_BUCKET: str = "selfpublisherforge-assets"
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = "YOUR_AWS_ACCESS_KEY_HERE"
    AWS_SECRET_ACCESS_KEY: str = "YOUR_AWS_SECRET_KEY_HERE"

    # AI/LLM
    ANTHROPIC_API_KEY: str = "YOUR_ANTHROPIC_API_KEY_HERE"
    OPENAI_API_KEY: str = "YOUR_OPENAI_API_KEY_HERE"
    DEFAULT_LLM_MODEL: str = "claude-sonnet-4-5-20250929"
    AI_WORD_COUNT_MULTIPLIER: float = float(os.environ.get("AI_WORD_COUNT_MULTIPLIER", "0.5"))

    # VoiceForge TTS
    ELEVENLABS_API_KEY: str = ""
    COQUI_XTTS_ENDPOINT: str = "http://localhost:8321"
    PIPER_ENDPOINT: str = "http://localhost:8322"

    # Stripe
    STRIPE_SECRET_KEY: str = "YOUR_STRIPE_SECRET_KEY_HERE"
    STRIPE_WEBHOOK_SECRET: str = "YOUR_STRIPE_WEBHOOK_SECRET_HERE"
    STRIPE_PRICE_STARTER: str = ""
    STRIPE_PRICE_PRO: str = ""
    STRIPE_PRICE_BUSINESS: str = ""
    STRIPE_PRICE_ENTERPRISE: str = ""

    # Email — SendGrid
    SENDGRID_API_KEY: str = "YOUR_SENDGRID_API_KEY_HERE"
    FROM_EMAIL: str = "noreply@selfpublisherforge.com"

    # Email — SMTP (fallback / alternative to SendGrid)
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASS: str | None = None
    SMTP_FROM: str = "noreply@selfpublisherforge.com"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    # GitHub OAuth
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = ""

    # Amazon Ads
    AMAZON_ADS_CLIENT_ID: str = ""
    AMAZON_ADS_CLIENT_SECRET: str = ""
    AMAZON_ADS_REFRESH_TOKEN: str = ""
    AMAZON_ADS_PROFILE_ID: str = ""
    AMAZON_ADS_REGION: str = "NA"
    DEFAULT_BID_AMOUNT: float = float(os.environ.get("DEFAULT_BID_AMOUNT", "0.75"))

    # Facebook Ads
    FACEBOOK_APP_ID: str = ""
    FACEBOOK_APP_SECRET: str = ""
    FACEBOOK_ACCESS_TOKEN: str = ""
    FACEBOOK_AD_ACCOUNT_ID: str = ""
    FACEBOOK_ADS_API_VERSION: str = os.environ.get("FACEBOOK_ADS_API_VERSION", "v18.0")

    # Amazon Product Advertising API (PA-API)
    AMAZON_PAAPI_ACCESS_KEY: str = ""
    AMAZON_PAAPI_SECRET_KEY: str = ""
    AMAZON_PAAPI_PARTNER_TAG: str = ""

    # Chrome Extension
    CHROME_EXTENSION_ID: str = os.environ.get("CHROME_EXTENSION_ID", "")

    # Market intelligence scoring midpoints (sigmoid scaling)
    MI_DEMAND_MIDPOINT: int = int(os.environ.get("MI_DEMAND_MIDPOINT", "5000"))
    MI_COMPETITION_MIDPOINT: int = int(os.environ.get("MI_COMPETITION_MIDPOINT", "50000"))
    MI_OPPORTUNITY_MIDPOINT: int = int(os.environ.get("MI_OPPORTUNITY_MIDPOINT", "500"))

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------
    _PLACEHOLDER_SECRETS: dict[str, str] = {
        "SECRET_KEY": "YOUR_SECRET_KEY_HERE",
        "AWS_ACCESS_KEY_ID": "YOUR_AWS_ACCESS_KEY_HERE",
        "AWS_SECRET_ACCESS_KEY": "YOUR_AWS_SECRET_KEY_HERE",
        "ANTHROPIC_API_KEY": "YOUR_ANTHROPIC_API_KEY_HERE",
        "OPENAI_API_KEY": "YOUR_OPENAI_API_KEY_HERE",
        "STRIPE_SECRET_KEY": "YOUR_STRIPE_SECRET_KEY_HERE",
        "STRIPE_WEBHOOK_SECRET": "YOUR_STRIPE_WEBHOOK_SECRET_HERE",
        "SENDGRID_API_KEY": "YOUR_SENDGRID_API_KEY_HERE",
    }

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> "Settings":
        """Ensure no placeholder secrets remain when running in production."""
        # Dynamically include FRONTEND_URL in CORS origins
        if self.FRONTEND_URL and self.FRONTEND_URL not in self.CORS_ORIGINS:
            self.CORS_ORIGINS = [*self.CORS_ORIGINS, self.FRONTEND_URL]

        if self.ENVIRONMENT != "production":
            return self

        missing: list[str] = [
            name for name, placeholder in self._PLACEHOLDER_SECRETS.items() if getattr(self, name) == placeholder
        ]
        if missing:
            raise ValueError(
                "Production mode (ENVIRONMENT=production) requires real values for the "
                "following environment variables that still contain placeholder "
                "defaults:\n  - " + "\n  - ".join(missing)
            )
        return self

    # Optional-but-recommended fields that default to empty strings.
    # These power optional integrations (OAuth, Stripe tiers, Amazon Ads)
    # and should be configured in production for full functionality.
    _OPTIONAL_RECOMMENDED_FIELDS: list[str] = [
        # OAuth — Google
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        # OAuth — GitHub
        "GITHUB_CLIENT_ID",
        "GITHUB_CLIENT_SECRET",
        # Stripe price IDs (billing tiers)
        "STRIPE_PRICE_STARTER",
        "STRIPE_PRICE_PRO",
        "STRIPE_PRICE_BUSINESS",
        "STRIPE_PRICE_ENTERPRISE",
        # Amazon Ads
        "AMAZON_ADS_CLIENT_ID",
        "AMAZON_ADS_CLIENT_SECRET",
        # Facebook Ads
        "FACEBOOK_APP_ID",
        "FACEBOOK_APP_SECRET",
        "FACEBOOK_ACCESS_TOKEN",
        "FACEBOOK_AD_ACCOUNT_ID",
        # Amazon PA-API
        "AMAZON_PAAPI_ACCESS_KEY",
        "AMAZON_PAAPI_SECRET_KEY",
        "AMAZON_PAAPI_PARTNER_TAG",
    ]

    @model_validator(mode="after")
    def _warn_empty_optional_secrets(self) -> "Settings":
        """Warn about empty optional integration credentials in production."""
        if self.ENVIRONMENT != "production":
            return self

        empty: list[str] = [name for name in self._OPTIONAL_RECOMMENDED_FIELDS if not getattr(self, name, "")]
        if empty:
            warnings.warn(
                "Production mode: the following optional integration credentials are "
                "empty. Related features (OAuth login, Stripe billing tiers, "
                "Amazon Ads, Facebook Ads, Amazon PA-API) will be unavailable "
                "until configured:\n  - " + "\n  - ".join(empty),
                UserWarning,
                stacklevel=2,
            )
        return self

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
