"""Unit tests for analytics metrics module.

Tests portfolio metric calculations, KPI computation, trend analysis,
and helper functions.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.analytics.metrics import (
    _change_direction,
    _get_date_trunc,
    _percent_change,
    _quantize,
    compute_kpis,
    compute_portfolio_metrics,
    compute_revenue_trend,
)
from app.modules.analytics.schemas import AggregationPeriod

# ---------- Helper function tests ----------


class TestQuantize:
    def test_quantize_two_decimal_places(self):
        assert _quantize(Decimal("10.456")) == Decimal("10.46")

    def test_quantize_rounds_up(self):
        assert _quantize(Decimal("10.455")) == Decimal("10.46")

    def test_quantize_rounds_down(self):
        assert _quantize(Decimal("10.454")) == Decimal("10.45")

    def test_quantize_zero(self):
        assert _quantize(Decimal("0.00")) == Decimal("0.00")

    def test_quantize_four_places(self):
        assert _quantize(Decimal("0.12345"), places=4) == Decimal("0.1235")

    def test_quantize_large_number(self):
        assert _quantize(Decimal("123456.789")) == Decimal("123456.79")


class TestPercentChange:
    def test_positive_change(self):
        result = _percent_change(Decimal("150"), Decimal("100"))
        assert result == 50.0

    def test_negative_change(self):
        result = _percent_change(Decimal("75"), Decimal("100"))
        assert result == -25.0

    def test_no_change(self):
        result = _percent_change(Decimal("100"), Decimal("100"))
        assert result == 0.0

    def test_zero_previous(self):
        result = _percent_change(Decimal("100"), Decimal("0"))
        assert result is None

    def test_double(self):
        result = _percent_change(Decimal("200"), Decimal("100"))
        assert result == 100.0

    def test_small_values(self):
        result = _percent_change(Decimal("0.15"), Decimal("0.10"))
        assert abs(result - 50.0) < 0.01


class TestChangeDirection:
    def test_up(self):
        assert _change_direction(10.0) == "up"

    def test_down(self):
        assert _change_direction(-10.0) == "down"

    def test_flat_none(self):
        assert _change_direction(None) == "flat"

    def test_flat_small_positive(self):
        assert _change_direction(0.3) == "flat"

    def test_flat_small_negative(self):
        assert _change_direction(-0.3) == "flat"

    def test_boundary_up(self):
        assert _change_direction(0.6) == "up"

    def test_boundary_down(self):
        assert _change_direction(-0.6) == "down"


class TestGetDateTrunc:
    def test_daily(self):
        assert _get_date_trunc(AggregationPeriod.DAILY) == "day"

    def test_weekly(self):
        assert _get_date_trunc(AggregationPeriod.WEEKLY) == "week"

    def test_monthly(self):
        assert _get_date_trunc(AggregationPeriod.MONTHLY) == "month"

    def test_quarterly(self):
        assert _get_date_trunc(AggregationPeriod.QUARTERLY) == "quarter"

    def test_yearly(self):
        assert _get_date_trunc(AggregationPeriod.YEARLY) == "year"


# ---------- Integration-style unit tests with mocked DB ----------


class TestComputePortfolioMetrics:
    """Tests for compute_portfolio_metrics with mocked database."""

    @pytest.fixture
    def org_id(self):
        return uuid.uuid4()

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_returns_portfolio_metrics_structure(self, mock_db, org_id):
        """Verify that compute_portfolio_metrics returns a proper PortfolioMetrics object."""
        # Mock the totals query
        totals_row = MagicMock()
        totals_row.total_revenue = Decimal("5000.00")
        totals_row.gross_revenue = Decimal("7000.00")
        totals_row.total_units = 250
        totals_row.total_books = 5

        # Mock the platform query
        platform_row1 = MagicMock()
        platform_row1.platform = "kdp"
        platform_row1.revenue = Decimal("3000.00")
        platform_row2 = MagicMock()
        platform_row2.platform = "ingram_spark"
        platform_row2.revenue = Decimal("2000.00")

        # Mock the format query
        format_row1 = MagicMock()
        format_row1.format_type = "ebook"
        format_row1.revenue = Decimal("4000.00")
        format_row1.units = 200
        format_row2 = MagicMock()
        format_row2.format_type = "paperback"
        format_row2.revenue = Decimal("1000.00")
        format_row2.units = 50

        # Mock the top books query
        book_row1 = MagicMock()
        book_row1.title = "Best Book"
        book_row1.revenue = Decimal("2500.00")
        book_row1.units = 100

        # Mock the expenses query (called by _compute_total_expenses)
        expenses_row = MagicMock()
        expenses_row.total_ad_spend = Decimal("500.00")

        # Set up the mock to return different results for each call
        totals_result = MagicMock()
        totals_result.one.return_value = totals_row

        expenses_result = MagicMock()
        expenses_result.one.return_value = expenses_row

        platform_result = MagicMock()
        platform_result.all.return_value = [platform_row1, platform_row2]

        format_result = MagicMock()
        format_result.all.return_value = [format_row1, format_row2]

        top_books_result = MagicMock()
        top_books_result.all.return_value = [book_row1]

        mock_db.execute = AsyncMock(
            side_effect=[totals_result, expenses_result, platform_result, format_result, top_books_result]
        )

        result = await compute_portfolio_metrics(mock_db, org_id)

        assert result.total_books == 5
        assert result.total_revenue == Decimal("5000.00")
        assert result.total_units_sold == 250
        assert "kdp" in result.platform_breakdown
        assert "ebook" in result.format_breakdown
        assert len(result.top_books) == 1
        assert result.top_books[0]["title"] == "Best Book"


class TestComputeKPIs:
    """Tests for compute_kpis with mocked database."""

    @pytest.fixture
    def org_id(self):
        return uuid.uuid4()

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_returns_four_kpi_cards(self, mock_db, org_id):
        """Verify that compute_kpis returns exactly 4 KPI cards."""
        now = datetime.now(UTC)
        period_start = now - timedelta(days=30)
        period_end = now

        # Current period
        current_row = MagicMock()
        current_row.revenue = Decimal("1500.00")
        current_row.units = 75
        current_row.records = 30

        # Previous period
        previous_row = MagicMock()
        previous_row.revenue = Decimal("1000.00")
        previous_row.units = 50
        previous_row.records = 20

        current_result = MagicMock()
        current_result.one.return_value = current_row

        previous_result = MagicMock()
        previous_result.one.return_value = previous_row

        mock_db.execute = AsyncMock(side_effect=[current_result, previous_result])

        kpis = await compute_kpis(mock_db, org_id, period_start, period_end)

        assert len(kpis) == 4
        assert kpis[0].label == "Total Revenue"
        assert kpis[1].label == "Units Sold"
        assert kpis[2].label == "Avg Revenue/Unit"
        assert kpis[3].label == "Royalty Records"

    @pytest.mark.asyncio
    async def test_kpi_change_direction(self, mock_db, org_id):
        """Verify change direction is computed correctly."""
        now = datetime.now(UTC)

        current_row = MagicMock()
        current_row.revenue = Decimal("2000.00")
        current_row.units = 100
        current_row.records = 40

        previous_row = MagicMock()
        previous_row.revenue = Decimal("1000.00")
        previous_row.units = 50
        previous_row.records = 20

        current_result = MagicMock()
        current_result.one.return_value = current_row
        previous_result = MagicMock()
        previous_result.one.return_value = previous_row

        mock_db.execute = AsyncMock(side_effect=[current_result, previous_result])

        kpis = await compute_kpis(mock_db, org_id, now - timedelta(days=30), now)

        # Revenue doubled: should be "up"
        assert kpis[0].change_direction == "up"
        assert kpis[0].change_percent == 100.0

        # Units doubled: should be "up"
        assert kpis[1].change_direction == "up"
        assert kpis[1].change_percent == 100.0


class TestComputeRevenueTrend:
    """Tests for compute_revenue_trend with mocked database."""

    @pytest.fixture
    def org_id(self):
        return uuid.uuid4()

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_empty_trend(self, mock_db, org_id):
        """When no data exists, returns empty trend."""
        now = datetime.now(UTC)

        result_mock = MagicMock()
        result_mock.all.return_value = []
        mock_db.execute = AsyncMock(return_value=result_mock)

        trend = await compute_revenue_trend(
            mock_db, org_id, now - timedelta(days=30), now
        )

        assert trend.metric == "revenue"
        assert len(trend.data_points) == 0
        assert trend.total == Decimal("0.00")
        assert trend.average == Decimal("0.00")
        assert trend.change_percent is None

    @pytest.mark.asyncio
    async def test_trend_with_data(self, mock_db, org_id):
        """Verify trend calculation with multiple data points."""
        now = datetime.now(UTC)

        row1 = MagicMock()
        row1.period = now - timedelta(days=60)
        row1.revenue = Decimal("500.00")

        row2 = MagicMock()
        row2.period = now - timedelta(days=30)
        row2.revenue = Decimal("750.00")

        row3 = MagicMock()
        row3.period = now
        row3.revenue = Decimal("1000.00")

        result_mock = MagicMock()
        result_mock.all.return_value = [row1, row2, row3]
        mock_db.execute = AsyncMock(return_value=result_mock)

        trend = await compute_revenue_trend(
            mock_db, org_id, now - timedelta(days=90), now
        )

        assert len(trend.data_points) == 3
        assert trend.total == Decimal("2250.00")
        assert trend.average == Decimal("750.00")
        # Change from 500 -> 1000 = 100%
        assert trend.change_percent == 100.0
