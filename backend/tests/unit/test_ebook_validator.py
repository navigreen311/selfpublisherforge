"""Unit tests for EbookValidator — TOC, images, links, prohibited elements, font size, file size."""

from __future__ import annotations

import pytest

from app.modules.kdp_validation.ebook_validator import EbookValidator
from app.modules.kdp_validation.rules import (
    MAX_EBOOK_FILE_SIZE_BYTES,
    MAX_EBOOK_IMAGE_SIZE_BYTES,
    RECOMMENDED_MIN_FONT_SIZE_PT,
)
from app.modules.kdp_validation.schemas import (
    EbookImageInfo,
    EbookLinkInfo,
    EbookValidationRequest,
    Severity,
    ValidationStatus,
)


@pytest.fixture
def validator() -> EbookValidator:
    return EbookValidator()


def _make_request(**overrides) -> EbookValidationRequest:
    """Create a valid-by-default ebook validation request."""
    defaults = dict(
        has_ncx_toc=True,
        has_html_toc=True,
        images=[],
        links=[],
        has_javascript=False,
        has_external_resources=False,
        min_font_size_pt=12.0,
        file_size_bytes=10 * 1024 * 1024,  # 10 MB
    )
    defaults.update(overrides)
    return EbookValidationRequest(**defaults)


# ===================================================================
# TOC validation
# ===================================================================


class TestTOC:
    def test_both_toc_present(self, validator: EbookValidator):
        req = _make_request(has_ncx_toc=True, has_html_toc=True)
        result = validator.validate(req)
        toc_issues = [i for i in result.issues if i.rule.startswith("toc_")]
        assert len(toc_issues) == 0

    def test_missing_ncx_toc_error(self, validator: EbookValidator):
        req = _make_request(has_ncx_toc=False)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "toc_ncx"]
        assert len(errors) == 1
        assert errors[0].severity == Severity.ERROR

    def test_missing_html_toc_warning(self, validator: EbookValidator):
        req = _make_request(has_html_toc=False)
        result = validator.validate(req)
        warnings = [i for i in result.issues if i.rule == "toc_html"]
        assert len(warnings) == 1
        assert warnings[0].severity == Severity.WARNING

    def test_both_toc_missing(self, validator: EbookValidator):
        req = _make_request(has_ncx_toc=False, has_html_toc=False)
        result = validator.validate(req)
        toc_issues = [i for i in result.issues if i.rule.startswith("toc_")]
        assert len(toc_issues) == 2


# ===================================================================
# Image validation
# ===================================================================


class TestImages:
    def test_valid_images(self, validator: EbookValidator):
        images = [
            EbookImageInfo(filename="cover.jpg", format="JPEG", size_bytes=500_000, dpi=150),
            EbookImageInfo(filename="chart.png", format="PNG", size_bytes=1_000_000, dpi=96),
        ]
        req = _make_request(images=images)
        result = validator.validate(req)
        img_errors = [i for i in result.issues if i.rule.startswith("ebook_image")]
        assert len(img_errors) == 0

    def test_invalid_image_format(self, validator: EbookValidator):
        images = [
            EbookImageInfo(filename="graphic.bmp", format="BMP", size_bytes=100_000),
        ]
        req = _make_request(images=images)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "ebook_image_format"]
        assert len(errors) == 1
        assert errors[0].severity == Severity.ERROR

    def test_oversized_image(self, validator: EbookValidator):
        images = [
            EbookImageInfo(
                filename="huge.jpg",
                format="JPEG",
                size_bytes=MAX_EBOOK_IMAGE_SIZE_BYTES + 1,
            ),
        ]
        req = _make_request(images=images)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "ebook_image_size"]
        assert len(errors) == 1

    def test_image_at_max_size(self, validator: EbookValidator):
        images = [
            EbookImageInfo(
                filename="exact.jpg",
                format="JPEG",
                size_bytes=MAX_EBOOK_IMAGE_SIZE_BYTES,
            ),
        ]
        req = _make_request(images=images)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "ebook_image_size"]
        assert len(errors) == 0

    def test_low_dpi_warning(self, validator: EbookValidator):
        images = [
            EbookImageInfo(filename="low.jpg", format="JPEG", size_bytes=100_000, dpi=50),
        ]
        req = _make_request(images=images)
        result = validator.validate(req)
        warnings = [i for i in result.issues if i.rule == "ebook_image_dpi"]
        assert len(warnings) == 1
        assert warnings[0].severity == Severity.WARNING

    def test_no_dpi_skips_check(self, validator: EbookValidator):
        images = [
            EbookImageInfo(filename="nodpi.jpg", format="JPEG", size_bytes=100_000, dpi=None),
        ]
        req = _make_request(images=images)
        result = validator.validate(req)
        warnings = [i for i in result.issues if i.rule == "ebook_image_dpi"]
        assert len(warnings) == 0

    def test_multiple_image_issues(self, validator: EbookValidator):
        images = [
            EbookImageInfo(filename="bad1.bmp", format="BMP", size_bytes=6_000_000, dpi=30),
            EbookImageInfo(filename="bad2.tiff", format="TIFF", size_bytes=100, dpi=300),
        ]
        req = _make_request(images=images)
        result = validator.validate(req)
        img_issues = [i for i in result.issues if i.rule.startswith("ebook_image")]
        # bad1: format + size + dpi = 3, bad2: format = 1
        assert len(img_issues) == 4


# ===================================================================
# Link validation
# ===================================================================


