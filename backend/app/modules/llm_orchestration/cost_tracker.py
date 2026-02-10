"""
Cost Tracker

Tracks token consumption and USD cost per model per request.
Manages per-org budgets with configurable alert thresholds (50/75/90/100%).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

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


class CostTracker:
    """Calculates cost, records usage, and enforces per-org budgets."""

    def __init__(self) -> None:
        self._pricing = dict(MODEL_PRICING)
        # In-memory budget store (will be backed by DB table in production)
        self._budgets: dict[str, OrgBudget] = {}
        self._usage_log: list[UsageRecord] = []

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

    def record_usage(
        self,
        org_id: str,
        model_id: str,
        task_type: str,
        input_tokens: int,
        output_tokens: int,
    ) -> UsageRecord:
        """Record a usage event and return the computed record."""
        cost = self.calculate_cost(model_id, input_tokens, output_tokens)
        record = UsageRecord(
            org_id=org_id,
            model_id=model_id,
            task_type=task_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )
        self._usage_log.append(record)

        # Update org budget
        budget = self._get_or_create_budget(org_id)
        budget.spent_usd = round(budget.spent_usd + cost, 6)
        budget.alert_level = self._evaluate_alert_level(budget)

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
        """Return aggregated usage stats for an org."""
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
