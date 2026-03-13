"""Tests for Print Quality Systems: cost engine, CMYK soft-proof, ink coverage.

Covers blueprint sections 8.1-8.3 with 17 tests across 6 test classes.
"""

from __future__ import annotations

import uuid

import pytest

from app.modules.specialty_books.service_print_quality import (
    FIXED_COST_BY_TRIM,
    HEAVY_INK_THRESHOLD,
    KDP_MAX_PAGES,
    KDP_MIN_PAGES,
    LIGHT_INK_THRESHOLD,
    MAX_INK_DENSITY_PCT,
    PER_PAGE_COST,
    SPINE_WIDTH_CREAM,
    SPINE_WIDTH_WHITE,
    analyze_ink_coverage,
    auto_adjust_color,
    calculate_print_cost,
    calculate_spine_width,
    generate_grayscale_preview,
    generate_soft_proof,
    validate_print_specs,
    _rgb_to_cmyk,
    _ink_density,
)


class TestPrintCostCalculation:
    """Tests for calculate_print_cost (blueprint 8.1)."""

    def test_basic_cost_matches_kdp_formula(self) -> None:
        result = calculate_print_cost(page_count=100, interior_type="black_white", trim_size="6x9")
        expected_cost = FIXED_COST_BY_TRIM["6x9"] + PER_PAGE_COST["black_white"] * 100
        assert result["base_cost"] == round(expected_cost, 2)
        assert result["total_cost"] == round(expected_cost, 2)
        assert result["ink_cost_adjustment"] == 0.0

    def test_color_interior_cost(self) -> None:
        result = calculate_print_cost(page_count=32, interior_type="premium_color", trim_size="8.5x8.5")
        expected = FIXED_COST_BY_TRIM["8.5x8.5"] + PER_PAGE_COST["premium_color"] * 32
        assert result["base_cost"] == round(expected, 2)

    def test_multiple_scenarios_calculated(self) -> None:
        result = calculate_print_cost(page_count=100, interior_type="black_white", trim_size="6x9")
        assert len(result["scenarios"]) == 4
        margins = [s["target_margin"] for s in result["scenarios"]]
        assert "0%" in margins
        assert "30%" in margins
        assert "50%" in margins
        assert "70%" in margins

    def test_scenario_prices_increase_with_margin(self) -> None:
        result = calculate_print_cost(page_count=100, interior_type="black_white", trim_size="6x9")
        prices = [s["price"] for s in result["scenarios"]]
        assert prices == sorted(prices)

    def test_margin_guardrails_warn_low_page_count(self) -> None:
        result = calculate_print_cost(page_count=10, interior_type="black_white", trim_size="6x9")
        assert any("below KDP minimum" in w for w in result["warnings"])

    def test_margin_guardrails_warn_high_page_count(self) -> None:
        result = calculate_print_cost(page_count=900, interior_type="black_white", trim_size="6x9")
        assert any("exceeds KDP maximum" in w for w in result["warnings"])

    def test_ink_coverage_adjustment_applied(self) -> None:
        result = calculate_print_cost(page_count=100, interior_type="standard_color", trim_size="8.5x11", ink_coverage_pct=70.0)
        assert result["ink_cost_adjustment"] > 0.0
        assert result["total_cost"] > result["base_cost"]

    def test_category_norm_recommendation(self) -> None:
        result = calculate_print_cost(page_count=50, interior_type="black_white", trim_size="8.5x11", category="adult_coloring")
        assert result["recommended_price"] is not None
        assert 7.0 <= result["recommended_price"] <= 15.0


