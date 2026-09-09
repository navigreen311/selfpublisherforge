"""Tests for Celery task queue configuration, registration, and behavior.

Validates:
  - Celery app creation and configuration
  - Task autodiscovery via ``conf.include``
  - Beat schedule entries
  - Retry policy resolution
  - Dead letter queue operations
  - Base task class behaviour (TrackedTask lifecycle)
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# 1. Celery app is properly created and configured
# ---------------------------------------------------------------------------


class TestCeleryAppConfig:

    def test_celery_app_exists_and_has_correct_name(self):
        """The Celery app must be importable and named 'selfpublisherforge'."""
        from app.tasks import celery_app

        assert celery_app is not None
        assert celery_app.main == "selfpublisherforge"

    def test_celery_config_values(self):
        """Key configuration values must be applied from CELERY_CONFIG."""
        from app.tasks import celery_app

        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.accept_content == ["json"]
        assert celery_app.conf.timezone == "UTC"
        assert celery_app.conf.enable_utc is True
        assert celery_app.conf.task_track_started is True
        assert celery_app.conf.task_acks_late is True
        assert celery_app.conf.task_reject_on_worker_lost is True
        assert celery_app.conf.worker_prefetch_multiplier == 1

    def test_celery_app_has_include_list(self):
        """All task modules must be listed in conf.include for autodiscovery."""
        from app.tasks import celery_app

        include = celery_app.conf.include
        assert isinstance(include, list)

        expected_modules = [
            "app.tasks.advertising",
            "app.tasks.agent_system",
            "app.tasks.analytics",
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
        ]
        for mod in expected_modules:
            assert mod in include, f"Module {mod} missing from celery_app.conf.include"


# ---------------------------------------------------------------------------
# 2. Beat schedule has expected entries
# ---------------------------------------------------------------------------


class TestBeatSchedule:

    def test_beat_schedule_is_dict(self):
        from app.tasks import celery_app

        assert isinstance(celery_app.conf.beat_schedule, dict)

    def test_beat_schedule_entries_have_required_keys(self):
        """Every beat schedule entry must have at least 'task' and 'schedule'."""
        from app.tasks import celery_app

        for name, entry in celery_app.conf.beat_schedule.items():
            assert "task" in entry, f"Beat entry '{name}' missing 'task' key"
            assert "schedule" in entry, f"Beat entry '{name}' missing 'schedule' key"

    def test_beat_schedule_contains_core_entries(self):
        """The central scheduler must contain the expected periodic tasks."""
        from app.tasks.scheduler import CELERY_BEAT_SCHEDULE

        assert "market-data-refresh" in CELERY_BEAT_SCHEDULE
        assert "analytics-daily-aggregation" in CELERY_BEAT_SCHEDULE
        assert "stale-session-cleanup" in CELERY_BEAT_SCHEDULE
        assert "usage-meter-monthly-reset" in CELERY_BEAT_SCHEDULE


# ---------------------------------------------------------------------------
# 3. Retry policy resolution
# ---------------------------------------------------------------------------


class TestRetryPolicy:

    def test_ai_task_policy_resolves(self):
        from app.tasks.config import get_retry_policy

        policy = get_retry_policy("app.tasks.ai_tasks.generate")
        assert policy["max_retries"] == 3
        assert policy["retry_backoff_max"] == 600

    def test_email_task_policy_resolves(self):
        from app.tasks.config import get_retry_policy

        policy = get_retry_policy("app.tasks.email_tasks.send")
        assert policy["max_retries"] == 5

    def test_unknown_task_gets_default_policy(self):
        from app.tasks.config import RETRY_POLICIES, get_retry_policy

        policy = get_retry_policy("app.tasks.unknown_module.do_stuff")
        assert policy == RETRY_POLICIES["default"]


# ---------------------------------------------------------------------------
# 4. Queue and exchange definitions
# ---------------------------------------------------------------------------


class TestQueueConfig:

    def test_task_queues_defined(self):
        from app.tasks.config import TASK_QUEUES

        queue_names = {q.name for q in TASK_QUEUES}
        assert "default" in queue_names
        assert "ai_queue" in queue_names
        assert "email_queue" in queue_names
        assert "file_queue" in queue_names
        assert "analytics_queue" in queue_names
        assert "dead_letter_queue" in queue_names

    def test_task_routes_defined(self):
        from app.tasks.config import TASK_ROUTES

        assert len(TASK_ROUTES) >= 4
        # AI tasks should route to ai_queue
        ai_route = TASK_ROUTES.get("app.tasks.ai_tasks.*", {})
        assert ai_route.get("queue") == "ai_queue"


# ---------------------------------------------------------------------------
# 5. Dead letter queue operations
# ---------------------------------------------------------------------------


class TestDeadLetterQueue:

    def _make_redis_mock(self):
        mock = MagicMock()
        pipe = MagicMock()
        pipe.execute = MagicMock(return_value=[True, True])
        mock.pipeline.return_value = pipe
        return mock

    def test_add_and_get_dead_letter(self):
        from app.tasks.dead_letter import DeadLetter, DeadLetterQueue

        dl = DeadLetter(
            source_type="task",
            source_name="test.task",
            payload={"key": "value"},
            error_message="test error",
            error_type="RuntimeError",
        )

        redis_mock = self._make_redis_mock()
        redis_mock.get = MagicMock(return_value=json.dumps(dl.to_dict()))

        dlq = DeadLetterQueue(redis_mock)
        dl_id = dlq.add(dl)
        assert dl_id == dl.id

        result = dlq.get(dl.id)
        assert result is not None
        assert result.source_name == "test.task"
        assert result.error_message == "test error"

    def test_dead_letter_serialization_roundtrip(self):
        from app.tasks.dead_letter import DeadLetter

        dl = DeadLetter(
            source_type="event",
            source_name="user.registered",
            payload={"user_id": "abc"},
            error_message="failed",
            error_type="ValueError",
            retry_count=1,
            max_retries=3,
            org_id="org-1",
            correlation_id="corr-2",
        )
        data = dl.to_dict()
        restored = DeadLetter.from_dict(data)

        assert restored.id == dl.id
        assert restored.source_name == dl.source_name
        assert restored.payload == dl.payload
        assert restored.org_id == dl.org_id

    def test_mark_retried_updates_status(self):
        from app.tasks.dead_letter import DeadLetter, DeadLetterQueue

        dl = DeadLetter(
            source_type="task",
            source_name="t1",
            error_message="err",
        )
        redis_mock = self._make_redis_mock()
        redis_mock.get = MagicMock(return_value=json.dumps(dl.to_dict()))

        dlq = DeadLetterQueue(redis_mock)
        result = dlq.mark_retried(dl.id)

        assert result is True
        saved = json.loads(redis_mock.set.call_args[0][1])
        assert saved["status"] == "retried"


# ---------------------------------------------------------------------------
# 6. TrackedTask lifecycle
# ---------------------------------------------------------------------------


class TestTrackedTaskLifecycle:

    def _build_task(self, cls, **kwargs):

        task = cls.__new__(cls)
        task.name = kwargs.pop("task_name", "test.task")

        mock_req = MagicMock()
        mock_req.retries = kwargs.get("retries", 0)
        mock_req.get = lambda key, default=None: {
            "correlation_id": kwargs.get("correlation_id")
        }.get(key, default)
        mock_req.headers = kwargs.get("headers", {})

        object.__setattr__(task, "_request", mock_req)
        type(task).request = property(lambda self: self._request)
        return task

    def test_tracked_task_sets_start_time(self):
        from app.tasks.base import TrackedTask

        task = self._build_task(TrackedTask)
        task.before_start("tid", (), {})
        assert task._start_time is not None
        assert task._elapsed() >= 0

    def test_tracked_task_generates_correlation_id(self):
        import uuid

        from app.tasks.base import TrackedTask

        task = self._build_task(TrackedTask)
        task.before_start("tid", (), {})
        # Should be a valid UUID
        uid = uuid.UUID(task.correlation_id)
        assert uid.version == 4

    def test_ai_task_token_tracking(self):
        from app.tasks.base import AITask

        task = self._build_task(AITask)
        task.before_start("tid", ("org-1",), {})
        task.record_tokens(500, 200)
        task.record_tokens(500, 300)

        assert task.total_input_tokens == 1000
        assert task.total_output_tokens == 500

        cost = task.calculate_cost()
        expected = (1000 / 1000) * 0.003 + (500 / 1000) * 0.015
        assert abs(cost - expected) < 1e-6

    def test_ai_task_budget_check(self):
        from app.tasks.base import AITask

        task = self._build_task(AITask)
        task.before_start("tid", ("org-1",), {})
        task.record_tokens(100, 50)

        assert task.check_budget(1.0) is True
        assert task.check_budget(0.0) is False


# ---------------------------------------------------------------------------
# 7. Module-specific task files don't mutate beat_schedule directly
# ---------------------------------------------------------------------------


class TestModuleScheduleIsolation:

    def test_advertising_exports_schedule_dict(self):
        """advertising.py should export a dict, not mutate celery_app.conf."""
        from app.tasks.advertising import ADVERTISING_BEAT_SCHEDULE

        assert isinstance(ADVERTISING_BEAT_SCHEDULE, dict)
        assert len(ADVERTISING_BEAT_SCHEDULE) >= 1

    def test_analytics_exports_schedule_dict(self):
        from app.tasks.analytics import ANALYTICS_BEAT_SCHEDULE

        assert isinstance(ANALYTICS_BEAT_SCHEDULE, dict)
        assert len(ANALYTICS_BEAT_SCHEDULE) >= 1

    def test_competitor_finder_exports_schedule_dict(self):
        from app.tasks.competitor_finder import CELERY_BEAT_SCHEDULE

        assert isinstance(CELERY_BEAT_SCHEDULE, dict)

    def test_market_intelligence_exports_schedule_dict(self):
        from app.tasks.market_intelligence import CELERY_BEAT_SCHEDULE

        assert isinstance(CELERY_BEAT_SCHEDULE, dict)
