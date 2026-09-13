"""Unit tests for TrackedTask, OrgScopedTask, and AITask base classes."""

from __future__ import annotations

import time
import uuid
from unittest.mock import MagicMock, patch

from app.tasks.base import AITask, OrgScopedTask, TrackedTask
from app.tasks.config import RETRY_POLICIES, get_retry_policy

# ---------------------------------------------------------------------------
# Helpers — lightweight stubs for Celery's Task internals
# ---------------------------------------------------------------------------


def _make_request(retries: int = 0, headers: dict | None = None, correlation_id: str | None = None):
    """Create a mock Celery request object."""
    req = MagicMock()
    req.retries = retries
    req.get = lambda key, default=None: {"correlation_id": correlation_id}.get(key, default)
    req.headers = headers or {}
    return req


def _build_task(cls, task_name: str = "app.tasks.test_task", **kwargs):
    """Instantiate a task class with the ``request`` property monkey-patched."""
    task = cls.__new__(cls)
    task.name = task_name
    # Celery's Task.request is a property — we override it at instance level
    # by patching the class attribute temporarily is fragile, so instead we
    # store the mock in a private attr and override ``request`` via __dict__
    # Celery 5.x uses _default_request / _request internally.  The simplest
    # reliable approach: patch the class property for the lifetime of the test.
    mock_req = _make_request(**kwargs)
    # Use object.__setattr__ to bypass the descriptor protocol
    object.__setattr__(task, "_request", mock_req)
    # Monkey-patch the class temporarily so that `self.request` returns our mock
    type(task).request = property(lambda self: self._request)
    return task


# ========================================================================
# TrackedTask
# ========================================================================


class TestTrackedTask:
    def test_before_start_sets_correlation_id_from_request(self):
        task = _build_task(TrackedTask, correlation_id="corr-123")
        task.before_start("tid-1", ("a",), {})

        assert task.correlation_id == "corr-123"

    def test_before_start_generates_correlation_id_when_missing(self):
        task = _build_task(TrackedTask)
        task.before_start("tid-2", (), {})

        # Should be a valid UUID4
        uid = uuid.UUID(task.correlation_id)
        assert uid.version == 4

    def test_before_start_uses_header_correlation_id(self):
        task = _build_task(TrackedTask, headers={"correlation_id": "hdr-456"})
        task.before_start("tid-3", (), {})

        assert task.correlation_id == "hdr-456"

    def test_on_success_calculates_duration(self):
        task = _build_task(TrackedTask)
        task.before_start("tid-4", (), {})
        # Simulate some work
        time.sleep(0.01)
        # Should not raise
        task.on_success("result", "tid-4", (), {})

    def test_on_failure_logs_error(self):
        task = _build_task(TrackedTask)
        task.before_start("tid-5", (), {})

        exc = ValueError("boom")
        task.on_failure(exc, "tid-5", (), {}, None)
        # No assertion beyond "doesn't raise" — logging is the side-effect

    def test_elapsed_zero_when_not_started(self):
        task = _build_task(TrackedTask)
        task._start_time = None
        assert task._elapsed() == 0.0

    def test_backoff_countdown_increases_with_retries(self):
        policy = RETRY_POLICIES["default"]
        task = _build_task(TrackedTask)

        # Retry 0
        task.request.retries = 0
        cd0 = task._backoff_countdown(policy)

        # Retry 2
        task.request.retries = 2
        cd2 = task._backoff_countdown(policy)

        assert cd2 > cd0

    def test_backoff_countdown_respects_max(self):
        policy = {"retry_backoff_max": 120}
        task = _build_task(TrackedTask)
        task.request.retries = 10  # very high
        cd = task._backoff_countdown(policy)
        assert cd <= 120


# ========================================================================
# OrgScopedTask
# ========================================================================