class TestLinks:
    def test_valid_internal_links(self, validator: EbookValidator):
        links = [
            EbookLinkInfo(href="#chapter1", is_internal=True, is_valid=True),
            EbookLinkInfo(href="#chapter2", is_internal=True, is_valid=True),
        ]
        req = _make_request(links=links)
        result = validator.validate(req)
        link_issues = [i for i in result.issues if i.rule.startswith("ebook_link")]
        assert len(link_issues) == 0

    def test_broken_internal_link(self, validator: EbookValidator):
        links = [
            EbookLinkInfo(href="#missing", is_internal=True, is_valid=False),
        ]
        req = _make_request(links=links)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "ebook_link_broken"]
        assert len(errors) == 1
        assert errors[0].severity == Severity.ERROR

    def test_external_link_info(self, validator: EbookValidator):
        links = [
            EbookLinkInfo(href="https://example.com", is_internal=False, is_valid=True),
        ]
        req = _make_request(links=links)
        result = validator.validate(req)
        infos = [i for i in result.issues if i.rule == "ebook_link_external"]
        assert len(infos) == 1
        assert infos[0].severity == Severity.INFO

    def test_multiple_broken_links(self, validator: EbookValidator):
        links = [
            EbookLinkInfo(href="#a", is_internal=True, is_valid=False),
            EbookLinkInfo(href="#b", is_internal=True, is_valid=False),
        ]
        req = _make_request(links=links)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "ebook_link_broken"]
        assert len(errors) == 2


# ===================================================================
# Prohibited elements
# ===================================================================


class TestProhibitedElements:
    def test_no_javascript(self, validator: EbookValidator):
        req = _make_request(has_javascript=False)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "ebook_no_javascript"]
        assert len(errors) == 0

    def test_has_javascript_error(self, validator: EbookValidator):
        req = _make_request(has_javascript=True)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "ebook_no_javascript"]
        assert len(errors) == 1
        assert errors[0].severity == Severity.ERROR

    def test_no_external_resources(self, validator: EbookValidator):
        req = _make_request(has_external_resources=False)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "ebook_no_external_resources"]
        assert len(errors) == 0

    def test_has_external_resources_error(self, validator: EbookValidator):
        req = _make_request(has_external_resources=True)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "ebook_no_external_resources"]
        assert len(errors) == 1
        assert errors[0].severity == Severity.ERROR


# ===================================================================
# Font size
# ===================================================================


class TestFontSize:
    def test_adequate_font_size(self, validator: EbookValidator):
        req = _make_request(min_font_size_pt=12.0)
        result = validator.validate(req)
        warnings = [i for i in result.issues if i.rule == "ebook_font_size"]
        assert len(warnings) == 0

    def test_small_font_size_warning(self, validator: EbookValidator):
        req = _make_request(min_font_size_pt=5.0)
        result = validator.validate(req)
        warnings = [i for i in result.issues if i.rule == "ebook_font_size"]
        assert len(warnings) == 1
        assert warnings[0].severity == Severity.WARNING

    def test_font_size_at_minimum(self, validator: EbookValidator):
        req = _make_request(min_font_size_pt=RECOMMENDED_MIN_FONT_SIZE_PT)
        result = validator.validate(req)
        warnings = [i for i in result.issues if i.rule == "ebook_font_size"]
        assert len(warnings) == 0

    def test_font_size_none_skips(self, validator: EbookValidator):
        req = _make_request(min_font_size_pt=None)
        result = validator.validate(req)
        warnings = [i for i in result.issues if i.rule == "ebook_font_size"]
        assert len(warnings) == 0


# ===================================================================
# File size
# ===================================================================


class TestFileSize:
    def test_valid_file_size(self, validator: EbookValidator):
        req = _make_request(file_size_bytes=100 * 1024 * 1024)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "ebook_file_size"]
        assert len(errors) == 0

    def test_oversized_file(self, validator: EbookValidator):
        req = _make_request(file_size_bytes=MAX_EBOOK_FILE_SIZE_BYTES + 1)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "ebook_file_size"]
        assert len(errors) == 1
        assert errors[0].severity == Severity.ERROR

    def test_file_at_limit(self, validator: EbookValidator):
        req = _make_request(file_size_bytes=MAX_EBOOK_FILE_SIZE_BYTES)
        result = validator.validate(req)
        errors = [i for i in result.issues if i.rule == "ebook_file_size"]
        assert len(errors) == 0


# ===================================================================
# Overall status
# ===================================================================


class TestOverallStatus:
    def test_passes_when_all_valid(self, validator: EbookValidator):
        req = _make_request()
        result = validator.validate(req)
        assert result.status == ValidationStatus.PASSED

    def test_fails_when_missing_ncx(self, validator: EbookValidator):
        req = _make_request(has_ncx_toc=False)
        result = validator.validate(req)
        assert result.status == ValidationStatus.FAILED

    def test_warnings_when_missing_html_toc(self, validator: EbookValidator):
        req = _make_request(has_html_toc=False)
        result = validator.validate(req)
        assert result.status == ValidationStatus.WARNINGS

    def test_metadata_populated(self, validator: EbookValidator):
        images = [EbookImageInfo(filename="a.jpg", format="JPEG", size_bytes=100)]
        links = [EbookLinkInfo(href="#ch1", is_internal=True, is_valid=True)]
        req = _make_request(images=images, links=links, file_size_bytes=5000)
        result = validator.validate(req)
        assert result.metadata["image_count"] == 1
        assert result.metadata["link_count"] == 1
        assert result.metadata["file_size_bytes"] == 5000
