"""Unit tests for CoverValidator — resolution, dimensions, safe zones, format, color space."""

from __future__ import annotations

import pytest

from app.modules.kdp_validation.cover_validator import CoverValidator
from app.modules.kdp_validation.rules import (
    PaperType,
    calculate_spine_width,
    expected_print_cover_height,
    expected_print_cover_width,
)
from app.modules.kdp_validation.schemas import (
    CoverValidationRequest,
    Severity,
    ValidationStatus,
)


@pytest.fixture
def validator() -> CoverValidator:
    return CoverValidator()


def _spine(page_count: int = 200, paper: str = "white") -> float:
    return calculate_spine_width(page_count, PaperType(paper))


def _make_print_cover(**overrides) -> CoverValidationRequest:
    """Create a valid-by-default print cover request (6x9, 200 pages, white)."""
    spine = _spine(200, "white")
    exp_w = expected_print_cover_width(6.0, spine)
    exp_h = expected_print_cover_height(9.0)
    defaults = {
        "cover_type": "print",
        "width_inches": round(exp_w, 4),
        "height_inches": round(exp_h, 4),
        "dpi": 300,
        "file_format": "TIFF",
        "color_space": "CMYK",
        "trim_size": "6x9",
        "page_count": 200,
        "paper_type": "white",
        "has_text_in_bleed": False,
    }
    defaults.update(overrides)
    return CoverValidationRequest(**defaults)


def _make_ebook_cover(**overrides) -> CoverValidationRequest:
    """Create a valid-by-default ebook cover request."""
    defaults = {
        "cover_type": "ebook",
        "width_inches": 6.0,
        "height_inches": 9.0,
        "dpi": 72,
        "file_format": "JPEG",
        "color_space": "RGB",
        "has_text_in_bleed": False,
    }
    defaults.update(overrides)
    return CoverValidationRequest(**defaults)


# ===================================================================
# Resolution
# ===================================================================


class TestResolution:
    def test_print_cover_at_min_dpi(self, validator: CoverValidator):
        req = _make_print_cover(dpi=300)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "cover_resolution"]
        assert len(errors) == 0

    def test_print_cover_below_min_dpi(self, validator: CoverValidator):
        req = _make_print_cover(dpi=150)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "cover_resolution"]
        assert len(errors) == 1
        assert errors[0].severity == Severity.ERROR

    def test_ebook_cover_at_min_dpi(self, validator: CoverValidator):
        req = _make_ebook_cover(dpi=72)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "cover_resolution"]
        assert len(errors) == 0

    def test_ebook_cover_below_min_dpi(self, validator: CoverValidator):
        req = _make_ebook_cover(dpi=50)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "cover_resolution"]
        assert len(errors) == 1

    def test_high_dpi_passes(self, validator: CoverValidator):
        req = _make_print_cover(dpi=600)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "cover_resolution"]
        assert len(errors) == 0


# ===================================================================
# Dimensions
# ===================================================================


class TestDimensions:
    def test_correct_dimensions(self, validator: CoverValidator):
        req = _make_print_cover()
        result = validator.validate(req)
        dim_errors = [
            i for i in result.issues if i.rule in ("cover_width", "cover_height") and i.severity == Severity.ERROR
        ]
        assert len(dim_errors) == 0

    def test_wrong_width(self, validator: CoverValidator):
        req = _make_print_cover(width_inches=10.0)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "cover_width"]
        assert len(errors) == 1

    def test_wrong_height(self, validator: CoverValidator):
        req = _make_print_cover(height_inches=15.0)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "cover_height"]
        assert len(errors) == 1

    def test_within_tolerance(self, validator: CoverValidator):
        """Small deviations within tolerance should pass."""
        spine = _spine(200)
        exp_w = expected_print_cover_width(6.0, spine)
        req = _make_print_cover(width_inches=round(exp_w + 0.02, 4))
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "cover_width"]
        assert len(errors) == 0

    def test_outside_tolerance(self, validator: CoverValidator):
        spine = _spine(200)
        exp_w = expected_print_cover_width(6.0, spine)
        req = _make_print_cover(width_inches=round(exp_w + 0.1, 4))
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "cover_width"]
        assert len(errors) == 1

    def test_ebook_skips_dimensions(self, validator: CoverValidator):
        """Ebook covers don't have strict dimension requirements."""
        req = _make_ebook_cover()
        result = validator.validate(req)
        dim_issues = [i for i in result.issues if i.rule in ("cover_width", "cover_height")]
        assert len(dim_issues) == 0

    def test_missing_trim_size_info(self, validator: CoverValidator):
        """When trim_size not provided, skip dimension check with info."""
        req = _make_print_cover(trim_size=None, page_count=None)
        result = validator.validate(req)
        infos = [i for i in result.issues if i.rule == "cover_dimensions_skipped"]
        assert len(infos) == 1

    def test_invalid_trim_size_error(self, validator: CoverValidator):
        req = _make_print_cover(trim_size="999x999")
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "cover_trim_size_valid"]
        assert len(errors) == 1

    def test_dimensions_vary_with_page_count(self, validator: CoverValidator):
        """Different page counts produce different expected widths (spine differs)."""
        spine_100 = _spine(100)
        spine_400 = _spine(400)
        exp_w_100 = expected_print_cover_width(6.0, spine_100)
        exp_w_400 = expected_print_cover_width(6.0, spine_400)
        assert exp_w_400 > exp_w_100

    def test_metadata_has_expected_dimensions(self, validator: CoverValidator):
        req = _make_print_cover()
        result = validator.validate(req)
        assert "expected_width" in result.metadata
        assert "expected_height" in result.metadata
        assert "spine_width" in result.metadata