class TestOrgScopedTask:
    def test_extracts_org_id_from_kwargs(self):
        task = _build_task(OrgScopedTask)
        task.before_start("tid-10", (), {"org_id": "org-abc"})

        assert task.org_id == "org-abc"

    def test_extracts_org_id_from_first_arg(self):
        task = _build_task(OrgScopedTask)
        task.before_start("tid-11", ("org-xyz",), {})

        assert task.org_id == "org-xyz"

    def test_warns_when_org_id_missing(self):
        task = _build_task(OrgScopedTask)
        with patch("app.tasks.base.logger") as mock_logger:
            task.before_start("tid-12", (), {})
            mock_logger.warning.assert_called_once()

        assert task.org_id is None

    def test_inherits_correlation_id_tracking(self):
        task = _build_task(OrgScopedTask, correlation_id="corr-org")
        task.before_start("tid-13", ("org-1",), {})

        assert task.correlation_id == "corr-org"
        assert task.org_id == "org-1"


# ========================================================================
# AITask
# ========================================================================


class TestAITask:
    def test_record_tokens_accumulates(self):
        task = _build_task(AITask)
        task.before_start("tid-20", ("org-ai",), {})

        task.record_tokens(100, 50)
        task.record_tokens(200, 100)

        assert task.total_input_tokens == 300
        assert task.total_output_tokens == 150

    def test_calculate_cost_basic(self):
        task = _build_task(AITask)
        task.before_start("tid-21", ("org-ai",), {})
        task.record_tokens(1000, 1000)

        cost = task.calculate_cost()
        expected = (1000 / 1000) * 0.003 + (1000 / 1000) * 0.015
        assert abs(cost - expected) < 1e-6

    def test_calculate_cost_zero_tokens(self):
        task = _build_task(AITask)
        task.before_start("tid-22", ("org-ai",), {})

        assert task.calculate_cost() == 0.0

    def test_check_budget_within(self):
        task = _build_task(AITask)
        task.before_start("tid-23", ("org-ai",), {})
        task.record_tokens(1000, 1000)

        assert task.check_budget(1.0) is True

    def test_check_budget_exceeded(self):
        task = _build_task(AITask)
        task.before_start("tid-24", ("org-ai",), {})
        task.record_tokens(1_000_000, 1_000_000)

        assert task.check_budget(0.001) is False

    def test_on_tracked_success_logs_token_info(self):
        task = _build_task(AITask)
        task.before_start("tid-25", ("org-ai",), {})
        task.record_tokens(500, 250)

        with patch("app.tasks.base.logger") as mock_logger:
            task.on_tracked_success("result", "tid-25", ("org-ai",), {}, 1.5)
            # Verify the AI-specific log message was emitted
            mock_logger.info.assert_called()
            log_msg = mock_logger.info.call_args[0][0]
            assert "TOKENS" in log_msg

    def test_custom_cost_rates(self):
        task = _build_task(AITask)
        task.COST_PER_1K_INPUT_TOKENS = 0.01
        task.COST_PER_1K_OUTPUT_TOKENS = 0.03
        task.before_start("tid-26", ("org-ai",), {})
        task.record_tokens(2000, 1000)

        cost = task.calculate_cost()
        expected = (2000 / 1000) * 0.01 + (1000 / 1000) * 0.03
        assert abs(cost - expected) < 1e-6


# ========================================================================
# Retry policy lookup
# ========================================================================


class TestRetryPolicy:
    def test_ai_task_policy(self):
        policy = get_retry_policy("app.tasks.ai_tasks.generate_content")
        assert policy["max_retries"] == 3
        assert policy["retry_backoff_max"] == 600

    def test_email_task_policy(self):
        policy = get_retry_policy("app.tasks.email_tasks.send_welcome")
        assert policy["max_retries"] == 5

    def test_file_task_policy(self):
        policy = get_retry_policy("app.tasks.file_tasks.convert_pdf")
        assert policy["max_retries"] == 3
        assert policy["retry_jitter"] is False

    def test_analytics_task_policy(self):
        policy = get_retry_policy("app.tasks.analytics_tasks.aggregate")
        assert policy["max_retries"] == 2

    def test_unknown_task_gets_default(self):
        policy = get_retry_policy("app.tasks.something_random.do_stuff")
        assert policy == RETRY_POLICIES["default"]
