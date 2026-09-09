"""Unit tests for the EPUB generator."""

from __future__ import annotations

import io
import uuid
import zipfile

import pytest

from app.modules.publishing_ops.epub_generator import (
    _build_chapter_xhtml,
    _build_container_xml,
    _build_nav_xhtml,
    _default_style,
    _wrap_paragraphs,
    generate_epub,
)
from app.modules.publishing_ops.schemas import (
    ChapterInput,
    ExportFormat,
    ExportRequest,
    TemplateStyleSettings,
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
        ChapterInput(title="Chapter 1: The Beginning", content="It was a dark and stormy night.\n\nThe wind howled.", order=1),
        ChapterInput(title="Chapter 2: The Middle", content="Things got interesting.\n\nVery interesting indeed.", order=2),
        ChapterInput(title="Chapter 3: The End", content="And they all lived happily ever after.", order=3),
    ]


@pytest.fixture
def export_request(book_id: uuid.UUID, sample_chapters: list[ChapterInput]) -> ExportRequest:
    return ExportRequest(
        book_id=book_id,
        format=ExportFormat.EPUB,
        chapters=sample_chapters,
        include_toc=True,
        include_cover=False,
    )


# ---------------------------------------------------------------------------
# Tests: helper functions
# ---------------------------------------------------------------------------

class TestDefaultStyle:
    def test_returns_css_string(self):
        css = _default_style()
        assert "body" in css
        assert "font-family" in css

    def test_uses_custom_settings(self):
        settings = TemplateStyleSettings(font_family="Garamond", font_size_pt=12.0)
        css = _default_style(settings)
        assert "Garamond" in css
        assert "12.0pt" in css

    def test_drop_cap_enabled(self):
        settings = TemplateStyleSettings(drop_cap=True)
        css = _default_style(settings)
        assert "first-letter" in css

    def test_drop_cap_disabled(self):
        settings = TemplateStyleSettings(drop_cap=False)
        css = _default_style(settings)
        assert "first-letter" not in css


class TestBuildChapterXhtml:
    def test_contains_title(self):
        xhtml = _build_chapter_xhtml("My Chapter", "<p>Content</p>")
        assert "<h1>My Chapter</h1>" in xhtml

    def test_contains_body(self):
        xhtml = _build_chapter_xhtml("Title", "<p>Hello world</p>")
        assert "<p>Hello world</p>" in xhtml

    def test_xml_escapes_title(self):
        xhtml = _build_chapter_xhtml("Tom & Jerry <3", "<p>content</p>")
        assert "Tom &amp; Jerry &lt;3" in xhtml

    def test_includes_stylesheet_link(self):
        xhtml = _build_chapter_xhtml("T", "<p>c</p>", css_path="../style.css")
        assert 'href="../style.css"' in xhtml


class TestWrapParagraphs:
    def test_wraps_plain_text(self):
        result = _wrap_paragraphs("First paragraph.\n\nSecond paragraph.")
        assert "<p>First paragraph.</p>" in result
        assert "<p>Second paragraph.</p>" in result

    def test_preserves_html(self):
        result = _wrap_paragraphs("<p>Already wrapped</p>")
        assert "<p>Already wrapped</p>" in result

    def test_empty_content(self):
        result = _wrap_paragraphs("")
        assert result == ""

    def test_escapes_special_chars(self):
        result = _wrap_paragraphs("Tom & Jerry")
        assert "Tom &amp; Jerry" in result


class TestBuildContainerXml:
    def test_valid_xml(self):
        xml = _build_container_xml()
        assert '<?xml version="1.0"' in xml
        assert "container" in xml
        assert "OEBPS/content.opf" in xml


class TestBuildNavXhtml:
    def test_creates_toc_entries(self):
        chapters = [
            ChapterInput(title="Chapter 1", content="c1", order=1),
            ChapterInput(title="Chapter 2", content="c2", order=2),
        ]
        nav = _build_nav_xhtml(chapters)
        assert "Chapter 1" in nav
        assert "Chapter 2" in nav
        assert "chapter1.xhtml" in nav
        assert "chapter2.xhtml" in nav

    def test_empty_chapters(self):
        nav = _build_nav_xhtml([])
        assert "<ol>" in nav
        assert "</ol>" in nav


# ---------------------------------------------------------------------------
# Tests: EPUB generation
# ---------------------------------------------------------------------------