# ===================================================================
# Safe zones
# ===================================================================


class TestSafeZones:
    def test_no_text_in_bleed(self, validator: CoverValidator):
        req = _make_print_cover(has_text_in_bleed=False)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "cover_safe_zone"]
        assert len(errors) == 0

    def test_text_in_bleed_error(self, validator: CoverValidator):
        req = _make_print_cover(has_text_in_bleed=True)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "cover_safe_zone"]
        assert len(errors) == 1
        assert errors[0].severity == Severity.ERROR


# ===================================================================
# File format
# ===================================================================


class TestFileFormat:
    def test_print_tiff_accepted(self, validator: CoverValidator):
        req = _make_print_cover(file_format="TIFF")
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "cover_format"]
        assert len(errors) == 0

    def test_print_png_accepted(self, validator: CoverValidator):
        req = _make_print_cover(file_format="PNG")
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "cover_format"]
        assert len(errors) == 0

    def test_print_jpeg_rejected(self, validator: CoverValidator):
        req = _make_print_cover(file_format="JPEG")
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "cover_format"]
        assert len(errors) == 1

    def test_ebook_jpeg_accepted(self, validator: CoverValidator):
        req = _make_ebook_cover(file_format="JPEG")
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "cover_format"]
        assert len(errors) == 0

    def test_ebook_jpg_accepted(self, validator: CoverValidator):
        req = _make_ebook_cover(file_format="JPG")
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "cover_format"]
        assert len(errors) == 0

    def test_ebook_tiff_rejected(self, validator: CoverValidator):
        req = _make_ebook_cover(file_format="TIFF")
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "cover_format"]
        assert len(errors) == 1


# ===================================================================
# Color space
# ===================================================================


class TestColorSpace:
    def test_print_cmyk_passes(self, validator: CoverValidator):
        req = _make_print_cover(color_space="CMYK")
        result = validator.validate(req)
        warnings = [i for i in result.issues if i.rule == "cover_color_space"]
        assert len(warnings) == 0

    def test_print_rgb_warning(self, validator: CoverValidator):
        req = _make_print_cover(color_space="RGB")
        result = validator.validate(req)
        warnings = [i for i in result.issues if i.rule == "cover_color_space"]
        assert len(warnings) == 1
        assert warnings[0].severity == Severity.WARNING

    def test_ebook_rgb_passes(self, validator: CoverValidator):
        req = _make_ebook_cover(color_space="RGB")
        result = validator.validate(req)
        warnings = [i for i in result.issues if i.rule == "cover_color_space"]
        assert len(warnings) == 0

    def test_ebook_srgb_passes(self, validator: CoverValidator):
        req = _make_ebook_cover(color_space="sRGB")
        result = validator.validate(req)
        warnings = [i for i in result.issues if i.rule == "cover_color_space"]
        assert len(warnings) == 0

    def test_ebook_cmyk_warning(self, validator: CoverValidator):
        req = _make_ebook_cover(color_space="CMYK")
        result = validator.validate(req)
        warnings = [i for i in result.issues if i.rule == "cover_color_space"]
        assert len(warnings) == 1

    def test_none_color_space_skips(self, validator: CoverValidator):
        req = _make_print_cover(color_space=None)
        result = validator.validate(req)
        warnings = [i for i in result.issues if i.rule == "cover_color_space"]
        assert len(warnings) == 0


# ===================================================================
# Overall status
# ===================================================================


class TestOverallStatus:
    def test_perfect_print_cover(self, validator: CoverValidator):
        req = _make_print_cover()
        result = validator.validate(req)
        assert result.status == ValidationStatus.PASSED

    def test_perfect_ebook_cover(self, validator: CoverValidator):
        req = _make_ebook_cover()
        result = validator.validate(req)
        assert result.status == ValidationStatus.PASSED

    def test_failed_cover(self, validator: CoverValidator):
        req = _make_print_cover(dpi=72, has_text_in_bleed=True)
        result = validator.validate(req)
        assert result.status == ValidationStatus.FAILED

    def test_warnings_status(self, validator: CoverValidator):
        req = _make_print_cover(color_space="RGB")
        result = validator.validate(req)
        # RGB on print cover is warning, but we need to make sure no errors
        has_error = any(i.severity == Severity.ERROR for i in result.issues)
        if not has_error:
            assert result.status == ValidationStatus.WARNINGS
