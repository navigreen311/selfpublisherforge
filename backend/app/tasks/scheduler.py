"""Celery Beat schedule — periodic task definitions."""
from celery.schedules import crontab, schedule

# ---------------------------------------------------------------------------
# Beat Schedule
# ---------------------------------------------------------------------------
CELERY_BEAT_SCHEDULE = {
    # ------------------------------------------------------------------
    # Market data refresh — every 6 hours
    # ------------------------------------------------------------------
    "market-data-refresh": {
        "task": "app.tasks.analytics_tasks.refresh_market_data",
        "schedule": schedule(run_every=6 * 60 * 60),  # 21 600 seconds
        "options": {"queue": "analytics_queue"},
        "kwargs": {},
    },
    # ------------------------------------------------------------------
    # Analytics aggregation — daily at 02:00 UTC
    # ------------------------------------------------------------------
    "analytics-daily-aggregation": {
        "task": "app.tasks.analytics_tasks.aggregate_daily_analytics",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "analytics_queue"},
        "kwargs": {},
    },
    # ------------------------------------------------------------------
    # KDP health check — every 4 hours
    # ------------------------------------------------------------------
    "kdp-health-check": {
        "task": "app.tasks.file_tasks.kdp_health_check",
        "schedule": schedule(run_every=4 * 60 * 60),  # 14 400 seconds
        "options": {"queue": "file_queue"},
        "kwargs": {},
    },
    # ------------------------------------------------------------------
    # Stale session cleanup — daily at 03:00 UTC
    # ------------------------------------------------------------------
    "stale-session-cleanup": {
        "task": "app.tasks.email_tasks.cleanup_stale_sessions",
        "schedule": crontab(hour=3, minute=0),
        "options": {"queue": "default"},
        "kwargs": {},
    },
    # ------------------------------------------------------------------
    # Usage meter reset — 1st of every month at 00:00 UTC
    # ------------------------------------------------------------------
    "usage-meter-monthly-reset": {
        "task": "app.tasks.analytics_tasks.reset_usage_meters",
        "schedule": crontab(day_of_month=1, hour=0, minute=0),
        "options": {"queue": "analytics_queue"},
        "kwargs": {},
    },
}
