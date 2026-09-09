"""
Unit tests for cost tracking, token counting, and per-org budget management.

Verifies USD cost calculation, usage recording, budget thresholds,
and alert levels at 50/75/90/100%.
"""

from unittest.mock import AsyncMock

import pytest

from app.modules.llm_orchestration.cost_tracker import (
    MODEL_PRICING,
    BudgetAlertLevel,
    CostTracker,
    OrgBudget,
)
from app.modules.llm_orchestration.router_config import ModelID

# -------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------

@pytest.fixture
def tracker() -> CostTracker:
    """Return a CostTracker with Redis persistence disabled."""
    t = CostTracker()
    # Prevent _get_redis from attempting a real connection;
    # _persist_to_redis will see client=None and skip Redis writes.
    t._get_redis = AsyncMock(return_value=None)
    return t


@pytest.fixture
def org_id() -> str:
    return "org-test-001"


# -------------------------------------------------------------------
# Cost calculation
# -------------------------------------------------------------------

class TestCostCalculation:
    """Verify per-model token cost calculations."""

    def test_claude_opus_cost(self, tracker: CostTracker):
        # 1000 input + 1000 output
        cost = tracker.calculate_cost(ModelID.CLAUDE_OPUS.value, 1000, 1000)
        pricing = MODEL_PRICING[ModelID.CLAUDE_OPUS.value]
        expected = pricing.input_cost_per_1k + pricing.output_cost_per_1k
        assert cost == pytest.approx(expected, abs=1e-6)

    def test_claude_haiku_cost(self, tracker: CostTracker):
        cost = tracker.calculate_cost(ModelID.CLAUDE_HAIKU.value, 1000, 1000)
        pricing = MODEL_PRICING[ModelID.CLAUDE_HAIKU.value]
        expected = pricing.input_cost_per_1k + pricing.output_cost_per_1k
        assert cost == pytest.approx(expected, abs=1e-6)

    def test_gpt4_mini_cost(self, tracker: CostTracker):
        cost = tracker.calculate_cost(ModelID.GPT_4_MINI.value, 1000, 1000)
        pricing = MODEL_PRICING[ModelID.GPT_4_MINI.value]
        expected = pricing.input_cost_per_1k + pricing.output_cost_per_1k
        assert cost == pytest.approx(expected, abs=1e-6)

    def test_zero_tokens_zero_cost(self, tracker: CostTracker):
        cost = tracker.calculate_cost(ModelID.CLAUDE_SONNET.value, 0, 0)
        assert cost == 0.0

    def test_unknown_model_returns_zero(self, tracker: CostTracker):
        cost = tracker.calculate_cost("unknown-model", 1000, 1000)
        assert cost == 0.0

    def test_cost_scales_linearly(self, tracker: CostTracker):
        cost_1k = tracker.calculate_cost(ModelID.CLAUDE_SONNET.value, 1000, 1000)
        cost_2k = tracker.calculate_cost(ModelID.CLAUDE_SONNET.value, 2000, 2000)
        assert cost_2k == pytest.approx(cost_1k * 2, abs=1e-6)

    def test_opus_more_expensive_than_haiku(self, tracker: CostTracker):
        opus_cost = tracker.calculate_cost(ModelID.CLAUDE_OPUS.value, 1000, 1000)
        haiku_cost = tracker.calculate_cost(ModelID.CLAUDE_HAIKU.value, 1000, 1000)
        assert opus_cost > haiku_cost

    def test_all_models_have_pricing(self):
        for model_id in ModelID:
            assert model_id.value in MODEL_PRICING, f"Missing pricing for {model_id}"


# -------------------------------------------------------------------
# Usage recording
# -------------------------------------------------------------------

class TestUsageRecording:
    """Verify that usage records are created and budgets updated."""

    async def test_record_creates_entry(self, tracker: CostTracker, org_id: str):
        record = await tracker.record_usage(
            org_id=org_id,
            model_id=ModelID.CLAUDE_SONNET.value,
            task_type="blurb_ad_copy",
            input_tokens=500,
            output_tokens=200,
        )
        assert record.org_id == org_id
        assert record.model_id == ModelID.CLAUDE_SONNET.value
        assert record.input_tokens == 500
        assert record.output_tokens == 200
        assert record.cost_usd > 0

    async def test_multiple_records_accumulate_cost(self, tracker: CostTracker, org_id: str):
        await tracker.record_usage(org_id, ModelID.CLAUDE_SONNET.value, "test", 1000, 1000)
        await tracker.record_usage(org_id, ModelID.CLAUDE_SONNET.value, "test", 1000, 1000)
        budget = tracker.get_budget(org_id)
        single_cost = tracker.calculate_cost(ModelID.CLAUDE_SONNET.value, 1000, 1000)
        assert budget.spent_usd == pytest.approx(single_cost * 2, abs=1e-6)

    async def test_usage_summary_aggregation(self, tracker: CostTracker, org_id: str):
        await tracker.record_usage(org_id, ModelID.CLAUDE_HAIKU.value, "review", 500, 100)
        await tracker.record_usage(org_id, ModelID.CLAUDE_SONNET.value, "blurb", 800, 300)
        summary = tracker.get_usage_summary(org_id)
        assert summary["request_count"] == 2
        assert summary["total_input_tokens"] == 1300
        assert summary["total_output_tokens"] == 400
        assert summary["total_cost_usd"] > 0

    async def test_usage_summary_filter_by_model(self, tracker: CostTracker, org_id: str):
        await tracker.record_usage(org_id, ModelID.CLAUDE_HAIKU.value, "review", 500, 100)
        await tracker.record_usage(org_id, ModelID.CLAUDE_SONNET.value, "blurb", 800, 300)
        summary = tracker.get_usage_summary(org_id, model_id=ModelID.CLAUDE_HAIKU.value)
        assert summary["request_count"] == 1
        assert summary["total_input_tokens"] == 500


