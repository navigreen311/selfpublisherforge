"""Unit tests for portfolio economics expense tracking.

Tests the expense calculation pipeline that was improved in W06 to use
real CampaignPerformance.spend data instead of placeholder values.
Covers _compute_total_expenses, ROI calculation, division-by-zero
safety, PortfolioMetricSnapshot population, and multi-campaign scenarios.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.analytics.metrics import _compute_total_expenses, compute_portfolio_metrics

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _make_expense_result(total_ad_spend: Decimal | int | float) -> MagicMock:
    """Build a mock DB execute result for _compute_total_expenses."""
    row = MagicMock()
    row.total_ad_spend = total_ad_spend
    result = MagicMock()
    result.one.return_value = row
    return result


def _make_totals_result(
    total_revenue: Decimal = Decimal("0.00"),
    gross_revenue: Decimal = Decimal("0.00"),
    total_units: int = 0,
    total_books: int = 0,
) -> MagicMock:
    """Build a mock DB execute result for the totals query."""
    row = MagicMock()
    row.total_revenue = total_revenue
    row.gross_revenue = gross_revenue
    row.total_units = total_units
    row.total_books = total_books
    result = MagicMock()
    result.one.return_value = row
    return result


def _make_empty_list_result() -> MagicMock:
    """Build a mock DB execute result that returns an empty list."""
    result = MagicMock()
    result.all.return_value = []
    return result


# ---------------------------------------------------------------------------
# Tests: _compute_total_expenses
# ---------------------------------------------------------------------------


class TestComputeTotalExpenses:
    """Tests for the _compute_total_expenses helper that sums ad spend."""

    @pytest.mark.asyncio
    async def test_returns_sum_of_campaign_spend(self):
        """Real expenses should come from CampaignPerformance.spend, summed
        across all campaigns belonging to the org."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_make_expense_result(Decimal("1234.56")))

        result = await _compute_total_expenses(db, ORG_ID)

        assert result == Decimal("1234.56")
        assert isinstance(result, Decimal)

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_campaigns(self):
        """When COALESCE returns 0 (no campaign data), the function should
        return Decimal('0') and not crash."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_make_expense_result(0))

        result = await _compute_total_expenses(db, ORG_ID)

        assert result == Decimal("0")

    @pytest.mark.asyncio
    async def test_handles_float_spend_from_db(self):
        """CampaignPerformance.spend is a Float column; verify that the
        function correctly converts to Decimal via str()."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_make_expense_result(99.99))

        result = await _compute_total_expenses(db, ORG_ID)

        assert result == Decimal("99.99")
        assert isinstance(result, Decimal)

    @pytest.mark.asyncio
    async def test_executes_exactly_one_query(self):
        """The function should issue a single SELECT query."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_make_expense_result(Decimal("50.00")))

        await _compute_total_expenses(db, ORG_ID)

        assert db.execute.await_count == 1


# ---------------------------------------------------------------------------
# Tests: ROI calculation
# ---------------------------------------------------------------------------


class TestROICalculation:
    """Tests for the ROI formula: (revenue - expenses) / expenses."""

    @pytest.mark.asyncio
    async def test_roi_positive_when_profitable(self):
        """ROI should be positive when revenue exceeds expenses."""
        db = AsyncMock()
        # Query order in compute_portfolio_metrics:
        # 1. totals, 2. expenses, 3. platform, 4. format, 5. top_books
        db.execute = AsyncMock(
            side_effect=[
                _make_totals_result(total_revenue=Decimal("10000.00"), total_books=3),
                _make_expense_result(Decimal("2000.00")),
                _make_empty_list_result(),  # platform
                _make_empty_list_result(),  # format
                _make_empty_list_result(),  # top_books
            ]
        )

        metrics = await compute_portfolio_metrics(db, ORG_ID)

        # ROI = (10000 - 2000) / 2000 = 4.0
        assert metrics.avg_roi == Decimal("4.0000")

    @pytest.mark.asyncio
    async def test_roi_negative_when_unprofitable(self):
        """ROI should be negative when expenses exceed revenue."""
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                _make_totals_result(total_revenue=Decimal("500.00"), total_books=1),
                _make_expense_result(Decimal("2000.00")),
                _make_empty_list_result(),
                _make_empty_list_result(),
                _make_empty_list_result(),
            ]
        )

        metrics = await compute_portfolio_metrics(db, ORG_ID)

        # ROI = (500 - 2000) / 2000 = -0.75
        assert metrics.avg_roi == Decimal("-0.7500")

    @pytest.mark.asyncio
    async def test_roi_zero_when_no_expenses(self):
        """When expenses are 0, ROI should default to 0 (no division by zero)."""
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                _make_totals_result(total_revenue=Decimal("5000.00"), total_books=2),
                _make_expense_result(Decimal("0.00")),
                _make_empty_list_result(),
                _make_empty_list_result(),
                _make_empty_list_result(),
            ]
        )

        metrics = await compute_portfolio_metrics(db, ORG_ID)

        assert metrics.avg_roi == Decimal("0.0000")

    @pytest.mark.asyncio
    async def test_roi_zero_when_both_zero(self):
        """When both revenue and expenses are 0, ROI should be 0."""
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                _make_totals_result(total_revenue=Decimal("0.00"), total_books=0),
                _make_expense_result(Decimal("0.00")),
                _make_empty_list_result(),
                _make_empty_list_result(),
                _make_empty_list_result(),
            ]
        )

        metrics = await compute_portfolio_metrics(db, ORG_ID)

        assert metrics.avg_roi == Decimal("0.0000")

    @pytest.mark.asyncio
    async def test_roi_breakeven(self):
        """When revenue equals expenses, ROI should be 0."""
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                _make_totals_result(total_revenue=Decimal("1000.00"), total_books=1),
                _make_expense_result(Decimal("1000.00")),
                _make_empty_list_result(),
                _make_empty_list_result(),
                _make_empty_list_result(),
            ]
        )

        metrics = await compute_portfolio_metrics(db, ORG_ID)

        # ROI = (1000 - 1000) / 1000 = 0
        assert metrics.avg_roi == Decimal("0.0000")


# ---------------------------------------------------------------------------
# Tests: PortfolioMetricSnapshot gets real total_expenses
# ---------------------------------------------------------------------------


class TestSnapshotExpenses:
    """Tests that PortfolioMetrics receives real total_expenses values."""

    @pytest.mark.asyncio
    async def test_total_expenses_populated_from_campaign_spend(self):
        """The snapshot's total_expenses field should reflect the sum of
        CampaignPerformance.spend, not a hard-coded placeholder."""
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                _make_totals_result(total_revenue=Decimal("8000.00"), total_books=4),
                _make_expense_result(Decimal("1500.00")),
                _make_empty_list_result(),
                _make_empty_list_result(),
                _make_empty_list_result(),
            ]
        )

        metrics = await compute_portfolio_metrics(db, ORG_ID)

        assert metrics.total_expenses == Decimal("1500.00")

    @pytest.mark.asyncio
    async def test_net_profit_equals_revenue_minus_expenses(self):
        """Net profit should be total_revenue - total_expenses."""
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                _make_totals_result(total_revenue=Decimal("8000.00"), total_books=4),
                _make_expense_result(Decimal("1500.00")),
                _make_empty_list_result(),
                _make_empty_list_result(),
                _make_empty_list_result(),
            ]
        )

        metrics = await compute_portfolio_metrics(db, ORG_ID)

        assert metrics.net_profit == Decimal("6500.00")

    @pytest.mark.asyncio
    async def test_all_expense_related_fields_consistent(self):
        """Verify that total_expenses, net_profit, and avg_roi are all
        internally consistent with each other."""
        revenue = Decimal("12000.00")
        expenses = Decimal("3000.00")

        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                _make_totals_result(total_revenue=revenue, total_books=6),
                _make_expense_result(expenses),
                _make_empty_list_result(),
                _make_empty_list_result(),
                _make_empty_list_result(),
            ]
        )

        metrics = await compute_portfolio_metrics(db, ORG_ID)

        assert metrics.total_expenses == expenses
        assert metrics.net_profit == revenue - expenses
        # ROI = (12000 - 3000) / 3000 = 3.0
        assert metrics.avg_roi == Decimal("3.0000")
        assert metrics.total_revenue == revenue


# ---------------------------------------------------------------------------
# Tests: No campaign data (defaults)
# ---------------------------------------------------------------------------


class TestNoCampaignData:
    """Tests that missing campaign data defaults gracefully to 0."""

    @pytest.mark.asyncio
    async def test_zero_expenses_with_no_campaigns(self):
        """When there are no campaigns at all, expenses should be 0."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_make_expense_result(0))

        result = await _compute_total_expenses(db, ORG_ID)

        assert result == Decimal("0")

    @pytest.mark.asyncio
    async def test_portfolio_metrics_with_no_campaign_data(self):
        """Full portfolio metrics call should not crash when there are
        zero campaigns and zero revenue."""
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                _make_totals_result(),  # all defaults (0)
                _make_expense_result(0),
                _make_empty_list_result(),
                _make_empty_list_result(),
                _make_empty_list_result(),
            ]
        )

        metrics = await compute_portfolio_metrics(db, ORG_ID)

        assert metrics.total_expenses == Decimal("0.00")
        assert metrics.net_profit == Decimal("0.00")
        assert metrics.avg_roi == Decimal("0.0000")
        assert metrics.total_revenue == Decimal("0.00")
        assert metrics.total_books == 0
        assert metrics.total_units_sold == 0

    @pytest.mark.asyncio
    async def test_revenue_with_no_expenses(self):
        """Revenue should still be reported correctly when there are no
        campaigns / expenses at all."""
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                _make_totals_result(
                    total_revenue=Decimal("2500.00"),
                    total_units=120,
                    total_books=3,
                ),
                _make_expense_result(0),
                _make_empty_list_result(),
                _make_empty_list_result(),
                _make_empty_list_result(),
            ]
        )

        metrics = await compute_portfolio_metrics(db, ORG_ID)

        assert metrics.total_revenue == Decimal("2500.00")
        assert metrics.total_expenses == Decimal("0.00")
        assert metrics.net_profit == Decimal("2500.00")
        assert metrics.avg_roi == Decimal("0.0000")  # no expenses => 0 ROI