class TestGenerateEpub:
    def test_returns_bytes(self, export_request: ExportRequest):
        result = generate_epub(export_request, title="Test Book")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_is_valid_zip(self, export_request: ExportRequest):
        result = generate_epub(export_request, title="Test Book")
        buf = io.BytesIO(result)
        assert zipfile.is_zipfile(buf)

    def test_contains_mimetype(self, export_request: ExportRequest):
        result = generate_epub(export_request, title="Test Book")
        buf = io.BytesIO(result)
        with zipfile.ZipFile(buf, "r") as zf:
            assert "mimetype" in zf.namelist()
            assert zf.read("mimetype") == b"application/epub+zip"

    def test_contains_container_xml(self, export_request: ExportRequest):
        result = generate_epub(export_request, title="Test Book")
        buf = io.BytesIO(result)
        with zipfile.ZipFile(buf, "r") as zf:
            assert "META-INF/container.xml" in zf.namelist()

    def test_contains_opf(self, export_request: ExportRequest):
        result = generate_epub(export_request, title="Test Book")
        buf = io.BytesIO(result)
        with zipfile.ZipFile(buf, "r") as zf:
            assert "OEBPS/content.opf" in zf.namelist()
            opf = zf.read("OEBPS/content.opf").decode("utf-8")
            assert "Test Book" in opf

    def test_contains_stylesheet(self, export_request: ExportRequest):
        result = generate_epub(export_request, title="Test Book")
        buf = io.BytesIO(result)
        with zipfile.ZipFile(buf, "r") as zf:
            assert "OEBPS/style.css" in zf.namelist()

    def test_contains_chapters(self, export_request: ExportRequest):
        result = generate_epub(export_request, title="Test Book")
        buf = io.BytesIO(result)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert "OEBPS/chapters/chapter1.xhtml" in names
            assert "OEBPS/chapters/chapter2.xhtml" in names
            assert "OEBPS/chapters/chapter3.xhtml" in names

    def test_chapter_content(self, export_request: ExportRequest):
        result = generate_epub(export_request, title="Test Book")
        buf = io.BytesIO(result)
        with zipfile.ZipFile(buf, "r") as zf:
            ch1 = zf.read("OEBPS/chapters/chapter1.xhtml").decode("utf-8")
            assert "The Beginning" in ch1
            assert "dark and stormy night" in ch1

    def test_contains_nav(self, export_request: ExportRequest):
        result = generate_epub(export_request, title="Test Book")
        buf = io.BytesIO(result)
        with zipfile.ZipFile(buf, "r") as zf:
            assert "OEBPS/nav.xhtml" in zf.namelist()
            nav = zf.read("OEBPS/nav.xhtml").decode("utf-8")
            assert "Chapter 1" in nav

    def test_without_toc(self, book_id: uuid.UUID, sample_chapters: list[ChapterInput]):
        request = ExportRequest(
            book_id=book_id,
            format=ExportFormat.EPUB,
            chapters=sample_chapters,
            include_toc=False,
        )
        result = generate_epub(request, title="No TOC")
        buf = io.BytesIO(result)
        with zipfile.ZipFile(buf, "r") as zf:
            # Nav must still exist (EPUB 3 requirement) but be empty
            nav = zf.read("OEBPS/nav.xhtml").decode("utf-8")
            assert "nav" in nav

    def test_with_cover_image(self, book_id: uuid.UUID, sample_chapters: list[ChapterInput]):
        request = ExportRequest(
            book_id=book_id,
            format=ExportFormat.EPUB,
            chapters=sample_chapters,
            include_cover=True,
        )
        fake_cover = b"\xff\xd8\xff\xe0" + b"\x00" * 100  # fake JPEG header
        result = generate_epub(request, title="With Cover", cover_image_bytes=fake_cover)
        buf = io.BytesIO(result)
        with zipfile.ZipFile(buf, "r") as zf:
            assert "OEBPS/images/cover.jpg" in zf.namelist()

    def test_without_cover_image(self, export_request: ExportRequest):
        result = generate_epub(export_request, title="No Cover")
        buf = io.BytesIO(result)
        with zipfile.ZipFile(buf, "r") as zf:
            assert "OEBPS/images/cover.jpg" not in zf.namelist()

    def test_custom_style_settings(self, export_request: ExportRequest):
        settings = TemplateStyleSettings(
            font_family="Palatino",
            font_size_pt=13.0,
            drop_cap=True,
        )
        result = generate_epub(export_request, title="Styled", style_settings=settings)
        buf = io.BytesIO(result)
        with zipfile.ZipFile(buf, "r") as zf:
            css = zf.read("OEBPS/style.css").decode("utf-8")
            assert "Palatino" in css
            assert "13.0pt" in css
            assert "first-letter" in css

    def test_chapters_sorted_by_order(self, book_id: uuid.UUID):
        chapters = [
            ChapterInput(title="Third", content="C", order=3),
            ChapterInput(title="First", content="A", order=1),
            ChapterInput(title="Second", content="B", order=2),
        ]
        request = ExportRequest(
            book_id=book_id,
            format=ExportFormat.EPUB,
            chapters=chapters,
        )
        result = generate_epub(request, title="Sorted")
        buf = io.BytesIO(result)
        with zipfile.ZipFile(buf, "r") as zf:
            ch1 = zf.read("OEBPS/chapters/chapter1.xhtml").decode("utf-8")
            assert "First" in ch1
            ch3 = zf.read("OEBPS/chapters/chapter3.xhtml").decode("utf-8")
            assert "Third" in ch3

    def test_authors_in_opf(self, export_request: ExportRequest):
        result = generate_epub(
            export_request, title="Multi Author", authors=["Alice", "Bob"]
        )
        buf = io.BytesIO(result)
        with zipfile.ZipFile(buf, "r") as zf:
            opf = zf.read("OEBPS/content.opf").decode("utf-8")
            assert "Alice" in opf
            assert "Bob" in opf

    def test_single_chapter(self, book_id: uuid.UUID):
        chapters = [ChapterInput(title="Only Chapter", content="One chapter book.", order=1)]
        request = ExportRequest(
            book_id=book_id,
            format=ExportFormat.EPUB,
            chapters=chapters,
        )
        result = generate_epub(request, title="Single")
        buf = io.BytesIO(result)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
            assert "OEBPS/chapters/chapter1.xhtml" in names
            assert "OEBPS/chapters/chapter2.xhtml" not in names
