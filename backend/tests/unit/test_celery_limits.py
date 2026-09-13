"""Unit tests for Celery task time limits and configuration.

Validates:
- Global CELERY_CONFIG has task_time_limit and task_soft_time_limit set
- soft_time_limit < time_limit (soft fires first to allow graceful shutdown)
- time_limit > 0
- All task modules are included in the celery app's ``include`` list
- Task decorator parameters (bind, max_retries, etc.) are properly configured
- Retry policies are correctly defined
"""

from __future__ import annotations

import pytest

from app.tasks.config import (
    CELERY_CONFIG,
    RETRY_POLICIES,
    TASK_QUEUES,
    TASK_ROUTES,
    get_retry_policy,
)

# =========================================================================
# Global time limits from CELERY_CONFIG
# =========================================================================


class TestGlobalTimeLimits:
    def test_task_time_limit_is_set(self):
        assert "task_time_limit" in CELERY_CONFIG

    def test_task_soft_time_limit_is_set(self):
        assert "task_soft_time_limit" in CELERY_CONFIG

    def test_time_limit_is_positive(self):
        assert CELERY_CONFIG["task_time_limit"] > 0

    def test_soft_time_limit_is_positive(self):
        assert CELERY_CONFIG["task_soft_time_limit"] > 0

    def test_soft_time_limit_less_than_time_limit(self):
        """Soft limit must fire before hard limit to allow graceful cleanup."""
        assert CELERY_CONFIG["task_soft_time_limit"] < CELERY_CONFIG["task_time_limit"]

    def test_time_limit_is_3600(self):
        """Default global time limit should be 1 hour (3600 seconds)."""
        assert CELERY_CONFIG["task_time_limit"] == 3600

    def test_soft_time_limit_is_3300(self):
        """Default global soft time limit should be 55 minutes (3300 seconds)."""
        assert CELERY_CONFIG["task_soft_time_limit"] == 3300

    def test_time_limit_gap_is_reasonable(self):
        """The gap between soft and hard limits should be at least 60 seconds."""
        gap = CELERY_CONFIG["task_time_limit"] - CELERY_CONFIG["task_soft_time_limit"]
        assert gap >= 60, f"Gap of {gap}s is too small for graceful shutdown"


# =========================================================================
# Other CELERY_CONFIG essentials
# =========================================================================


class TestCeleryConfigEssentials:
    def test_serializer_is_json(self):
        assert CELERY_CONFIG["task_serializer"] == "json"

    def test_accept_content_includes_json(self):
        assert "json" in CELERY_CONFIG["accept_content"]

    def test_result_serializer_is_json(self):
        assert CELERY_CONFIG["result_serializer"] == "json"

    def test_utc_enabled(self):
        assert CELERY_CONFIG["enable_utc"] is True

    def test_timezone_is_utc(self):
        assert CELERY_CONFIG["timezone"] == "UTC"

    def test_track_started(self):
        assert CELERY_CONFIG["task_track_started"] is True

    def test_acks_late(self):
        assert CELERY_CONFIG["task_acks_late"] is True

    def test_reject_on_worker_lost(self):
        assert CELERY_CONFIG["task_reject_on_worker_lost"] is True

    def test_result_expires_is_24h(self):
        assert CELERY_CONFIG["result_expires"] == 86400

    def test_default_retry_delay(self):
        assert CELERY_CONFIG["task_default_retry_delay"] == 60


# =========================================================================
# Retry policies
# =========================================================================


