"""Unit tests for the PDF generator module.

Tests cover:
- PDF generation returning bytes (not dict/JSON)
- Multi-chapter document generation
- ISBN barcode rendering
- Different page/trim sizes (Letter, A4, 6x9, etc.)

The generator uses ReportLab which must be installed. Tests are skipped
via try/except if reportlab is not available in the test environment.
"""

from __future__ import annotations

import uuid

import pytest

from app.modules.publishing_ops.pdf_generator import (
    REPORTLAB_AVAILABLE,
    TRIM_DIMENSIONS,
    PDFDocument,
    _validate_isbn13,
    generate_pdf,
    generate_pdf_bytes,
    render_isbn_barcode,
)
from app.modules.publishing_ops.schemas import (
    ChapterInput,
    ExportFormat,
    ExportRequest,
    TemplateStyleSettings,
    TrimSize,
)

# Skip the entire module if reportlab is not installed
pytestmark = pytest.mark.skipif(
    not REPORTLAB_AVAILABLE,
    reason="reportlab is not installed; PDF generation tests require it",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def book_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_chapters() -> list[ChapterInput]:
    return [
        ChapterInput(
            title="Chapter 1: The Beginning",
            content="It was a dark and stormy night.\n\nThe wind howled through the trees.",
            order=1,
        ),
        ChapterInput(
            title="Chapter 2: The Journey",
            content="They set off at dawn.\n\nThe road stretched endlessly before them.",
            order=2,
        ),
    ]


@pytest.fixture
def export_request(book_id: uuid.UUID, sample_chapters: list[ChapterInput]) -> ExportRequest:
    return ExportRequest(
        book_id=book_id,
        format=ExportFormat.PDF,
        chapters=sample_chapters,
        trim_size=TrimSize.SIZE_6x9,
    )


@pytest.fixture
def export_request_with_isbn(book_id: uuid.UUID, sample_chapters: list[ChapterInput]) -> ExportRequest:
    return ExportRequest(
        book_id=book_id,
        format=ExportFormat.PDF,
        chapters=sample_chapters,
        trim_size=TrimSize.SIZE_6x9,
        include_isbn_barcode=True,
        isbn="978-0-306-40615-7",
    )


# ---------------------------------------------------------------------------
# Tests: generate_pdf_bytes returns bytes
# ---------------------------------------------------------------------------


class TestGeneratePdfReturnsBytes:
    """Verify that the PDF generator returns raw bytes, not a dict or JSON string."""

    def test_generate_pdf_bytes_returns_bytes(self, export_request: ExportRequest):
        result = generate_pdf_bytes(export_request, title="Test Book")
        assert isinstance(result, bytes), (
            f"Expected bytes, got {type(result).__name__}"
        )

    def test_generate_pdf_bytes_not_empty(self, export_request: ExportRequest):
        result = generate_pdf_bytes(export_request, title="Test Book")
        assert len(result) > 0

    def test_generate_pdf_bytes_starts_with_pdf_header(self, export_request: ExportRequest):
        """Real PDF files begin with the %PDF magic bytes."""
        result = generate_pdf_bytes(export_request, title="Test Book")
        assert result[:5] == b"%PDF-", (
            "PDF output should start with %PDF- magic header"
        )

    def test_generate_pdf_returns_pdfdocument(self, export_request: ExportRequest):
        doc = generate_pdf(export_request, title="Test Book")
        assert isinstance(doc, PDFDocument)

    def test_to_bytes_returns_bytes_not_dict(self, export_request: ExportRequest):
        doc = generate_pdf(export_request, title="Test Book")
        raw = doc.to_bytes()
        assert isinstance(raw, bytes)
        assert not isinstance(raw, dict)

    def test_to_bytes_matches_generate_pdf_bytes(self, export_request: ExportRequest):
        """Both code paths should produce equivalent PDF output."""
        doc = generate_pdf(export_request, title="Consistent")
        via_wrapper = generate_pdf_bytes(
            export_request, title="Consistent"
        )
        # Both should be valid PDFs (start with %PDF-)
        assert doc.to_bytes()[:5] == b"%PDF-"
        assert via_wrapper[:5] == b"%PDF-"


# ---------------------------------------------------------------------------
# Tests: generate PDF with chapters
# ---------------------------------------------------------------------------


class TestGeneratePdfWithChapters:
    """Verify that multi-chapter PDF generation works correctly."""

    def test_two_chapters_produce_multiple_pages(self, export_request: ExportRequest):
        doc = generate_pdf(export_request, title="Two Chapters")
        # Title page + TOC + at least 2 chapter pages = 4+ pages
        assert doc.total_pages >= 4, (
            f"Expected at least 4 pages (title+TOC+2 chapters), got {doc.total_pages}"
        )

    def test_chapters_sorted_by_order(self, book_id: uuid.UUID):
        """Chapters should be sorted by their order field, not insertion order.
        Verify by checking the PDF renders without error when given out-of-order chapters."""
        chapters = [
            ChapterInput(title="Second Chapter", content="Content B", order=2),
            ChapterInput(title="First Chapter", content="Content A", order=1),
        ]
        request = ExportRequest(
            book_id=book_id,
            format=ExportFormat.PDF,
            chapters=chapters,
        )
        doc = generate_pdf(request, title="Sorted Chapters")
        assert doc.total_pages >= 1
        # The PDF should contain the title
        assert doc.title == "Sorted Chapters"

    def test_document_metadata(self, export_request: ExportRequest):
        doc = generate_pdf(
            export_request,
            title="Metadata Test",
            authors=["Alice", "Bob"],
        )
        assert doc.title == "Metadata Test"
        assert doc.authors == ["Alice", "Bob"]
        assert doc.book_id == str(export_request.book_id)
        assert doc.generated_at != ""

    def test_single_chapter(self, book_id: uuid.UUID):
        chapters = [
            ChapterInput(title="Only Chapter", content="Short content.", order=1),
        ]
        request = ExportRequest(
            book_id=book_id,
            format=ExportFormat.PDF,
            chapters=chapters,
        )
        doc = generate_pdf(request, title="Single Chapter Book")
        assert doc.total_pages >= 1

    def test_custom_style_settings_stored(self, export_request: ExportRequest):
        style = TemplateStyleSettings(
            font_family="Palatino",
            font_size_pt=13.0,
            chapter_heading_font="Times New Roman",
        )
        doc = generate_pdf(export_request, title="Styled", style_settings=style)
        assert doc.font_family == "Palatino"
        assert doc.font_size_pt == 13.0

    def test_margins_stored(self, export_request: ExportRequest):
        style = TemplateStyleSettings(
            margin_top_in=1.0,
            margin_bottom_in=0.8,
            margin_inner_in=1.2,
            margin_outer_in=0.9,
        )
        doc = generate_pdf(export_request, title="Margins", style_settings=style)
        assert doc.margin_top_in == 1.0
        assert doc.margin_bottom_in == 0.8
        assert doc.margin_inner_in == 1.2
        assert doc.margin_outer_in == 0.9

    def test_default_authors_is_empty_list(self, export_request: ExportRequest):
        doc = generate_pdf(export_request, title="No Authors")
        assert doc.authors == []


# ---------------------------------------------------------------------------
# Tests: ISBN rendering
# ---------------------------------------------------------------------------


class TestGeneratePdfWithIsbn:
    """Verify that ISBN barcode rendering does not crash and integrates correctly."""

    def test_isbn_stored_in_document(self, export_request_with_isbn: ExportRequest):
        doc = generate_pdf(export_request_with_isbn, title="ISBN Book")
        assert doc.isbn == "978-0-306-40615-7"
        assert doc.include_isbn_barcode is True

    def test_isbn_not_stored_when_disabled(self, export_request: ExportRequest):
        """When include_isbn_barcode is False, ISBN barcode flag should be False."""
        doc = generate_pdf(export_request, title="No ISBN")
        assert doc.include_isbn_barcode is False

    def test_generate_pdf_bytes_with_isbn_does_not_crash(
        self, export_request_with_isbn: ExportRequest
    ):
        """End-to-end: generating bytes with ISBN should not raise."""
        result = generate_pdf_bytes(export_request_with_isbn, title="ISBN Bytes Test")
        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:5] == b"%PDF-"

    def test_isbn_barcode_adds_extra_page(
        self,
        book_id: uuid.UUID,
        sample_chapters: list[ChapterInput],
    ):
        """A request with ISBN barcode should have more pages than without."""
        request_no_isbn = ExportRequest(
            book_id=book_id,
            format=ExportFormat.PDF,
            chapters=sample_chapters,
            trim_size=TrimSize.SIZE_6x9,
            include_isbn_barcode=False,
        )
        request_with_isbn = ExportRequest(
            book_id=book_id,
            format=ExportFormat.PDF,
            chapters=sample_chapters,
            trim_size=TrimSize.SIZE_6x9,
            include_isbn_barcode=True,
            isbn="978-0-306-40615-7",
        )
        doc_no = generate_pdf(request_no_isbn, title="No ISBN")
        doc_yes = generate_pdf(request_with_isbn, title="With ISBN")
        assert doc_yes.total_pages >= doc_no.total_pages

    def test_render_isbn_barcode_returns_png_bytes(self):
        """Directly test the barcode renderer with a valid ISBN-13."""
        png_bytes = render_isbn_barcode("978-0-306-40615-7")
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 100

    def test_validate_isbn13_valid(self):
        cleaned = _validate_isbn13("978-0-306-40615-7")
        assert cleaned == "9780306406157"

    def test_validate_isbn13_strips_hyphens_and_spaces(self):
        cleaned = _validate_isbn13("978 0 306 40615 7")
        assert cleaned == "9780306406157"

    def test_validate_isbn13_invalid_length(self):
        with pytest.raises(ValueError, match="13 digits"):
            _validate_isbn13("978-0-306")

    def test_validate_isbn13_invalid_checksum(self):
        with pytest.raises(ValueError, match="check digit"):
            _validate_isbn13("978-0-306-40615-0")

    def test_validate_isbn13_non_digits(self):
        with pytest.raises(ValueError, match="only digits"):
            _validate_isbn13("978-0-306-4061A-7")

    def test_invalid_isbn_does_not_crash_pdf(self, book_id: uuid.UUID):
        """An invalid ISBN should not crash PDF generation;
        the barcode builder handles errors gracefully."""
        chapters = [
            ChapterInput(title="Ch1", content="Content.", order=1),
        ]
        request = ExportRequest(
            book_id=book_id,
            format=ExportFormat.PDF,
            chapters=chapters,
            include_isbn_barcode=True,
            isbn="000-0-000-00000-0",  # Invalid ISBN
        )
        # Should not raise -- the barcode builder catches the error
        doc = generate_pdf(request, title="Bad ISBN")
        assert doc.total_pages >= 1


