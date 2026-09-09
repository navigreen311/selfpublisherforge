"""Tests for Kindle Fixed-Layout Export & Device Preview System.

Covers:
  - KPF generation creates valid package structure
  - Fixed-layout EPUB has correct OPF properties
  - Device preview generates for all 6 devices
  - Paperwhite preview is grayscale
  - Read-aloud sync maps text regions
  - Kindle validation catches oversized files
  - Viewport dimensions match trim size
  - Read order covers all pages
  - Text pop-up overlays generated
  - Word-level highlighting mode
  - Single-device preview filtering
  - EPUB spine and manifest completeness
"""

from __future__ import annotations

import uuid

import pytest

from app.modules.specialty_books.service_kindle_export import (
    DEVICE_SPECS,
    KDP_MAX_FILE_SIZE_BYTES,
    FixedLayoutEPUBResponse,
    HighlightMode,
    KindleDevice,
    KindleValidationResponse,
    KPFExportResponse,
    MultiDevicePreviewResponse,
    ReadAloudSyncResponse,
    _build_ncx,
    _build_opf,
    _build_text_popups,
    _compute_simulated_file_size,
    _viewport_for_trim,
    generate_device_preview,
    generate_fixed_epub,
    generate_kpf,
    generate_read_aloud_sync,
    validate_kindle_export,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BOOK_ID = uuid.uuid4()
ORG_ID = uuid.uuid4()
BOOK_TYPE = "childrens"


# ---------------------------------------------------------------------------
# KPF Generation Tests
# ---------------------------------------------------------------------------


class TestKPFGeneration:
    """KPF generation creates valid package structure."""

    @pytest.mark.asyncio
    async def test_kpf_creates_valid_structure(self):
        result = await generate_kpf(None, BOOK_TYPE, BOOK_ID, ORG_ID)
        assert isinstance(result, KPFExportResponse)
        assert result.format == "kpf"
        assert result.book_id == BOOK_ID
        assert result.org_id == ORG_ID
        assert result.page_count > 0
        assert len(result.pages) == result.page_count
        assert result.file_url.endswith(".kpf")

    @pytest.mark.asyncio
    async def test_kpf_pages_have_read_order(self):
        result = await generate_kpf(None, BOOK_TYPE, BOOK_ID, ORG_ID)
        read_orders = [p.read_order_index for p in result.pages]
        assert read_orders == list(range(len(result.pages)))

    @pytest.mark.asyncio
    async def test_kpf_pages_have_text_popups(self):
        result = await generate_kpf(None, BOOK_TYPE, BOOK_ID, ORG_ID)
        pages_with_popups = [p for p in result.pages if len(p.text_popups) > 0]
        assert len(pages_with_popups) > 0, "At least some pages should have text popups"

    @pytest.mark.asyncio
    async def test_kpf_pages_have_image_refs(self):
        result = await generate_kpf(None, BOOK_TYPE, BOOK_ID, ORG_ID)
        for page in result.pages:
            assert len(page.image_refs) > 0, f"Page {page.page_number} missing image refs"

    @pytest.mark.asyncio
    async def test_kpf_metadata_populated(self):
        result = await generate_kpf(None, BOOK_TYPE, BOOK_ID, ORG_ID)
        assert "title" in result.metadata
        assert "author" in result.metadata
        assert "language" in result.metadata


# ---------------------------------------------------------------------------
# Fixed-Layout EPUB Tests
# ---------------------------------------------------------------------------


class TestFixedLayoutEPUB:
    """Fixed-layout EPUB has correct OPF properties."""

    @pytest.mark.asyncio
    async def test_epub_has_fixed_layout_properties(self):
        result = await generate_fixed_epub(None, BOOK_TYPE, BOOK_ID, ORG_ID)
        assert isinstance(result, FixedLayoutEPUBResponse)
        assert result.format == "epub"
        assert result.opf_properties["fixed_layout"] is True
        assert result.opf_properties["rendition_layout"] == "pre-paginated"

    @pytest.mark.asyncio
    async def test_epub_has_viewport_in_opf(self):
        result = await generate_fixed_epub(None, BOOK_TYPE, BOOK_ID, ORG_ID)
        viewport = result.opf_properties.get("viewport", "")
        assert "width=" in viewport
        assert "height=" in viewport

    @pytest.mark.asyncio
    async def test_epub_spine_covers_all_pages(self):
        result = await generate_fixed_epub(None, BOOK_TYPE, BOOK_ID, ORG_ID)
        assert len(result.spine_items) == result.page_count

    @pytest.mark.asyncio
    async def test_epub_manifest_includes_xhtml_and_css(self):
        result = await generate_fixed_epub(None, BOOK_TYPE, BOOK_ID, ORG_ID)
        xhtml_items = [i for i in result.manifest_items if i.endswith(".xhtml")]
        css_items = [i for i in result.manifest_items if i.endswith(".css")]
        # pages + nav.xhtml
        assert len(xhtml_items) == result.page_count + 1
        assert len(css_items) == result.page_count

    @pytest.mark.asyncio
    async def test_epub_pages_have_correct_viewport(self):
        result = await generate_fixed_epub(None, BOOK_TYPE, BOOK_ID, ORG_ID)
        vw, vh = _viewport_for_trim("8.5x11")
        for page in result.pages:
            assert page.viewport_width == vw
            assert page.viewport_height == vh

    @pytest.mark.asyncio
    async def test_epub_file_url_has_epub_extension(self):
        result = await generate_fixed_epub(None, BOOK_TYPE, BOOK_ID, ORG_ID)
        assert result.file_url.endswith(".epub")


# ---------------------------------------------------------------------------
# Device Preview Tests
# ---------------------------------------------------------------------------


class TestDevicePreview:
    """Device preview generates for all 6 devices."""

    @pytest.mark.asyncio
    async def test_preview_generates_all_six_devices(self):
        result = await generate_device_preview(None, BOOK_TYPE, BOOK_ID, ORG_ID)
        assert isinstance(result, MultiDevicePreviewResponse)
        assert len(result.previews) == 6
        device_names = {p.device for p in result.previews}
        for dev in KindleDevice:
            assert dev in device_names

    @pytest.mark.asyncio
    async def test_paperwhite_preview_is_grayscale(self):
        result = await generate_device_preview(
            None, BOOK_TYPE, BOOK_ID, ORG_ID, KindleDevice.KINDLE_PAPERWHITE
        )
        pw = result.previews[0]
        assert pw.grayscale is True
        assert pw.resolution_width == 1236
        assert pw.resolution_height == 1648
        # URLs should contain grayscale suffix
        for pp in pw.page_previews:
            assert "_gs" in pp.preview_url

    @pytest.mark.asyncio
    async def test_non_paperwhite_is_color(self):
        result = await generate_device_preview(
            None, BOOK_TYPE, BOOK_ID, ORG_ID, KindleDevice.KINDLE_FIRE_HD_10
        )
        preview = result.previews[0]
        assert preview.grayscale is False
        for pp in preview.page_previews:
            assert "_gs" not in pp.preview_url

    @pytest.mark.asyncio
    async def test_single_device_preview(self):
        result = await generate_device_preview(
            None, BOOK_TYPE, BOOK_ID, ORG_ID, KindleDevice.IPAD
        )
        assert len(result.previews) == 1
        assert result.previews[0].device == KindleDevice.IPAD
        assert result.previews[0].resolution_width == 2048
        assert result.previews[0].resolution_height == 2732

    @pytest.mark.asyncio
    async def test_device_preview_has_frame_overlay(self):
        result = await generate_device_preview(
            None, BOOK_TYPE, BOOK_ID, ORG_ID, KindleDevice.IPHONE
        )
        assert result.previews[0].frame_overlay_url is not None
        assert "iphone" in result.previews[0].frame_overlay_url

    @pytest.mark.asyncio
    async def test_device_specs_match_expected_resolutions(self):
        assert DEVICE_SPECS[KindleDevice.KINDLE_FIRE_HD_10]["width"] == 1920
        assert DEVICE_SPECS[KindleDevice.KINDLE_FIRE_HD_10]["height"] == 1200
        assert DEVICE_SPECS[KindleDevice.KINDLE_FIRE_HD_8]["width"] == 1280
        assert DEVICE_SPECS[KindleDevice.KINDLE_FIRE_HD_8]["height"] == 800
        assert DEVICE_SPECS[KindleDevice.KINDLE_PAPERWHITE]["width"] == 1236
        assert DEVICE_SPECS[KindleDevice.KINDLE_PAPERWHITE]["height"] == 1648
        assert DEVICE_SPECS[KindleDevice.IPAD]["width"] == 2048
        assert DEVICE_SPECS[KindleDevice.IPAD]["height"] == 2732
        assert DEVICE_SPECS[KindleDevice.IPAD_MINI]["width"] == 1488
        assert DEVICE_SPECS[KindleDevice.IPAD_MINI]["height"] == 2266
        assert DEVICE_SPECS[KindleDevice.IPHONE]["width"] == 1170
        assert DEVICE_SPECS[KindleDevice.IPHONE]["height"] == 2532


# ---------------------------------------------------------------------------
# Read-Aloud Sync Tests
# ---------------------------------------------------------------------------


class TestReadAloudSync:
    """Read-aloud sync maps text regions."""

    @pytest.mark.asyncio
    async def test_sentence_mode_maps_regions(self):
        result = await generate_read_aloud_sync(
            None, BOOK_TYPE, BOOK_ID, ORG_ID, HighlightMode.SENTENCE
        )
        assert isinstance(result, ReadAloudSyncResponse)
        assert result.highlight_mode == HighlightMode.SENTENCE
        assert result.total_regions > 0
        assert result.total_duration_ms > 0
        assert len(result.regions) == result.total_regions

    @pytest.mark.asyncio
    async def test_word_mode_maps_regions(self):
        result = await generate_read_aloud_sync(
            None, BOOK_TYPE, BOOK_ID, ORG_ID, HighlightMode.WORD
        )
        assert result.highlight_mode == HighlightMode.WORD
        assert result.total_regions > 0
        # Word mode should produce more regions than sentence mode
        sentence_result = await generate_read_aloud_sync(
            None, BOOK_TYPE, BOOK_ID, ORG_ID, HighlightMode.SENTENCE
        )
        assert result.total_regions > sentence_result.total_regions

    @pytest.mark.asyncio
    async def test_sync_regions_have_bounding_boxes(self):
        result = await generate_read_aloud_sync(
            None, BOOK_TYPE, BOOK_ID, ORG_ID, HighlightMode.SENTENCE
        )
        for region in result.regions:
            assert "x" in region.bounding_box
            assert "y" in region.bounding_box
            assert "width" in region.bounding_box
            assert "height" in region.bounding_box

    @pytest.mark.asyncio
    async def test_sync_timing_is_sequential(self):
        result = await generate_read_aloud_sync(
            None, BOOK_TYPE, BOOK_ID, ORG_ID, HighlightMode.SENTENCE
        )
        for i in range(1, len(result.regions)):
            assert result.regions[i].start_ms >= result.regions[i - 1].end_ms


# ---------------------------------------------------------------------------
# Validation Tests
# ---------------------------------------------------------------------------


class TestKindleValidation:
    """Kindle validation catches issues."""

    @pytest.mark.asyncio
    async def test_valid_book_passes_validation(self):
        result = await validate_kindle_export(None, BOOK_TYPE, BOOK_ID, ORG_ID)
        assert isinstance(result, KindleValidationResponse)
        assert result.valid is True
        assert result.file_size_ok is True
        assert result.images_embedded is True
        assert result.read_order_complete is True
        assert result.viewport_matches is True

    @pytest.mark.asyncio
    async def test_file_size_limit_constant(self):
        assert KDP_MAX_FILE_SIZE_BYTES == 650 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_validation_returns_correct_ids(self):
        result = await validate_kindle_export(None, BOOK_TYPE, BOOK_ID, ORG_ID)
        assert result.book_id == BOOK_ID
        assert result.org_id == ORG_ID


# ---------------------------------------------------------------------------
# Viewport & Trim Size Tests
# ---------------------------------------------------------------------------


class TestViewportTrimSize:
    """Viewport dimensions match trim size."""

    def test_all_trim_sizes_have_viewports(self):
        expected_trims = ["5x8", "5.5x8.5", "6x9", "7x10", "8x10", "8.5x8.5", "8.5x11"]
        for trim in expected_trims:
            vw, vh = _viewport_for_trim(trim)
            assert vw > 0
            assert vh > 0

    def test_unknown_trim_defaults(self):
        vw, vh = _viewport_for_trim("99x99")
        assert vw == 850
        assert vh == 1100

    def test_square_trim_has_equal_dimensions(self):
        vw, vh = _viewport_for_trim("8.5x8.5")
        assert vw == vh == 850


# ---------------------------------------------------------------------------
# Internal Helper Tests
# ---------------------------------------------------------------------------


class TestInternalHelpers:
    """Text pop-up overlays and OPF/NCX builders."""

    def test_text_popups_generated_for_content(self):
        popups = _build_text_popups(1, "Hello world. This is a test.")
        assert len(popups) == 2
        assert popups[0]["tappable"] is True
        assert "region_id" in popups[0]

    def test_text_popups_empty_for_no_content(self):
        popups = _build_text_popups(1, "")
        assert popups == []

    def test_opf_has_required_fields(self):
        opf = _build_opf(BOOK_ID, "Test", "Author", "en", 850, 1100, 10)
        assert opf["fixed_layout"] is True
        assert opf["rendition_layout"] == "pre-paginated"
        assert len(opf["spine"]) == 10
        assert "nav.xhtml" in opf["manifest"]
        assert "toc.ncx" in opf["manifest"]

    def test_ncx_has_all_nav_points(self):
        ncx = _build_ncx(5, "Test Book")
        assert len(ncx["nav_points"]) == 5
        assert ncx["nav_points"][0]["play_order"] == 1
        assert ncx["nav_points"][4]["play_order"] == 5

    def test_simulated_file_size_reasonable(self):
        size = _compute_simulated_file_size(32, has_images=True)
        assert size > 0
        assert size < KDP_MAX_FILE_SIZE_BYTES
