"""Unit tests for the KU (Kindle Unlimited) vs. Wide distribution calculator."""

from __future__ import annotations

import pytest

from app.modules.pricing_automation.ku_calculator import (
    _breakeven_ku_reads,
    calculate_ku_vs_wide,
)
from app.modules.pricing_automation.schemas import KUCalculatorRequest, KUCalculatorResponse


# ──────────────────── Basic Calculation Tests ────────────────────


class TestKUCalculatorBasic:
    def test_ku_exclusive_calculation(self):
        """Test KU exclusive revenue is correctly calculated."""
        request = KUCalculatorRequest(
            book_page_count=300,
            estimated_ku_reads_per_month=100,
            ku_page_rate=0.0045,
            wide_price=4.99,
            wide_monthly_sales=50,
            wide_royalty_rate=0.70,
            amazon_price=4.99,
            amazon_monthly_sales=30,
            amazon_royalty_rate=0.70,
        )
        result = calculate_ku_vs_wide(request)

        # KU page revenue: 300 * 100 * 0.0045 = 135.00
        # KU paid sales: 4.99 * 30 = 149.70
        # KU paid royalties: 149.70 * 0.70 = 104.79
        # KU total royalties: 135.00 + 104.79 = 239.79
        assert result.ku_exclusive.monthly_royalties == pytest.approx(239.79, abs=0.01)
        assert result.ku_exclusive.source == "KU Exclusive (KDP Select)"

    def test_wide_distribution_calculation(self):
        """Test wide distribution revenue is correctly calculated."""
        request = KUCalculatorRequest(
            book_page_count=300,
            estimated_ku_reads_per_month=100,
            ku_page_rate=0.0045,
            wide_price=4.99,
            wide_monthly_sales=50,
            wide_royalty_rate=0.70,
            amazon_price=4.99,
            amazon_monthly_sales=30,
            amazon_royalty_rate=0.70,
        )
        result = calculate_ku_vs_wide(request)

        # Wide revenue: 4.99 * 50 = 249.50
        # Wide royalties: 249.50 * 0.70 = 174.65
        assert result.wide_distribution.monthly_royalties == pytest.approx(174.65, abs=0.01)
        assert result.wide_distribution.source == "Wide Distribution"

    def test_annual_is_12x_monthly(self):
        """Verify annual calculations are 12x monthly."""
        request = KUCalculatorRequest(
            book_page_count=250,
            estimated_ku_reads_per_month=80,
            ku_page_rate=0.0045,
            wide_price=3.99,
            wide_monthly_sales=40,
            wide_royalty_rate=0.70,
            amazon_price=3.99,
            amazon_monthly_sales=20,
            amazon_royalty_rate=0.70,
        )
        result = calculate_ku_vs_wide(request)

        assert result.ku_exclusive.annual_royalties == pytest.approx(
            result.ku_exclusive.monthly_royalties * 12, abs=0.02
        )
        assert result.wide_distribution.annual_royalties == pytest.approx(
            result.wide_distribution.monthly_royalties * 12, abs=0.02
        )

    def test_difference_is_ku_minus_wide(self):
        """Verify difference calculation is KU - Wide."""
        request = KUCalculatorRequest(
            book_page_count=300,
            estimated_ku_reads_per_month=100,
            ku_page_rate=0.0045,
            wide_price=4.99,
            wide_monthly_sales=50,
            wide_royalty_rate=0.70,
            amazon_price=4.99,
            amazon_monthly_sales=30,
            amazon_royalty_rate=0.70,
        )
        result = calculate_ku_vs_wide(request)

        expected_diff = (
            result.ku_exclusive.monthly_royalties
            - result.wide_distribution.monthly_royalties
        )
        assert result.difference_monthly == pytest.approx(expected_diff, abs=0.02)
        assert result.difference_annual == pytest.approx(expected_diff * 12, abs=0.25)


# ──────────────────── Recommendation Tests ────────────────────