# -------------------------------------------------------------------
# Budget management
# -------------------------------------------------------------------

class TestBudgetManagement:
    """Verify per-org budget tracking and checks."""

    def test_default_budget(self, tracker: CostTracker, org_id: str):
        budget = tracker.get_budget(org_id)
        assert budget.monthly_budget_usd == 100.0
        assert budget.spent_usd == 0.0

    def test_set_budget(self, tracker: CostTracker, org_id: str):
        tracker.set_budget(org_id, 500.0)
        budget = tracker.get_budget(org_id)
        assert budget.monthly_budget_usd == 500.0

    def test_check_budget_within_limit(self, tracker: CostTracker, org_id: str):
        tracker.set_budget(org_id, 100.0)
        assert tracker.check_budget(org_id, estimated_cost=50.0) is True

    def test_check_budget_exceeds_limit(self, tracker: CostTracker, org_id: str):
        tracker.set_budget(org_id, 100.0)
        assert tracker.check_budget(org_id, estimated_cost=150.0) is False

    async def test_remaining_budget_decreases(self, tracker: CostTracker, org_id: str):
        tracker.set_budget(org_id, 10.0)
        await tracker.record_usage(org_id, ModelID.CLAUDE_OPUS.value, "test", 1000, 1000)
        budget = tracker.get_budget(org_id)
        assert budget.remaining_usd < 10.0

    async def test_remaining_never_negative(self, tracker: CostTracker, org_id: str):
        tracker.set_budget(org_id, 0.001)
        await tracker.record_usage(org_id, ModelID.CLAUDE_OPUS.value, "test", 10000, 10000)
        budget = tracker.get_budget(org_id)
        assert budget.remaining_usd >= 0.0


# -------------------------------------------------------------------
# Alert levels
# -------------------------------------------------------------------

class TestAlertLevels:
    """Verify budget alert thresholds at 50/75/90/100%."""

    def test_no_alert_at_zero_spend(self, tracker: CostTracker, org_id: str):
        tracker.set_budget(org_id, 100.0)
        assert tracker.get_alert_level(org_id) == BudgetAlertLevel.NONE

    async def test_no_alert_below_50_percent(self, tracker: CostTracker, org_id: str):
        tracker.set_budget(org_id, 100.0)
        # Spend ~$0.018 per call (Sonnet 1k/1k)
        # Need to stay below $50
        for _ in range(10):
            await tracker.record_usage(org_id, ModelID.CLAUDE_SONNET.value, "test", 1000, 1000)
        assert tracker.get_alert_level(org_id) == BudgetAlertLevel.NONE

    async def test_warning_at_50_percent(self, tracker: CostTracker, org_id: str):
        tracker.set_budget(org_id, 1.0)
        # Spend enough to hit ~50%
        # Opus: $0.015 input + $0.075 output = $0.09 per 1K each
        # 6 calls => ~$0.54 => 54%
        for _ in range(6):
            await tracker.record_usage(org_id, ModelID.CLAUDE_OPUS.value, "test", 1000, 1000)
        level = tracker.get_alert_level(org_id)
        assert level == BudgetAlertLevel.WARNING_50

    async def test_warning_at_75_percent(self, tracker: CostTracker, org_id: str):
        tracker.set_budget(org_id, 1.0)
        # 9 Opus calls => ~$0.81 => 81%
        for _ in range(9):
            await tracker.record_usage(org_id, ModelID.CLAUDE_OPUS.value, "test", 1000, 1000)
        level = tracker.get_alert_level(org_id)
        assert level == BudgetAlertLevel.WARNING_75

    async def test_critical_at_90_percent(self, tracker: CostTracker, org_id: str):
        tracker.set_budget(org_id, 1.0)
        # 10 Opus calls => ~$0.90 => 90%
        for _ in range(10):
            await tracker.record_usage(org_id, ModelID.CLAUDE_OPUS.value, "test", 1000, 1000)
        level = tracker.get_alert_level(org_id)
        assert level == BudgetAlertLevel.CRITICAL_90

    async def test_exceeded_at_100_percent(self, tracker: CostTracker, org_id: str):
        tracker.set_budget(org_id, 1.0)
        # 12 Opus calls => ~$1.08 => 108%
        for _ in range(12):
            await tracker.record_usage(org_id, ModelID.CLAUDE_OPUS.value, "test", 1000, 1000)
        level = tracker.get_alert_level(org_id)
        assert level == BudgetAlertLevel.EXCEEDED_100

    async def test_budget_check_false_when_exceeded(self, tracker: CostTracker, org_id: str):
        tracker.set_budget(org_id, 0.01)
        await tracker.record_usage(org_id, ModelID.CLAUDE_OPUS.value, "test", 1000, 1000)
        assert tracker.check_budget(org_id) is False


# -------------------------------------------------------------------
# OrgBudget dataclass
# -------------------------------------------------------------------

class TestOrgBudget:
    """Test OrgBudget property calculations."""

    def test_usage_ratio(self):
        budget = OrgBudget(org_id="test", monthly_budget_usd=100.0, spent_usd=50.0)
        assert budget.usage_ratio == pytest.approx(0.5)

    def test_usage_ratio_zero_budget(self):
        budget = OrgBudget(org_id="test", monthly_budget_usd=0.0, spent_usd=10.0)
        assert budget.usage_ratio == 1.0

    def test_remaining_usd(self):
        budget = OrgBudget(org_id="test", monthly_budget_usd=100.0, spent_usd=30.0)
        assert budget.remaining_usd == pytest.approx(70.0)
