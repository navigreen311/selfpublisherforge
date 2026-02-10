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
)

# Apply enhanced configuration (routing, queues, serialisation, etc.)
celery_app.conf.update(**CELERY_CONFIG)

# Register Celery Beat schedule
celery_app.conf.beat_schedule = CELERY_BEAT_SCHEDULE

# Import task modules so @celery_app.task decorators are registered.
# These imports must come after celery_app is created to avoid circular imports.
import app.tasks.pricing_automation  # noqa: E402, F401
