"""
Cost Tracker

Tracks token consumption and USD cost per model per request.
Manages per-org budgets with configurable alert thresholds (50/75/90/100%).

Persistence is Redis-backed using atomic INCRBYFLOAT for cost accumulation.
Falls back to in-memory tracking if Redis is unavailable.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from redis.asyncio import Redis

from app.config import get_settings
from app.modules.llm_orchestration.router_config import ModelID

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------
# Per-model pricing (USD per 1K tokens) — updated as of latest public rates
# -----------------------------------------------------------------------
@dataclass(frozen=True)
class ModelPricing:
    """Cost per 1 000 tokens for a given model."""

    input_cost_per_1k: float
    output_cost_per_1k: float


MODEL_PRICING: dict[str, ModelPricing] = {
    ModelID.CLAUDE_OPUS.value: ModelPricing(
        input_cost_per_1k=0.015,
        output_cost_per_1k=0.075,
    ),
    ModelID.CLAUDE_SONNET.value: ModelPricing(
        input_cost_per_1k=0.003,
        output_cost_per_1k=0.015,
    ),
    ModelID.CLAUDE_HAIKU.value: ModelPricing(
        input_cost_per_1k=0.001,
        output_cost_per_1k=0.005,
    ),
    ModelID.GPT_4.value: ModelPricing(
        input_cost_per_1k=0.005,
        output_cost_per_1k=0.015,
    ),
    ModelID.GPT_4_MINI.value: ModelPricing(
        input_cost_per_1k=0.00015,
        output_cost_per_1k=0.0006,
    ),
}


class BudgetAlertLevel(str, Enum):
    """Alert thresholds for per-org budget tracking."""

    NONE = "none"
    WARNING_50 = "warning_50"
    WARNING_75 = "warning_75"
    CRITICAL_90 = "critical_90"
    EXCEEDED_100 = "exceeded_100"


ALERT_THRESHOLDS: list[tuple[float, BudgetAlertLevel]] = [
    (1.00, BudgetAlertLevel.EXCEEDED_100),
    (0.90, BudgetAlertLevel.CRITICAL_90),
    (0.75, BudgetAlertLevel.WARNING_75),
    (0.50, BudgetAlertLevel.WARNING_50),
]


@dataclass
class UsageRecord:
    """A single request's cost record."""

    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    org_id: str = ""
    model_id: str = ""
    task_type: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class OrgBudget:
    """Per-organization budget state."""

    org_id: str
    monthly_budget_usd: float = 100.0
    spent_usd: float = 0.0
    period_start: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
    )
    alert_level: BudgetAlertLevel = BudgetAlertLevel.NONE

    @property
    def remaining_usd(self) -> float:
        return max(self.monthly_budget_usd - self.spent_usd, 0.0)

    @property
    def usage_ratio(self) -> float:
        if self.monthly_budget_usd <= 0:
            return 1.0
        return self.spent_usd / self.monthly_budget_usd


# -----------------------------------------------------------------------
# Redis key helpers
# -----------------------------------------------------------------------
_COST_KEY_PREFIX = "llm_cost"
_DAILY_TTL_SECONDS = 90 * 86_400  # 90 days


def _daily_cost_key(org_id: str, day: date) -> str:
    """Key for aggregate daily cost: llm_cost:{org_id}:{YYYY-MM-DD}"""
    return f"{_COST_KEY_PREFIX}:{org_id}:{day.isoformat()}"


def _model_cost_key(org_id: str, day: date, model_id: str) -> str:
    """Key for per-model daily cost: llm_cost:{org_id}:{YYYY-MM-DD}:{model}"""
    return f"{_COST_KEY_PREFIX}:{org_id}:{day.isoformat()}:{model_id}"


def _tokens_input_key(org_id: str, day: date) -> str:
    return f"{_COST_KEY_PREFIX}:{org_id}:{day.isoformat()}:tokens_in"


def _tokens_output_key(org_id: str, day: date) -> str:
    return f"{_COST_KEY_PREFIX}:{org_id}:{day.isoformat()}:tokens_out"


def _request_count_key(org_id: str, day: date) -> str:
    return f"{_COST_KEY_PREFIX}:{org_id}:{day.isoformat()}:requests"