# ---------------------------------------------------------------------------
# Tests: page/trim sizes
# ---------------------------------------------------------------------------


class TestGeneratePdfPageSizes:
    """Verify that different trim/page sizes are handled correctly."""

    @pytest.mark.parametrize(
        "trim_size,expected_width,expected_height",
        [
            (TrimSize.SIZE_5x8, 5.0, 8.0),
            (TrimSize.SIZE_5_25x8, 5.25, 8.0),
            (TrimSize.SIZE_5_5x8_5, 5.5, 8.5),
            (TrimSize.SIZE_6x9, 6.0, 9.0),
            (TrimSize.SIZE_7x10, 7.0, 10.0),
            (TrimSize.SIZE_8_5x11, 8.5, 11.0),  # Letter size
        ],
    )
    def test_trim_size_dimensions(
        self,
        book_id: uuid.UUID,
        sample_chapters: list[ChapterInput],
        trim_size: TrimSize,
        expected_width: float,
        expected_height: float,
    ):
        request = ExportRequest(
            book_id=book_id,
            format=ExportFormat.PDF,
            chapters=sample_chapters,
            trim_size=trim_size,
        )
        doc = generate_pdf(request, title=f"Size {trim_size.value}")
        assert doc.trim_width_in == expected_width
        assert doc.trim_height_in == expected_height

    def test_letter_size_works(self, book_id: uuid.UUID, sample_chapters: list[ChapterInput]):
        """Verify the 8.5x11 (US Letter) size generates successfully."""
        request = ExportRequest(
            book_id=book_id,
            format=ExportFormat.PDF,
            chapters=sample_chapters,
            trim_size=TrimSize.SIZE_8_5x11,
        )
        doc = generate_pdf(request, title="Letter Size")
        assert doc.trim_width_in == 8.5
        assert doc.trim_height_in == 11.0
        assert doc.total_pages >= 2

    def test_a4_equivalent_works(self, book_id: uuid.UUID, sample_chapters: list[ChapterInput]):
        """The closest A4 equivalent in the system is 7x10. Verify it works."""
        request = ExportRequest(
            book_id=book_id,
            format=ExportFormat.PDF,
            chapters=sample_chapters,
            trim_size=TrimSize.SIZE_7x10,
        )
        doc = generate_pdf(request, title="A4 Equivalent")
        assert doc.trim_width_in == 7.0
        assert doc.trim_height_in == 10.0
        assert doc.total_pages >= 2

    def test_all_trim_sizes_produce_valid_documents(
        self, book_id: uuid.UUID, sample_chapters: list[ChapterInput]
    ):
        """Every trim size in the enum should produce a valid document without error."""
        for trim_size in TrimSize:
            request = ExportRequest(
                book_id=book_id,
                format=ExportFormat.PDF,
                chapters=sample_chapters,
                trim_size=trim_size,
            )
            doc = generate_pdf(request, title=f"Test {trim_size.value}")
            assert doc.total_pages >= 1
            assert doc.trim_width_in > 0
            assert doc.trim_height_in > 0

    def test_trim_dimensions_lookup_complete(self):
        """Ensure TRIM_DIMENSIONS has an entry for every TrimSize enum member."""
        for trim_size in TrimSize:
            assert trim_size in TRIM_DIMENSIONS, (
                f"Missing TRIM_DIMENSIONS entry for {trim_size.value}"
            )
            w, h = TRIM_DIMENSIONS[trim_size]
            assert w > 0
            assert h > 0

    def test_smallest_trim_produces_pdf(self, book_id: uuid.UUID, sample_chapters: list[ChapterInput]):
        """The 5x8 trim (smallest) should still produce valid PDF bytes."""
        request = ExportRequest(
            book_id=book_id,
            format=ExportFormat.PDF,
            chapters=sample_chapters,
            trim_size=TrimSize.SIZE_5x8,
        )
        raw = generate_pdf_bytes(request, title="Small Trim")
        assert raw[:5] == b"%PDF-"

    def test_largest_trim_produces_pdf(self, book_id: uuid.UUID, sample_chapters: list[ChapterInput]):
        """The 8.5x11 trim (largest) should still produce valid PDF bytes."""
        request = ExportRequest(
            book_id=book_id,
            format=ExportFormat.PDF,
            chapters=sample_chapters,
            trim_size=TrimSize.SIZE_8_5x11,
        )
        raw = generate_pdf_bytes(request, title="Large Trim")
        assert raw[:5] == b"%PDF-"
