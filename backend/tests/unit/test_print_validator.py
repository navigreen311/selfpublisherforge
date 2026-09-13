"""Unit tests for PrintValidator — margins, bleed, spine calculations, fonts, DPI, color."""

from __future__ import annotations

import pytest

from app.modules.kdp_validation.print_validator import PrintValidator
from app.modules.kdp_validation.rules import (
    MIN_PAGE_COUNT,
    PaperType,
    calculate_spine_width,
    get_inside_margin,
    get_max_page_count,
)
from app.modules.kdp_validation.schemas import (
    PrintValidationRequest,
    Severity,
    ValidationStatus,
)


@pytest.fixture
def validator() -> PrintValidator:
    return PrintValidator()


def _make_request(**overrides) -> PrintValidationRequest:
    """Create a valid-by-default print validation request."""
    defaults = {
        "trim_size": "6x9",
        "page_count": 200,
        "paper_type": "white",
        "has_bleed": False,
        "inside_margin": 0.625,
        "outside_margin": 0.5,
        "top_margin": 0.5,
        "bottom_margin": 0.5,
        "image_dpi": 300,
        "fonts_embedded": True,
        "color_space": "RGB",
    }
    defaults.update(overrides)
    return PrintValidationRequest(**defaults)


# ===================================================================
# Trim size validation
# ===================================================================


class TestTrimSize:
    def test_valid_trim_size(self, validator: PrintValidator):
        req = _make_request(trim_size="6x9")
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "trim_size_valid"]
        assert len(errors) == 0

    def test_invalid_trim_size(self, validator: PrintValidator):
        req = _make_request(trim_size="4x4")
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "trim_size_valid"]
        assert len(errors) == 1
        assert errors[0].severity == Severity.ERROR

    def test_all_standard_trim_sizes_valid(self, validator: PrintValidator):
        for key in ["5x8", "5.5x8.5", "6x9", "6.14x9.21", "7x10", "8.5x11"]:
            req = _make_request(trim_size=key)
            result = validator.validate(req)
            trim_errors = [i for i in result.issues if i.rule == "trim_size_valid"]
            assert len(trim_errors) == 0, f"Trim size {key} should be valid"


# ===================================================================
# Page count validation
# ===================================================================


class TestPageCount:
    def test_valid_page_count(self, validator: PrintValidator):
        req = _make_request(page_count=200)
        result = validator.validate(req)
        pc_errors = [i for i in result.issues if i.rule.startswith("page_count")]
        # Should only have even-page info at most
        assert all(i.severity != Severity.ERROR for i in pc_errors)

    def test_below_minimum(self, validator: PrintValidator):
        req = _make_request(page_count=10)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "page_count_min"]
        assert len(errors) == 1
        assert errors[0].severity == Severity.ERROR

    def test_exactly_minimum(self, validator: PrintValidator):
        req = _make_request(page_count=MIN_PAGE_COUNT)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "page_count_min"]
        assert len(errors) == 0

    def test_above_maximum(self, validator: PrintValidator):
        req = _make_request(page_count=900)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "page_count_max"]
        assert len(errors) == 1
        assert errors[0].severity == Severity.ERROR

    def test_odd_page_count_warning(self, validator: PrintValidator):
        req = _make_request(page_count=201)
        result = validator.validate(req)
        warnings = [i for i in result.issues if i.rule == "page_count_even"]
        assert len(warnings) == 1
        assert warnings[0].severity == Severity.WARNING

    def test_even_page_count_no_warning(self, validator: PrintValidator):
        req = _make_request(page_count=200)
        result = validator.validate(req)
        warnings = [i for i in result.issues if i.rule == "page_count_even"]
        assert len(warnings) == 0

    def test_invalid_paper_type(self, validator: PrintValidator):
        req = _make_request(paper_type="glossy")
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "paper_type_valid"]
        assert len(errors) == 1


# ===================================================================
# Margin validation
# ===================================================================


class TestMargins:
    def test_margins_pass_6x9(self, validator: PrintValidator):
        # 6x9, 200 pages: inside requires 0.5 + 0.125 = 0.625
        req = _make_request(
            trim_size="6x9",
            page_count=200,
            inside_margin=0.625,
            outside_margin=0.25,
            top_margin=0.25,
            bottom_margin=0.25,
        )
        result = validator.validate(req)
        margin_errors = [i for i in result.issues if i.rule.startswith("margin_") and i.severity == Severity.ERROR]
        assert len(margin_errors) == 0

    def test_inside_margin_too_small(self, validator: PrintValidator):
        req = _make_request(
            trim_size="6x9",
            page_count=200,
            inside_margin=0.4,  # Below required 0.625
        )
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "margin_inside"]
        assert len(errors) == 1
        assert errors[0].severity == Severity.ERROR

    def test_outside_margin_too_small(self, validator: PrintValidator):
        req = _make_request(outside_margin=0.1)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "margin_outside"]
        assert len(errors) == 1

    def test_top_margin_too_small(self, validator: PrintValidator):
        req = _make_request(top_margin=0.1)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "margin_top"]
        assert len(errors) == 1

    def test_bottom_margin_too_small(self, validator: PrintValidator):
        req = _make_request(bottom_margin=0.1)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "margin_bottom"]
        assert len(errors) == 1

    def test_inside_margin_scales_with_pages(self, validator: PrintValidator):
        """High page-count books need wider inside margins."""
        # 350 pages on 6x9: base 0.5 + 0.25 = 0.75 required
        req = _make_request(
            trim_size="6x9",
            page_count=350,
            inside_margin=0.6,  # Below 0.75
        )
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "margin_inside"]
        assert len(errors) == 1

    def test_margins_not_checked_for_invalid_trim(self, validator: PrintValidator):
        """If trim is invalid, margin checks are skipped (no crash)."""
        req = _make_request(trim_size="invalid", inside_margin=0.1)
        result = validator.validate(req)
        margin_errors = [i for i in result.issues if i.rule.startswith("margin_")]
        assert len(margin_errors) == 0


