"""Celery application factory with enhanced routing, queues, and scheduling."""
from celery import Celery
from app.config import get_settings
from app.tasks.config import CELERY_CONFIG
from app.tasks.scheduler import CELERY_BEAT_SCHEDULE

settings = get_settings()

celery_app = Celery(
    "selfpublisherforge",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.advertising",
        "app.tasks.analytics",
        "app.tasks.agent_system",
        "app.tasks.competitor_finder",
        "app.tasks.knowledge_vault",
        "app.tasks.market_intelligence",
        "app.tasks.marketing",
        "app.tasks.notifications",
        "app.tasks.portfolio_economics",
        "app.tasks.pricing_automation",
        "app.tasks.production_pipeline",
        "app.tasks.publishing_ops",
        "app.tasks.review_intelligence",
        "app.tasks.style_cloning",
    ],
)

# Apply enhanced configuration (routing, queues, serialisation, etc.)
celery_app.conf.update(**CELERY_CONFIG)

# Register Celery Beat schedule
celery_app.conf.beat_schedule = CELERY_BEAT_SCHEDULE
