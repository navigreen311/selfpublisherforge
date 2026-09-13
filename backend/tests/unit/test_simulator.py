"""Unit tests for the price simulation engine."""

from __future__ import annotations

import uuid

import pytest

from app.modules.pricing_automation.schemas import (
    BookFormat,
    PriceSimulationRequest,
)
from app.modules.pricing_automation.simulator import (
    _build_price_point,
    _estimate_sales_change,
    _get_royalty_rate,
    simulate_price_change,
)

# ──────────────────── Royalty Rate ────────────────────


class TestGetRoyaltyRate:
    def test_ebook_35_low(self):
        assert _get_royalty_rate(0.99, BookFormat.EBOOK) == 0.35

    def test_ebook_70_range(self):
        assert _get_royalty_rate(2.99, BookFormat.EBOOK) == 0.70
        assert _get_royalty_rate(4.99, BookFormat.EBOOK) == 0.70
        assert _get_royalty_rate(9.99, BookFormat.EBOOK) == 0.70

    def test_ebook_35_high(self):
        assert _get_royalty_rate(12.99, BookFormat.EBOOK) == 0.35

    def test_paperback(self):
        assert _get_royalty_rate(14.99, BookFormat.PAPERBACK) == 0.40

    def test_hardcover(self):
        assert _get_royalty_rate(24.99, BookFormat.HARDCOVER) == 0.35

    def test_audiobook(self):
        assert _get_royalty_rate(19.99, BookFormat.AUDIOBOOK) == 0.40


# ──────────────────── Sales Change Estimation ────────────────────


class TestEstimateSalesChange:
    def test_price_increase_reduces_sales(self):
        new_sales = _estimate_sales_change(
            current_price=4.99,
            new_price=6.99,
            current_daily_sales=10.0,
            elasticity=-1.5,
        )
        assert new_sales < 10.0

    def test_price_decrease_increases_sales(self):
        new_sales = _estimate_sales_change(
            current_price=4.99,
            new_price=2.99,
            current_daily_sales=10.0,
            elasticity=-1.5,
        )
        assert new_sales > 10.0

    def test_no_price_change(self):
        new_sales = _estimate_sales_change(
            current_price=4.99,
            new_price=4.99,
            current_daily_sales=10.0,
            elasticity=-1.5,
        )
        assert new_sales == pytest.approx(10.0)

    def test_zero_current_price(self):
        new_sales = _estimate_sales_change(
            current_price=0.0,
            new_price=4.99,
            current_daily_sales=10.0,
            elasticity=-1.5,
        )
        assert new_sales == 10.0

    def test_sales_never_negative(self):
        # Extreme price increase
        new_sales = _estimate_sales_change(
            current_price=0.99,
            new_price=99.99,
            current_daily_sales=10.0,
            elasticity=-2.0,
        )
        assert new_sales >= 0.0

    def test_elasticity_magnitude_matters(self):
        # Higher elasticity (more negative) = bigger impact
        low_e = _estimate_sales_change(4.99, 6.99, 10.0, -0.5)
        high_e = _estimate_sales_change(4.99, 6.99, 10.0, -2.0)
        assert high_e < low_e


# ──────────────────── Build Price Point ────────────────────


class TestBuildPricePoint:
    def test_basic_calculation(self):
        point = _build_price_point(4.99, 10.0, BookFormat.EBOOK)
        assert point.price == 4.99
        assert point.estimated_daily_sales == 10.0
        assert point.estimated_daily_revenue == pytest.approx(49.90, abs=0.01)
        assert point.estimated_monthly_revenue == pytest.approx(49.90 * 30, abs=1.0)
        assert point.royalty_rate == 0.70  # $4.99 is in 70% tier
        assert point.estimated_daily_royalties == pytest.approx(49.90 * 0.70, abs=0.01)

    def test_royalty_override(self):
        point = _build_price_point(4.99, 10.0, BookFormat.EBOOK, royalty_override=0.50)
        assert point.royalty_rate == 0.50


# ──────────────────── Full Simulation ────────────────────


class TestSimulatePriceChange:
    def test_basic_simulation(self):
        request = PriceSimulationRequest(
            current_price=4.99,
            proposed_price=2.99,
            current_daily_sales=10.0,
            elasticity=-1.5,
        )
        result = simulate_price_change(request)

        assert result.current_price == 4.99
        assert result.proposed_price == 2.99
        assert result.book_format == BookFormat.EBOOK
        assert result.elasticity == -1.5
        assert result.current_metrics.price == 4.99
        assert result.proposed_metrics.price == 2.99
        # Dropping price should increase sales
        assert result.proposed_metrics.estimated_daily_sales > result.current_metrics.estimated_daily_sales

    def test_price_change_percentage(self):
        request = PriceSimulationRequest(
            current_price=10.00,
            proposed_price=5.00,
            current_daily_sales=10.0,
        )
        result = simulate_price_change(request)
        assert result.price_change_pct == pytest.approx(-50.0)

    def test_recommended_price_points_generated(self):
        request = PriceSimulationRequest(
            current_price=4.99,
            proposed_price=2.99,
            current_daily_sales=10.0,
        )
        result = simulate_price_change(request)
        assert len(result.recommended_price_points) > 0
        # Should be sorted by monthly royalties descending
        royalties = [p.estimated_monthly_royalties for p in result.recommended_price_points]
        assert royalties == sorted(royalties, reverse=True)

    def test_breakeven_sales_calculated(self):
        request = PriceSimulationRequest(
            current_price=4.99,
            proposed_price=2.99,
            current_daily_sales=10.0,
        )
        result = simulate_price_change(request)
        assert result.breakeven_sales > 0

    def test_with_book_id(self):
        bid = uuid.uuid4()
        request = PriceSimulationRequest(
            book_id=bid,
            current_price=4.99,
            proposed_price=6.99,
            current_daily_sales=10.0,
        )
        result = simulate_price_change(request)
        assert result.book_id == bid

    def test_paperback_format(self):
        request = PriceSimulationRequest(
            current_price=14.99,
            proposed_price=12.99,
            book_format=BookFormat.PAPERBACK,
            current_daily_sales=5.0,
        )
        result = simulate_price_change(request)
        assert result.book_format == BookFormat.PAPERBACK
        assert len(result.recommended_price_points) > 0

    def test_royalty_rate_override(self):
        request = PriceSimulationRequest(
            current_price=4.99,
            proposed_price=2.99,
            current_daily_sales=10.0,
            royalty_rate=0.60,
        )
        result = simulate_price_change(request)
        assert result.current_metrics.royalty_rate == 0.60
        assert result.proposed_metrics.royalty_rate == 0.60