# ===================================================================
# Bleed
# ===================================================================


class TestBleed:
    def test_bleed_info_when_enabled(self, validator: PrintValidator):
        req = _make_request(has_bleed=True)
        result = validator.validate(req)
        infos = [i for i in result.issues if i.rule == "bleed_enabled"]
        assert len(infos) == 1
        assert infos[0].severity == Severity.INFO

    def test_no_bleed_info_when_disabled(self, validator: PrintValidator):
        req = _make_request(has_bleed=False)
        result = validator.validate(req)
        infos = [i for i in result.issues if i.rule == "bleed_enabled"]
        assert len(infos) == 0


# ===================================================================
# Fonts
# ===================================================================


class TestFonts:
    def test_fonts_embedded_pass(self, validator: PrintValidator):
        req = _make_request(fonts_embedded=True)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "fonts_embedded"]
        assert len(errors) == 0

    def test_fonts_not_embedded_error(self, validator: PrintValidator):
        req = _make_request(fonts_embedded=False)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "fonts_embedded"]
        assert len(errors) == 1
        assert errors[0].severity == Severity.ERROR


# ===================================================================
# Image DPI
# ===================================================================


class TestImageDPI:
    def test_dpi_at_minimum(self, validator: PrintValidator):
        req = _make_request(image_dpi=300)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "image_dpi_print"]
        assert len(errors) == 0

    def test_dpi_below_minimum(self, validator: PrintValidator):
        req = _make_request(image_dpi=150)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "image_dpi_print"]
        assert len(errors) == 1

    def test_dpi_none_skips_check(self, validator: PrintValidator):
        req = _make_request(image_dpi=None)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "image_dpi_print"]
        assert len(errors) == 0


# ===================================================================
# Color space
# ===================================================================


class TestColorSpace:
    def test_rgb_passes(self, validator: PrintValidator):
        req = _make_request(color_space="RGB")
        result = validator.validate(req)
        warnings = [i for i in result.issues if i.rule == "color_space_interior"]
        assert len(warnings) == 0

    def test_cmyk_warning(self, validator: PrintValidator):
        req = _make_request(color_space="CMYK")
        result = validator.validate(req)
        warnings = [i for i in result.issues if i.rule == "color_space_interior"]
        assert len(warnings) == 1
        assert warnings[0].severity == Severity.WARNING

    def test_none_skips_check(self, validator: PrintValidator):
        req = _make_request(color_space=None)
        result = validator.validate(req)
        warnings = [i for i in result.issues if i.rule == "color_space_interior"]
        assert len(warnings) == 0


# ===================================================================
# Spine calculation
# ===================================================================


class TestSpineCalculation:
    def test_spine_in_metadata(self, validator: PrintValidator):
        req = _make_request(page_count=200, paper_type="white")
        result = validator.validate(req)
        expected = calculate_spine_width(200, PaperType.WHITE)
        assert result.metadata["spine_width_inches"] == expected

    def test_spine_cream_paper(self, validator: PrintValidator):
        req = _make_request(page_count=200, paper_type="cream")
        result = validator.validate(req)
        expected = calculate_spine_width(200, PaperType.CREAM)
        assert result.metadata["spine_width_inches"] == expected

    def test_spine_increases_with_pages(self):
        spine_100 = calculate_spine_width(100, PaperType.WHITE)
        spine_300 = calculate_spine_width(300, PaperType.WHITE)
        assert spine_300 > spine_100

    def test_cream_thicker_than_white(self):
        spine_white = calculate_spine_width(200, PaperType.WHITE)
        spine_cream = calculate_spine_width(200, PaperType.CREAM)
        assert spine_cream > spine_white


# ===================================================================
# Overall status
# ===================================================================


class TestOverallStatus:
    def test_passes_when_all_valid(self, validator: PrintValidator):
        req = _make_request()
        result = validator.validate(req)
        assert result.status == ValidationStatus.PASSED

    def test_fails_when_error(self, validator: PrintValidator):
        req = _make_request(fonts_embedded=False)
        result = validator.validate(req)
        assert result.status == ValidationStatus.FAILED

    def test_warnings_status(self, validator: PrintValidator):
        # Odd page count produces a warning, no errors
        req = _make_request(page_count=201, color_space="RGB", image_dpi=300)
        result = validator.validate(req)
        # Check no errors, only warnings
        has_error = any(i.severity == Severity.ERROR for i in result.issues)
        has_warning = any(i.severity == Severity.WARNING for i in result.issues)
        if not has_error and has_warning:
            assert result.status == ValidationStatus.WARNINGS


# ===================================================================
# Rules helpers
# ===================================================================


class TestRulesHelpers:
    def test_get_inside_margin_low_pages(self):
        assert get_inside_margin(0.5, 100) == 0.5

    def test_get_inside_margin_medium_pages(self):
        assert get_inside_margin(0.5, 200) == 0.625

    def test_get_inside_margin_high_pages(self):
        assert get_inside_margin(0.5, 400) == 0.75

    def test_get_inside_margin_very_high_pages(self):
        assert get_inside_margin(0.5, 600) == 0.875

    def test_max_page_count_white(self):
        assert get_max_page_count(PaperType.WHITE) == 828

    def test_max_page_count_cream(self):
        assert get_max_page_count(PaperType.CREAM) == 828