class CostTracker:
    """Calculates cost, records usage, and enforces per-org budgets.

    Primary storage is Redis (atomic INCRBYFLOAT for cost accumulation).
    Falls back to in-memory tracking if Redis is unavailable.
    """

    def __init__(self, redis_client: Optional[Redis] = None) -> None:
        self._pricing = dict(MODEL_PRICING)
        self._redis: Optional[Redis] = redis_client
        self._redis_available: bool = True

        # In-memory fallbacks (always maintained as secondary store)
        self._budgets: dict[str, OrgBudget] = {}
        self._usage_log: list[UsageRecord] = []

    async def _get_redis(self) -> Optional[Redis]:
        """Lazily initialize the Redis connection. Returns None if unavailable."""
        if self._redis is None:
            try:
                settings = get_settings()
                self._redis = Redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                )
                await self._redis.ping()
                self._redis_available = True
            except Exception:
                logger.warning(
                    "Redis connection unavailable for cost tracking — "
                    "falling back to in-memory only",
                    exc_info=True,
                )
                self._redis_available = False
                return None
        return self._redis

    # ------------------------------------------------------------------
    # Cost calculation
    # ------------------------------------------------------------------

    def calculate_cost(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Return USD cost for a given model + token counts."""
        pricing = self._pricing.get(model_id)
        if pricing is None:
            logger.warning("No pricing data for model %s, cost = 0", model_id)
            return 0.0
        cost = (
            (input_tokens / 1000) * pricing.input_cost_per_1k
            + (output_tokens / 1000) * pricing.output_cost_per_1k
        )
        return round(cost, 6)

    # ------------------------------------------------------------------
    # Usage recording
    # ------------------------------------------------------------------

    async def record_usage(
        self,
        org_id: str,
        model_id: str,
        task_type: str,
        input_tokens: int,
        output_tokens: int,
    ) -> UsageRecord:
        """Record a usage event. Persists to Redis and in-memory."""
        cost = self.calculate_cost(model_id, input_tokens, output_tokens)
        record = UsageRecord(
            org_id=org_id,
            model_id=model_id,
            task_type=task_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )

        # Always update in-memory
        self._usage_log.append(record)
        budget = self._get_or_create_budget(org_id)
        budget.spent_usd = round(budget.spent_usd + cost, 6)
        budget.alert_level = self._evaluate_alert_level(budget)

        # Persist to Redis atomically
        today = datetime.now(timezone.utc).date()
        await self._persist_to_redis(
            org_id=org_id,
            model_id=model_id,
            day=today,
            cost=cost,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        logger.info(
            "Usage recorded: org=%s model=%s tokens=%d+%d cost=$%.6f total=$%.4f/%s",
            org_id,
            model_id,
            input_tokens,
            output_tokens,
            cost,
            budget.spent_usd,
            budget.monthly_budget_usd,
        )
        return record

    async def _persist_to_redis(
        self,
        org_id: str,
        model_id: str,
        day: date,
        cost: float,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """Atomically accumulate cost and token counts in Redis."""
        try:
            client = await self._get_redis()
            if client is None:
                return

            pipe = client.pipeline(transaction=False)

            # Aggregate daily cost
            agg_key = _daily_cost_key(org_id, day)
            pipe.incrbyfloat(agg_key, cost)
            pipe.expire(agg_key, _DAILY_TTL_SECONDS)

            # Per-model daily cost
            model_key = _model_cost_key(org_id, day, model_id)
            pipe.incrbyfloat(model_key, cost)
            pipe.expire(model_key, _DAILY_TTL_SECONDS)

            # Token counters
            tin_key = _tokens_input_key(org_id, day)
            pipe.incrbyfloat(tin_key, float(input_tokens))
            pipe.expire(tin_key, _DAILY_TTL_SECONDS)

            tout_key = _tokens_output_key(org_id, day)
            pipe.incrbyfloat(tout_key, float(output_tokens))
            pipe.expire(tout_key, _DAILY_TTL_SECONDS)

            # Request count
            req_key = _request_count_key(org_id, day)
            pipe.incr(req_key)
            pipe.expire(req_key, _DAILY_TTL_SECONDS)

            await pipe.execute()
            logger.debug(
                "Redis cost persisted: org=%s day=%s cost=$%.6f model=%s",
                org_id,
                day.isoformat(),
                cost,
                model_id,
            )
        except Exception:
            logger.warning(
                "Failed to persist cost to Redis for org=%s — "
                "in-memory tracking continues",
                org_id,
                exc_info=True,
            )
            self._redis_available = False

    # ------------------------------------------------------------------
    # Cost retrieval
    # ------------------------------------------------------------------

    async def get_costs(
        self,
        org_id: str,
        start_date: date,
        end_date: date,
        model_id: Optional[str] = None,
    ) -> dict:
        """Aggregate costs from Redis for an org over a date range.

        Returns a dict with total_cost_usd, daily breakdown, total tokens,
        and request count. Falls back to in-memory data if Redis is
        unavailable.
        """
        # Try Redis first
        try:
            client = await self._get_redis()
            if client is not None:
                return await self._get_costs_from_redis(
                    client, org_id, start_date, end_date, model_id
                )
        except Exception:
            logger.warning(
                "Failed to read costs from Redis for org=%s — "
                "falling back to in-memory",
                org_id,
                exc_info=True,
            )
            self._redis_available = False

        # Fallback: aggregate from in-memory usage log
        return self._get_costs_from_memory(org_id, start_date, end_date, model_id)

    async def _get_costs_from_redis(
        self,
        client: Redis,
        org_id: str,
        start_date: date,
        end_date: date,
        model_id: Optional[str],
    ) -> dict:
        """Read cost data from Redis keys across the date range."""
        total_cost = 0.0
        total_input_tokens = 0
        total_output_tokens = 0
        total_requests = 0
        daily: list[dict] = []

        current = start_date
        while current <= end_date:
            if model_id:
                cost_key = _model_cost_key(org_id, current, model_id)
            else:
                cost_key = _daily_cost_key(org_id, current)

            tin_key = _tokens_input_key(org_id, current)
            tout_key = _tokens_output_key(org_id, current)
            req_key = _request_count_key(org_id, current)

            pipe = client.pipeline(transaction=False)
            pipe.get(cost_key)
            pipe.get(tin_key)
            pipe.get(tout_key)
            pipe.get(req_key)
            results = await pipe.execute()

            day_cost = float(results[0] or 0)
            day_tin = int(float(results[1] or 0))
            day_tout = int(float(results[2] or 0))
            day_reqs = int(results[3] or 0)

            total_cost += day_cost
            total_input_tokens += day_tin
            total_output_tokens += day_tout
            total_requests += day_reqs

            if day_cost > 0 or day_reqs > 0:
                daily.append({
                    "date": current.isoformat(),
                    "cost_usd": round(day_cost, 6),
                    "input_tokens": day_tin,
                    "output_tokens": day_tout,
                    "request_count": day_reqs,
                })

            current += timedelta(days=1)

        return {
            "org_id": org_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "model_id": model_id,
            "total_cost_usd": round(total_cost, 6),
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_requests": total_requests,
            "daily": daily,
        }

    def _get_costs_from_memory(
        self,
        org_id: str,
        start_date: date,
        end_date: date,
        model_id: Optional[str],
    ) -> dict:
        """Aggregate cost data from the in-memory usage log."""
        records = [
            r
            for r in self._usage_log
            if r.org_id == org_id
            and start_date <= r.created_at.date() <= end_date
        ]
        if model_id:
            records = [r for r in records if r.model_id == model_id]

        # Group by day
        from collections import defaultdict
        by_day: dict[date, list[UsageRecord]] = defaultdict(list)
        for r in records:
            by_day[r.created_at.date()].append(r)

        daily: list[dict] = []
        for day in sorted(by_day.keys()):
            day_records = by_day[day]
            daily.append({
                "date": day.isoformat(),
                "cost_usd": round(sum(r.cost_usd for r in day_records), 6),
                "input_tokens": sum(r.input_tokens for r in day_records),
                "output_tokens": sum(r.output_tokens for r in day_records),
                "request_count": len(day_records),
            })

        total_cost = sum(r.cost_usd for r in records)
        total_input = sum(r.input_tokens for r in records)
        total_output = sum(r.output_tokens for r in records)

        return {
            "org_id": org_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "model_id": model_id,
            "total_cost_usd": round(total_cost, 6),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_requests": len(records),
            "daily": daily,
        }

    # ------------------------------------------------------------------
    # Budget management
    # ------------------------------------------------------------------

    def set_budget(self, org_id: str, monthly_budget_usd: float) -> OrgBudget:
        """Set or update the monthly budget for an organization."""
        budget = self._get_or_create_budget(org_id)
        budget.monthly_budget_usd = monthly_budget_usd
        budget.alert_level = self._evaluate_alert_level(budget)
        return budget

    def get_budget(self, org_id: str) -> OrgBudget:
        """Return the current budget state for an org."""
        return self._get_or_create_budget(org_id)

    def check_budget(self, org_id: str, estimated_cost: float = 0.0) -> bool:
        """Return True if the org can afford the estimated cost."""
        budget = self._get_or_create_budget(org_id)
        return (budget.spent_usd + estimated_cost) <= budget.monthly_budget_usd

    def get_alert_level(self, org_id: str) -> BudgetAlertLevel:
        """Return the current alert level for an org."""
        budget = self._get_or_create_budget(org_id)
        return self._evaluate_alert_level(budget)

    def get_usage_summary(
        self,
        org_id: str,
        model_id: Optional[str] = None,
    ) -> dict:
        """Return aggregated usage stats for an org (from in-memory log)."""
        records = [r for r in self._usage_log if r.org_id == org_id]
        if model_id:
            records = [r for r in records if r.model_id == model_id]

        total_input = sum(r.input_tokens for r in records)
        total_output = sum(r.output_tokens for r in records)
        total_cost = sum(r.cost_usd for r in records)

        return {
            "org_id": org_id,
            "request_count": len(records),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cost_usd": round(total_cost, 6),
            "budget": self.get_budget(org_id).monthly_budget_usd,
            "remaining_usd": round(self.get_budget(org_id).remaining_usd, 6),
            "alert_level": self.get_alert_level(org_id).value,
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_or_create_budget(self, org_id: str) -> OrgBudget:
        if org_id not in self._budgets:
            self._budgets[org_id] = OrgBudget(org_id=org_id)
        return self._budgets[org_id]

    @staticmethod
    def _evaluate_alert_level(budget: OrgBudget) -> BudgetAlertLevel:
        """Determine the alert level from current usage ratio."""
        ratio = budget.usage_ratio
        for threshold, level in ALERT_THRESHOLDS:
            if ratio >= threshold:
                return level
        return BudgetAlertLevel.NONE
