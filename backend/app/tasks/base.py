"""Base task classes with tracking, multi-tenancy, and AI cost awareness."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, cast

from celery import Task

from app.tasks.config import get_retry_policy

logger = logging.getLogger(__name__)


class TrackedTask(Task):
    """Base task that logs start/end/error, tracks duration, and injects a correlation ID.

    Every task invocation receives a ``correlation_id`` in its headers.  If the
    caller does not supply one, the task generates its own.  Subclasses may
    override ``on_tracked_start`` / ``on_tracked_success`` / ``on_tracked_failure``
    hooks for custom behaviour without losing the tracking logic.
    """

    abstract = True
    _start_time: float | None = None

    # ------------------------------------------------------------------
    # Celery lifecycle hooks
    # ------------------------------------------------------------------
    def before_start(self, task_id: str, args: tuple, kwargs: dict) -> None:
        self._start_time = time.monotonic()
        self._correlation_id = (
            self.request.get("correlation_id")
            or (self.request.headers or {}).get("correlation_id")
            or str(uuid.uuid4())
        )
        logger.info(
            "Task STARTED  | task=%s id=%s correlation_id=%s args=%s",
            self.name,
            task_id,
            self._correlation_id,
            args,
        )
        self.on_tracked_start(task_id, args, kwargs)

    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict) -> None:
        duration = self._elapsed()
        logger.info(
            "Task SUCCESS  | task=%s id=%s correlation_id=%s duration=%.3fs",
            self.name,
            task_id,
            getattr(self, "_correlation_id", "N/A"),
            duration,
        )
        self.on_tracked_success(retval, task_id, args, kwargs, duration)

    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any) -> None:
        duration = self._elapsed()
        logger.error(
            "Task FAILED   | task=%s id=%s correlation_id=%s duration=%.3fs error=%s",
            self.name,
            task_id,
            getattr(self, "_correlation_id", "N/A"),
            duration,
            str(exc),
        )
        self.on_tracked_failure(exc, task_id, args, kwargs, einfo, duration)

    # ------------------------------------------------------------------
    # Extension hooks (override in subclasses)
    # ------------------------------------------------------------------
    def on_tracked_start(self, task_id: str, args: tuple, kwargs: dict) -> None:
        """Called after tracking data is initialised."""

    def on_tracked_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict, duration: float) -> None:
        """Called after a successful task completion."""

    def on_tracked_failure(
        self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: Any, duration: float
    ) -> None:
        """Called after a task failure."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @property
    def correlation_id(self) -> str:
        return getattr(self, "_correlation_id", "N/A")

    def _elapsed(self) -> float:
        if self._start_time is None:
            return 0.0
        return time.monotonic() - self._start_time

    def apply_retry_policy(self, exc: Exception, **extra_kwargs: Any) -> None:
        """Retry the current task using the retry policy from ``tasks.config``."""
        policy = get_retry_policy(self.name or "")
        self.retry(
            exc=exc,
            max_retries=policy["max_retries"],
            countdown=self._backoff_countdown(policy),
            **extra_kwargs,
        )

    def _backoff_countdown(self, policy: dict) -> int:
        """Calculate exponential backoff countdown based on current retry number."""
        retries = self.request.retries or 0
        base = 60  # 1-minute base
        return cast("int", min(base * (2**retries), policy.get("retry_backoff_max", 300)))


class OrgScopedTask(TrackedTask):
    """Task that carries ``org_id`` context for multi-tenant isolation.

    Workers MUST pass ``org_id`` as the first positional argument or as a keyword
    argument so downstream code can enforce tenant scoping.
    """

    abstract = True

    def before_start(self, task_id: str, args: tuple, kwargs: dict) -> None:
        super().before_start(task_id, args, kwargs)
        self._org_id = kwargs.get("org_id") or (args[0] if args else None)
        if self._org_id is None:
            logger.warning(
                "OrgScopedTask %s invoked WITHOUT org_id — tenant isolation may be broken",
                self.name,
            )

    @property
    def org_id(self) -> str | None:
        return getattr(self, "_org_id", None)


class AITask(OrgScopedTask):
    """Task specialised for AI / LLM workloads.

    Provides token tracking, cost calculation, and budget-checking helpers.
    """

    abstract = True

    # Cost per 1 000 tokens (USD) — override per model as needed
    COST_PER_1K_INPUT_TOKENS: float = 0.003
    COST_PER_1K_OUTPUT_TOKENS: float = 0.015

    def before_start(self, task_id: str, args: tuple, kwargs: dict) -> None:
        super().before_start(task_id, args, kwargs)
        self._input_tokens: int = 0
        self._output_tokens: int = 0

    # ------------------------------------------------------------------
    # Token tracking helpers
    # ------------------------------------------------------------------
    def record_tokens(self, input_tokens: int, output_tokens: int) -> None:
        """Accumulate token usage for the current invocation."""
        self._input_tokens += input_tokens
        self._output_tokens += output_tokens

    @property
    def total_input_tokens(self) -> int:
        return getattr(self, "_input_tokens", 0)

    @property
    def total_output_tokens(self) -> int:
        return getattr(self, "_output_tokens", 0)

    def calculate_cost(self) -> float:
        """Return estimated cost in USD for the tokens consumed so far."""
        input_cost = (self.total_input_tokens / 1000) * self.COST_PER_1K_INPUT_TOKENS
        output_cost = (self.total_output_tokens / 1000) * self.COST_PER_1K_OUTPUT_TOKENS
        return round(input_cost + output_cost, 6)

    def check_budget(self, budget_usd: float) -> bool:
        """Return ``True`` if current cost is within the given budget."""
        return self.calculate_cost() <= budget_usd

    def on_tracked_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict, duration: float) -> None:
        logger.info(
            "AITask TOKENS | task=%s id=%s input=%d output=%d cost=$%.6f",
            self.name,
            task_id,
            self.total_input_tokens,
            self.total_output_tokens,
            self.calculate_cost(),
        )