class TestInkCoverage:
    """Tests for analyze_ink_coverage (blueprint 8.3)."""

    def test_ink_coverage_from_pixel_data(self) -> None:
        pixels = [50] * 70 + [200] * 30
        result = analyze_ink_coverage([{"page_num": 1, "pixel_data": pixels}])
        assert result["per_page"][0]["coverage_pct"] == 70.0
        assert result["average"] == 70.0

    def test_ink_coverage_from_precomputed(self) -> None:
        result = analyze_ink_coverage([
            {"page_num": 1, "coverage_pct": 45.0},
            {"page_num": 2, "coverage_pct": 55.0},
        ])
        assert result["per_page"][0]["coverage_pct"] == 45.0
        assert result["per_page"][1]["coverage_pct"] == 55.0
        assert result["average"] == 50.0

    def test_heavy_ink_warning_triggers(self) -> None:
        result = analyze_ink_coverage([{"page_num": 1, "coverage_pct": 85.0}])
        assert result["per_page"][0]["heavy_warning"] is True

    def test_heavy_ink_warning_not_triggered(self) -> None:
        result = analyze_ink_coverage([{"page_num": 1, "coverage_pct": 80.0}])
        assert result["per_page"][0]["heavy_warning"] is False

    def test_light_ink_warning_triggers(self) -> None:
        result = analyze_ink_coverage([{"page_num": 1, "coverage_pct": 3.0}])
        assert result["per_page"][0]["light_warning"] is True

    def test_min_max_average(self) -> None:
        pages = [
            {"page_num": 1, "coverage_pct": 20.0},
            {"page_num": 2, "coverage_pct": 60.0},
            {"page_num": 3, "coverage_pct": 40.0},
        ]
        result = analyze_ink_coverage(pages)
        assert result["min"] == 20.0
        assert result["max"] == 60.0
        assert result["average"] == 40.0


class TestSoftProof:
    """Tests for generate_soft_proof (blueprint 8.2)."""

    def test_out_of_gamut_detection(self) -> None:
        pixels = [{"page": 1, "x": 10, "y": 20, "r": 0, "g": 100, "b": 255}]
        result = generate_soft_proof(pixels)
        assert isinstance(result["out_of_gamut_areas"], list)
        assert result["cmyk_preview_url"] is not None

    def test_shadow_crush_detection(self) -> None:
        pixels = [{"page": 1, "x": 0, "y": 0, "r": 5, "g": 5, "b": 5}]
        result = generate_soft_proof(pixels)
        assert len(result["shadow_crush_warnings"]) > 0

    def test_ink_density_key_present(self) -> None:
        pixels = [{"page": 1, "x": 0, "y": 0, "r": 10, "g": 1, "b": 1}]
        result = generate_soft_proof(pixels)
        assert "ink_density_issues" in result

    def test_soft_proof_returns_preview_url(self) -> None:
        pixels = [{"page": 1, "x": 0, "y": 0, "r": 128, "g": 128, "b": 128}]
        result = generate_soft_proof(pixels, profile="FOGRA39")
        assert "FOGRA39" in result["cmyk_preview_url"]


class TestAutoAdjust:
    """Tests for auto_adjust_color."""

    def test_auto_adjust_returns_adjusted_pixels(self) -> None:
        pixels = [{"page": 1, "x": 0, "y": 0, "r": 0, "g": 100, "b": 255}]
        result = auto_adjust_color(pixels)
        assert isinstance(result["adjusted_pixels"], list)
        assert len(result["adjusted_pixels"]) == 1

    def test_auto_adjust_lightens_shadows(self) -> None:
        pixels = [{"page": 1, "x": 0, "y": 0, "r": 5, "g": 5, "b": 5}]
        result = auto_adjust_color(pixels)
        shadow_changes = [c for c in result["changes_log"] if c["type"] == "shadow_lighten"]
        assert len(shadow_changes) > 0
        adj = result["adjusted_pixels"][0]
        assert adj["r"] >= 5 or adj["g"] >= 5 or adj["b"] >= 5