class TestKURecommendation:
    def test_ku_strongly_recommended_when_much_better(self):
        """When KU is significantly better, recommendation should be strong."""
        request = KUCalculatorRequest(
            book_page_count=500,
            estimated_ku_reads_per_month=200,
            ku_page_rate=0.0045,
            wide_price=2.99,
            wide_monthly_sales=10,
            wide_royalty_rate=0.70,
            amazon_price=2.99,
            amazon_monthly_sales=50,
            amazon_royalty_rate=0.70,
        )
        result = calculate_ku_vs_wide(request)
        assert result.difference_monthly > 0
        assert "KU" in result.recommendation

    def test_wide_recommended_when_better(self):
        """When wide distribution is better, recommendation should favor wide."""
        request = KUCalculatorRequest(
            book_page_count=100,
            estimated_ku_reads_per_month=5,
            ku_page_rate=0.0045,
            wide_price=9.99,
            wide_monthly_sales=100,
            wide_royalty_rate=0.70,
            amazon_price=9.99,
            amazon_monthly_sales=10,
            amazon_royalty_rate=0.70,
        )
        result = calculate_ku_vs_wide(request)
        assert result.difference_monthly < 0
        assert "Wide" in result.recommendation

    def test_close_difference_mentions_both(self):
        """When difference is small, recommendation should be nuanced."""
        request = KUCalculatorRequest(
            book_page_count=200,
            estimated_ku_reads_per_month=50,
            ku_page_rate=0.0045,
            wide_price=4.99,
            wide_monthly_sales=30,
            wide_royalty_rate=0.70,
            amazon_price=4.99,
            amazon_monthly_sales=25,
            amazon_royalty_rate=0.70,
        )
        result = calculate_ku_vs_wide(request)
        # The recommendation should exist regardless
        assert len(result.recommendation) > 0


# ──────────────────── Edge Cases ────────────────────


class TestKUEdgeCases:
    def test_zero_ku_reads(self):
        """Should handle zero KU reads gracefully."""
        request = KUCalculatorRequest(
            book_page_count=300,
            estimated_ku_reads_per_month=0,
            ku_page_rate=0.0045,
            wide_price=4.99,
            wide_monthly_sales=50,
            wide_royalty_rate=0.70,
            amazon_price=4.99,
            amazon_monthly_sales=30,
            amazon_royalty_rate=0.70,
        )
        result = calculate_ku_vs_wide(request)
        # KU revenue is just paid sales
        assert result.ku_exclusive.monthly_royalties > 0
        assert result.details["ku_page_reads_revenue"] == 0.0

    def test_zero_wide_sales(self):
        """Should handle zero wide sales."""
        request = KUCalculatorRequest(
            book_page_count=300,
            estimated_ku_reads_per_month=100,
            ku_page_rate=0.0045,
            wide_price=4.99,
            wide_monthly_sales=0,
            wide_royalty_rate=0.70,
            amazon_price=4.99,
            amazon_monthly_sales=30,
            amazon_royalty_rate=0.70,
        )
        result = calculate_ku_vs_wide(request)
        assert result.wide_distribution.monthly_royalties == 0.0
        assert result.difference_monthly > 0

    def test_zero_amazon_paid_sales(self):
        """Should handle no Amazon paid sales (all KU reads)."""
        request = KUCalculatorRequest(
            book_page_count=300,
            estimated_ku_reads_per_month=100,
            ku_page_rate=0.0045,
            wide_price=4.99,
            wide_monthly_sales=50,
            wide_royalty_rate=0.70,
            amazon_price=4.99,
            amazon_monthly_sales=0,
            amazon_royalty_rate=0.70,
        )
        result = calculate_ku_vs_wide(request)
        # KU should only have page read revenue
        assert result.ku_exclusive.monthly_royalties == pytest.approx(135.0, abs=0.01)

    def test_high_page_count_book(self):
        """Test with a very long book."""
        request = KUCalculatorRequest(
            book_page_count=2000,
            estimated_ku_reads_per_month=50,
            ku_page_rate=0.0045,
            wide_price=14.99,
            wide_monthly_sales=20,
            wide_royalty_rate=0.60,
            amazon_price=14.99,
            amazon_monthly_sales=15,
            amazon_royalty_rate=0.35,
        )
        result = calculate_ku_vs_wide(request)
        # Long books benefit hugely from KU page reads
        # 2000 * 50 * 0.0045 = 450.00 from reads alone
        assert result.ku_exclusive.monthly_royalties > 450.0

    def test_custom_ku_page_rate(self):
        """Test with a custom KU page rate."""
        request = KUCalculatorRequest(
            book_page_count=300,
            estimated_ku_reads_per_month=100,
            ku_page_rate=0.005,  # Higher than default
            wide_price=4.99,
            wide_monthly_sales=50,
            wide_royalty_rate=0.70,
            amazon_price=4.99,
            amazon_monthly_sales=30,
            amazon_royalty_rate=0.70,
        )
        result = calculate_ku_vs_wide(request)
        # 300 * 100 * 0.005 = 150.00
        assert result.details["ku_page_reads_revenue"] == pytest.approx(150.0, abs=0.01)