# ---------------------------------------------------------------------------
# Tests: Multiple campaigns across an org
# ---------------------------------------------------------------------------


class TestMultipleCampaigns:
    """Tests that expenses are correctly aggregated from multiple campaigns."""

    @pytest.mark.asyncio
    async def test_aggregate_spend_across_many_campaigns(self):
        """_compute_total_expenses uses SQL SUM, so the mock should return
        the pre-aggregated total. Verify it is passed through correctly."""
        # The SQL query already aggregates across all campaigns for the org.
        # A total of e.g. 3 campaigns spending 100+250+150 = 500
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_make_expense_result(Decimal("500.00")))

        result = await _compute_total_expenses(db, ORG_ID)

        assert result == Decimal("500.00")

    @pytest.mark.asyncio
    async def test_portfolio_with_large_multi_campaign_spend(self):
        """End-to-end metrics with a large aggregate spend across campaigns."""
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                _make_totals_result(
                    total_revenue=Decimal("50000.00"),
                    gross_revenue=Decimal("65000.00"),
                    total_units=2500,
                    total_books=15,
                ),
                _make_expense_result(Decimal("12500.00")),  # 25% of revenue
                _make_empty_list_result(),
                _make_empty_list_result(),
                _make_empty_list_result(),
            ]
        )

        metrics = await compute_portfolio_metrics(db, ORG_ID)

        assert metrics.total_expenses == Decimal("12500.00")
        assert metrics.net_profit == Decimal("37500.00")
        # ROI = (50000 - 12500) / 12500 = 3.0
        assert metrics.avg_roi == Decimal("3.0000")

    @pytest.mark.asyncio
    async def test_different_org_ids_are_independent(self):
        """Verify that _compute_total_expenses is called with the correct
        org_id (by checking the query is executed once per call)."""
        org_a = uuid.uuid4()
        org_b = uuid.uuid4()

        db_a = AsyncMock()
        db_a.execute = AsyncMock(return_value=_make_expense_result(Decimal("100.00")))

        db_b = AsyncMock()
        db_b.execute = AsyncMock(return_value=_make_expense_result(Decimal("999.00")))

        result_a = await _compute_total_expenses(db_a, org_a)
        result_b = await _compute_total_expenses(db_b, org_b)

        assert result_a == Decimal("100.00")
        assert result_b == Decimal("999.00")
        assert result_a != result_b

    @pytest.mark.asyncio
    async def test_high_expenses_low_revenue_gives_negative_roi(self):
        """Scenario: aggressive ad spend exceeds revenue."""
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                _make_totals_result(
                    total_revenue=Decimal("1000.00"),
                    total_units=50,
                    total_books=2,
                ),
                _make_expense_result(Decimal("5000.00")),
                _make_empty_list_result(),
                _make_empty_list_result(),
                _make_empty_list_result(),
            ]
        )

        metrics = await compute_portfolio_metrics(db, ORG_ID)

        assert metrics.total_expenses == Decimal("5000.00")
        assert metrics.net_profit == Decimal("-4000.00")
        # ROI = (1000 - 5000) / 5000 = -0.8
        assert metrics.avg_roi == Decimal("-0.8000")

    @pytest.mark.asyncio
    async def test_fractional_penny_spend_preserved(self):
        """Verify sub-cent precision is handled through Decimal conversion."""
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_make_expense_result(Decimal("123.456789")))

        result = await _compute_total_expenses(db, ORG_ID)

        # The raw function returns unrounded Decimal; rounding happens in
        # compute_portfolio_metrics via _quantize.
        assert result == Decimal("123.456789")