class TestSpineWidth:
    """Tests for calculate_spine_width."""

    def test_white_paper_formula(self) -> None:
        result = calculate_spine_width(100, "white")
        expected = round(100 * SPINE_WIDTH_WHITE, 4)
        assert result["spine_width_inches"] == expected

    def test_cream_paper_formula(self) -> None:
        result = calculate_spine_width(200, "cream")
        expected = round(200 * SPINE_WIDTH_CREAM, 4)
        assert result["spine_width_inches"] == expected

    def test_mm_conversion(self) -> None:
        result = calculate_spine_width(100, "white")
        expected_mm = round(result["spine_width_inches"] * 25.4, 2)
        assert result["spine_width_mm"] == expected_mm

    def test_cream_wider_than_white(self) -> None:
        white = calculate_spine_width(100, "white")
        cream = calculate_spine_width(100, "cream")
        assert cream["spine_width_inches"] > white["spine_width_inches"]


class TestPrintSpecValidation:
    """Tests for validate_print_specs."""

    @pytest.mark.asyncio
    async def test_valid_specs_pass(self) -> None:
        result = await validate_print_specs(
            db=None, book_type="coloring", book_id=uuid.uuid4(), org_id=uuid.uuid4(),
            dpi=300, margins={"top": 0.25, "bottom": 0.25, "outside": 0.375, "gutter": 0.625},
            trim_size="8.5x11", page_count=100, file_size_mb=50.0,
        )
        assert result["all_passed"] is True

    @pytest.mark.asyncio
    async def test_invalid_dpi_fails(self) -> None:
        result = await validate_print_specs(
            db=None, book_type="childrens", book_id=uuid.uuid4(), org_id=uuid.uuid4(),
            dpi=150, trim_size="8.5x11", page_count=32,
        )
        dpi_check = next(c for c in result["checks"] if c["name"] == "dpi_check")
        assert dpi_check["passed"] is False

    @pytest.mark.asyncio
    async def test_margin_violations_caught(self) -> None:
        result = await validate_print_specs(
            db=None, book_type="puzzle", book_id=uuid.uuid4(), org_id=uuid.uuid4(),
            dpi=300, margins={"top": 0.1, "bottom": 0.1, "outside": 0.2, "gutter": 0.3},
            trim_size="6x9", page_count=100,
        )
        failed = [c for c in result["checks"] if not c["passed"]]
        margin_fails = [c for c in failed if c["name"].startswith("margin_")]
        assert len(margin_fails) >= 3

    @pytest.mark.asyncio
    async def test_page_count_below_minimum_fails(self) -> None:
        result = await validate_print_specs(
            db=None, book_type="coloring", book_id=uuid.uuid4(), org_id=uuid.uuid4(),
            dpi=300, trim_size="8.5x11", page_count=10,
        )
        pc_check = next(c for c in result["checks"] if c["name"] == "page_count")
        assert pc_check["passed"] is False

    @pytest.mark.asyncio
    async def test_page_count_above_maximum_fails(self) -> None:
        result = await validate_print_specs(
            db=None, book_type="puzzle", book_id=uuid.uuid4(), org_id=uuid.uuid4(),
            dpi=300, trim_size="6x9", page_count=900,
        )
        pc_check = next(c for c in result["checks"] if c["name"] == "page_count")
        assert pc_check["passed"] is False

    @pytest.mark.asyncio
    async def test_invalid_trim_size_fails(self) -> None:
        result = await validate_print_specs(
            db=None, book_type="childrens", book_id=uuid.uuid4(), org_id=uuid.uuid4(),
            dpi=300, trim_size="4x4", page_count=32,
        )
        trim_check = next(c for c in result["checks"] if c["name"] == "trim_size")
        assert trim_check["passed"] is False


class TestGrayscalePreview:
    """Tests for generate_grayscale_preview."""

    def test_converts_to_grayscale(self) -> None:
        pixels = [{"page": 1, "x": 0, "y": 0, "r": 255, "g": 0, "b": 0}]
        result = generate_grayscale_preview(pixels)
        px = result["grayscale_pixels"][0]
        assert px["r"] == px["g"] == px["b"]
        assert px["r"] == 76

    def test_white_stays_white(self) -> None:
        pixels = [{"page": 1, "x": 0, "y": 0, "r": 255, "g": 255, "b": 255}]
        result = generate_grayscale_preview(pixels)
        px = result["grayscale_pixels"][0]
        assert px["r"] == 255