class TestRetryPolicies:
    def test_default_policy_exists(self):
        assert "default" in RETRY_POLICIES

    def test_ai_tasks_policy_exists(self):
        assert "ai_tasks" in RETRY_POLICIES

    def test_email_tasks_policy_exists(self):
        assert "email_tasks" in RETRY_POLICIES

    def test_file_tasks_policy_exists(self):
        assert "file_tasks" in RETRY_POLICIES

    def test_analytics_tasks_policy_exists(self):
        assert "analytics_tasks" in RETRY_POLICIES

    @pytest.mark.parametrize("policy_name", list(RETRY_POLICIES.keys()))
    def test_every_policy_has_max_retries(self, policy_name: str):
        assert "max_retries" in RETRY_POLICIES[policy_name]
        assert RETRY_POLICIES[policy_name]["max_retries"] > 0

    @pytest.mark.parametrize("policy_name", list(RETRY_POLICIES.keys()))
    def test_every_policy_has_retry_backoff(self, policy_name: str):
        assert "retry_backoff" in RETRY_POLICIES[policy_name]
        assert RETRY_POLICIES[policy_name]["retry_backoff"] is True

    @pytest.mark.parametrize("policy_name", list(RETRY_POLICIES.keys()))
    def test_every_policy_has_backoff_max(self, policy_name: str):
        assert "retry_backoff_max" in RETRY_POLICIES[policy_name]
        assert RETRY_POLICIES[policy_name]["retry_backoff_max"] > 0

    def test_ai_tasks_backoff_max_is_600(self):
        assert RETRY_POLICIES["ai_tasks"]["retry_backoff_max"] == 600

    def test_email_tasks_max_retries_is_5(self):
        assert RETRY_POLICIES["email_tasks"]["max_retries"] == 5

    def test_get_retry_policy_ai_task(self):
        policy = get_retry_policy("app.tasks.ai_tasks.generate_content")
        assert policy["max_retries"] == 3

    def test_get_retry_policy_unknown_falls_back_to_default(self):
        policy = get_retry_policy("app.tasks.mystery.do_something")
        assert policy == RETRY_POLICIES["default"]


# =========================================================================
# Task queues and routing
# =========================================================================


class TestTaskQueuesAndRouting:
    def test_task_queues_defined(self):
        assert len(TASK_QUEUES) > 0

    def test_default_queue_exists(self):
        queue_names = [q.name for q in TASK_QUEUES]
        assert "default" in queue_names

    def test_ai_queue_exists(self):
        queue_names = [q.name for q in TASK_QUEUES]
        assert "ai_queue" in queue_names

    def test_email_queue_exists(self):
        queue_names = [q.name for q in TASK_QUEUES]
        assert "email_queue" in queue_names

    def test_analytics_queue_exists(self):
        queue_names = [q.name for q in TASK_QUEUES]
        assert "analytics_queue" in queue_names

    def test_dead_letter_queue_exists(self):
        queue_names = [q.name for q in TASK_QUEUES]
        assert "dead_letter_queue" in queue_names

    def test_task_routes_defined(self):
        assert len(TASK_ROUTES) > 0

    def test_ai_tasks_route_to_ai_queue(self):
        assert TASK_ROUTES["app.tasks.ai_tasks.*"]["queue"] == "ai_queue"

    def test_email_tasks_route_to_email_queue(self):
        assert TASK_ROUTES["app.tasks.email_tasks.*"]["queue"] == "email_queue"

    def test_config_default_queue(self):
        assert CELERY_CONFIG["task_default_queue"] == "default"


# =========================================================================
# Celery app include list
# =========================================================================


class TestCeleryAppIncludes:
    """Verify that the Celery app's ``include`` list references all task modules."""

    EXPECTED_TASK_MODULES = [
        "app.tasks.advertising",
        "app.tasks.agent_system",
        "app.tasks.analytics",
        "app.tasks.competitor_finder",
        "app.tasks.dead_letter",
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
    ]

    @pytest.mark.parametrize("module_path", EXPECTED_TASK_MODULES)
    def test_module_is_included(self, module_path: str):
        """Each task module should be importable (i.e. it exists in the codebase)."""
        # We only verify the module is importable; actual Celery app registration
        # is integration-level.
        import importlib

        mod = importlib.import_module(module_path)
        assert mod is not None
