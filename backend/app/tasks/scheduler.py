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
        "task": "app.tasks.analytics.refresh_market_data",
        "schedule": schedule(run_every=6 * 60 * 60),
        "options": {"queue": "analytics_queue"},
    },
    # ------------------------------------------------------------------
    # Analytics aggregation — daily at 02:00 UTC
    # ------------------------------------------------------------------
    "analytics-daily-aggregation": {
        "task": "app.tasks.analytics.aggregate_daily_analytics",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "analytics_queue"},
    },
    # ------------------------------------------------------------------
    # KDP health check — every 4 hours
    # ------------------------------------------------------------------
    "kdp-health-check": {
        "task": "app.tasks.production_pipeline.check_deadlines",
        "schedule": schedule(run_every=4 * 60 * 60),
        "options": {"queue": "default"},
    },
    # ------------------------------------------------------------------
    # Stale session cleanup — daily at 03:00 UTC
    # ------------------------------------------------------------------
    "stale-session-cleanup": {
        "task": "app.tasks.notifications.cleanup_stale_sessions",
        "schedule": crontab(hour=3, minute=0),
        "options": {"queue": "default"},
    },
    # ------------------------------------------------------------------
    # Usage meter reset — 1st of every month at 00:00 UTC
    # ------------------------------------------------------------------
    "usage-meter-monthly-reset": {
        "task": "app.tasks.analytics.reset_usage_meters",
        "schedule": crontab(day_of_month=1, hour=0, minute=0),
        "options": {"queue": "analytics_queue"},
    },
    # ------------------------------------------------------------------
    # Market Intelligence — refresh categories, BSR history, snapshots
    # ------------------------------------------------------------------
    "market-refresh-categories": {
        "task": "app.tasks.market_intelligence.refresh_category_data",
        "schedule": crontab(hour=1, minute=0),
        "options": {"queue": "analytics_queue"},
    },
    "market-update-bsr-history": {
        "task": "app.tasks.market_intelligence.update_bsr_history",
        "schedule": schedule(run_every=4 * 60 * 60),
        "options": {"queue": "analytics_queue"},
    },
    "market-generate-snapshot": {
        "task": "app.tasks.market_intelligence.generate_market_snapshot",
        "schedule": crontab(hour=6, minute=0),
        "options": {"queue": "analytics_queue"},
    },
    # ------------------------------------------------------------------
    # Production Pipeline — deadline check every hour
    # ------------------------------------------------------------------
    "pipeline-deadline-check": {
        "task": "app.tasks.production_pipeline.check_deadlines",
        "schedule": crontab(minute=0),
        "options": {"queue": "default"},
    },
    # ------------------------------------------------------------------
    # Pricing Automation — promotions lifecycle every 15 min
    # ------------------------------------------------------------------
    "activate-scheduled-promotions": {
        "task": "app.tasks.pricing_automation.activate_scheduled_promotions",
        "schedule": schedule(run_every=15 * 60),
        "options": {"queue": "default"},
    },
    "complete-expired-promotions": {
        "task": "app.tasks.pricing_automation.complete_expired_promotions",
        "schedule": schedule(run_every=15 * 60),
        "options": {"queue": "default"},
    },
    # ------------------------------------------------------------------
    # Competitor Finder — alerts every hour
    # ------------------------------------------------------------------
    "check-competitor-alerts-hourly": {
        "task": "app.tasks.competitor_finder.check_competitor_alerts",
        "schedule": crontab(minute=0),
        "options": {"queue": "analytics_queue"},
    },
    # ------------------------------------------------------------------
    # Marketing — emails, social posts, ARC follow-ups
    # ------------------------------------------------------------------
    "marketing-send-scheduled-emails": {
        "task": "app.tasks.marketing.send_scheduled_emails",
        "schedule": crontab(minute=0),
        "options": {"queue": "email_queue"},
    },
    "marketing-social-post-reminders": {
        "task": "app.tasks.marketing.send_social_post_reminders",
        "schedule": schedule(run_every=6 * 60 * 60),
        "options": {"queue": "email_queue"},
    },
    "marketing-arc-follow-ups": {
        "task": "app.tasks.marketing.send_arc_follow_ups",
        "schedule": crontab(hour=10, minute=0),
        "options": {"queue": "email_queue"},
    },
    # ------------------------------------------------------------------
    # Advertising — performance sync, bid optimization, budget alerts
    # ------------------------------------------------------------------
    "sync-ad-performance-hourly": {
        "task": "app.tasks.advertising.sync_performance",
        "schedule": crontab(minute=0),
        "options": {"queue": "default"},
    },
    "auto-optimize-bids-daily": {
        "task": "app.tasks.advertising.auto_optimize",
        "schedule": crontab(hour=4, minute=0),
        "options": {"queue": "default"},
    },
    "check-budget-alerts-every-4h": {
        "task": "app.tasks.advertising.budget_alerts",
        "schedule": schedule(run_every=4 * 60 * 60),
        "options": {"queue": "default"},
    },
    # ------------------------------------------------------------------
    # Review Intelligence — analyze pending reviews, velocity snapshots
    # ------------------------------------------------------------------
    "review-analyze-pending-hourly": {
        "task": "app.tasks.review_intelligence.analyze_pending_reviews",
        "schedule": crontab(minute=30),
        "options": {"queue": "analytics_queue"},
    },
    "review-velocity-snapshots-daily": {
        "task": "app.tasks.review_intelligence.compute_velocity_snapshots",
        "schedule": crontab(hour=5, minute=0),
        "options": {"queue": "analytics_queue"},
    },
    # ------------------------------------------------------------------
    # Analytics — daily metric aggregation
    # ------------------------------------------------------------------
    "daily-metric-aggregation": {
        "task": "app.tasks.analytics.aggregate_daily_metrics",
        "schedule": crontab(hour=2, minute=30),
        "options": {"queue": "analytics_queue"},
    },
}