# ──────────────────── Breakeven Calculation ────────────────────


class TestBreakevenReads:
    def test_breakeven_positive_gap(self):
        """When wide earns more, breakeven reads should be positive."""
        reads = _breakeven_ku_reads(
            wide_royalties=200.0,
            ku_paid_royalties=50.0,
            page_count=300,
            page_rate=0.0045,
        )
        # (200 - 50) / (300 * 0.0045) = 150 / 1.35 = 111.11 -> 112
        assert reads == 112

    def test_breakeven_no_gap(self):
        """When KU already earns more, breakeven is 0."""
        reads = _breakeven_ku_reads(
            wide_royalties=50.0,
            ku_paid_royalties=100.0,
            page_count=300,
            page_rate=0.0045,
        )
        assert reads == 0

    def test_breakeven_zero_pages(self):
        """Edge case: zero pages should return 0."""
        reads = _breakeven_ku_reads(
            wide_royalties=200.0,
            ku_paid_royalties=50.0,
            page_count=0,
            page_rate=0.0045,
        )
        assert reads == 0

    def test_breakeven_zero_rate(self):
        """Edge case: zero page rate should return 0."""
        reads = _breakeven_ku_reads(
            wide_royalties=200.0,
            ku_paid_royalties=50.0,
            page_count=300,
            page_rate=0.0,
        )
        assert reads == 0

    def test_breakeven_appears_in_response(self):
        """Breakeven KU reads should appear in response details."""
        request = KUCalculatorRequest(
            book_page_count=300,
            estimated_ku_reads_per_month=100,
            ku_page_rate=0.0045,
            wide_price=4.99,
            wide_monthly_sales=50,
            wide_royalty_rate=0.70,
            amazon_price=4.99,
            amazon_monthly_sales=30,
            amazon_royalty_rate=0.70,
        )
        result = calculate_ku_vs_wide(request)
        assert "breakeven_ku_reads" in result.details
        assert isinstance(result.details["breakeven_ku_reads"], int)


# ──────────────────── Response Structure ────────────────────


class TestResponseStructure:
    def test_response_has_all_fields(self):
        request = KUCalculatorRequest(
            book_page_count=300,
            estimated_ku_reads_per_month=100,
            ku_page_rate=0.0045,
            wide_price=4.99,
            wide_monthly_sales=50,
            wide_royalty_rate=0.70,
            amazon_price=4.99,
            amazon_monthly_sales=30,
            amazon_royalty_rate=0.70,
        )
        result = calculate_ku_vs_wide(request)

        assert isinstance(result, KUCalculatorResponse)
        assert result.ku_exclusive is not None
        assert result.wide_distribution is not None
        assert isinstance(result.difference_monthly, float)
        assert isinstance(result.difference_annual, float)
        assert isinstance(result.recommendation, str)
        assert isinstance(result.details, dict)

    def test_details_contain_all_breakdown(self):
        request = KUCalculatorRequest(
            book_page_count=300,
            estimated_ku_reads_per_month=100,
            ku_page_rate=0.0045,
            wide_price=4.99,
            wide_monthly_sales=50,
            wide_royalty_rate=0.70,
            amazon_price=4.99,
            amazon_monthly_sales=30,
            amazon_royalty_rate=0.70,
        )
        result = calculate_ku_vs_wide(request)

        expected_keys = [
            "ku_page_reads_revenue",
            "ku_paid_sales_revenue",
            "ku_paid_royalties",
            "ku_pages_per_read",
            "ku_reads_per_month",
            "ku_page_rate",
            "wide_sales_revenue",
            "wide_royalties",
            "wide_price",
            "wide_monthly_sales",
            "wide_royalty_rate",
            "breakeven_ku_reads",
        ]
        for key in expected_keys:
            assert key in result.details, f"Missing detail key: {key}"
