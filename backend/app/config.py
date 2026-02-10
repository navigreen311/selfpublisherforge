import os

from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    APP_NAME: str = "SelfPublisherForge"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
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
    FACEBOOK_ADS_API_VERSION: str = os.environ.get("FACEBOOK_ADS_API_VERSION", "v18.0")

    # Chrome Extension
    CHROME_EXTENSION_ID: str = os.environ.get("CHROME_EXTENSION_ID", "")

    # Market intelligence scoring midpoints (sigmoid scaling)
    MI_DEMAND_MIDPOINT: int = int(os.environ.get("MI_DEMAND_MIDPOINT", "5000"))
    MI_COMPETITION_MIDPOINT: int = int(os.environ.get("MI_COMPETITION_MIDPOINT", "50000"))
    MI_OPPORTUNITY_MIDPOINT: int = int(os.environ.get("MI_OPPORTUNITY_MIDPOINT", "500"))

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

@lru_cache
def get_settings() -> Settings:
    return Settings()
