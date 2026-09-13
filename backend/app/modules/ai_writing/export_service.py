"""Export service for manuscripts.

Supports exporting manuscripts in multiple formats:
- DOCX (python-docx)
- EPUB (ebooklib)
- PDF (reportlab)
- TXT (plain text)
- Markdown

Each export function returns bytes suitable for streaming as a file download.
Uses graceful fallbacks when optional libraries are not installed.
"""

from __future__ import annotations

import io
import logging
import re
import uuid as _uuid
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.content import Chapter, Manuscript
from app.modules.ai_writing.tiptap_converter import tiptap_to_html, tiptap_to_text

logger = logging.getLogger(__name__)

ExportFormat = Literal["docx", "epub", "pdf", "txt", "markdown"]

SUPPORTED_FORMATS: set[str] = {"docx", "epub", "pdf", "txt", "markdown"}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def export_manuscript(
    db: AsyncSession,
    manuscript_id: _uuid.UUID,
    format: ExportFormat,  # — shadows built-in intentionally for API clarity
) -> tuple[bytes, str, str]:
    """Export a full manuscript in the requested format.

    Parameters
    ----------
    db:
        Async database session.
    manuscript_id:
        UUID of the manuscript to export.
    format:
        One of ``'docx'``, ``'epub'``, ``'pdf'``, ``'txt'``, ``'markdown'``.

    Returns
    -------
    tuple[bytes, str, str]
        ``(file_bytes, filename, content_type)`` ready for a streaming response.

    Raises
    ------
    AppException
        404 if the manuscript is not found; 400 for unsupported format or
        missing optional library.
    """
    if format not in SUPPORTED_FORMATS:
        raise AppException(
            status_code=400,
            code="UNSUPPORTED_FORMAT",
            message=f"Unsupported export format: {format}. Supported: {', '.join(sorted(SUPPORTED_FORMATS))}",
        )

    manuscript, chapters = await _load_manuscript_with_chapters(db, manuscript_id)
    title = _manuscript_title(manuscript, chapters)
    safe_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_") or "manuscript"

    if format == "docx":
        data = _export_docx(title, chapters)
        return data, f"{safe_title}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if format == "epub":
        data = _export_epub(title, chapters)
        return data, f"{safe_title}.epub", "application/epub+zip"
    if format == "pdf":
        data = _export_pdf(title, chapters)
        return data, f"{safe_title}.pdf", "application/pdf"
    if format == "txt":
        data = _export_txt(title, chapters)
        return data, f"{safe_title}.txt", "text/plain; charset=utf-8"
    if format == "markdown":
        data = _export_markdown(title, chapters)
        return data, f"{safe_title}.md", "text/markdown; charset=utf-8"

    # Unreachable, but satisfies type checker
    raise AppException(status_code=400, code="UNSUPPORTED_FORMAT", message="Unknown format")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _load_manuscript_with_chapters(
    db: AsyncSession, manuscript_id: _uuid.UUID
) -> tuple[Manuscript, list[Chapter]]:
    """Fetch the manuscript and its ordered chapters."""
    result = await db.execute(select(Manuscript).where(Manuscript.id == manuscript_id))
    manuscript = result.scalar_one_or_none()
    if not manuscript:
        raise AppException(
            status_code=404,
            code="MANUSCRIPT_NOT_FOUND",
            message=f"Manuscript {manuscript_id} not found.",
        )

    ch_result = await db.execute(
        select(Chapter).where(Chapter.manuscript_id == manuscript_id).order_by(Chapter.order_index)
    )
    chapters = list(ch_result.scalars().all())
    return manuscript, chapters


def _manuscript_title(manuscript: Manuscript, chapters: list[Chapter]) -> str:
    """Derive a human-readable title for the manuscript."""
    # The Manuscript model doesn't have a dedicated title column; derive from
    # the associated book relationship or fall back to a generic name.
    if hasattr(manuscript, "book") and manuscript.book and hasattr(manuscript.book, "title"):
        return manuscript.book.title or "Untitled Manuscript"
    return "Untitled Manuscript"


def _chapter_plain_text(chapter: Chapter) -> str:
    """Extract plain text from a chapter's content (which may be TipTap JSON or plain text)."""
    content = chapter.content
    if not content:
        return ""
    # Try to detect if content is TipTap JSON
    if isinstance(content, str) and content.strip().startswith("{"):
        try:
            import json

            parsed = json.loads(content)
            if isinstance(parsed, dict) and parsed.get("type") == "doc":
                return tiptap_to_text(parsed)
        except (json.JSONDecodeError, TypeError):
            pass
    return tiptap_to_text(content) if isinstance(content, dict) else content


def _chapter_html(chapter: Chapter) -> str:
    """Extract HTML from a chapter's content."""
    content = chapter.content
    if not content:
        return ""
    if isinstance(content, str) and content.strip().startswith("{"):
        try:
            import json

            parsed = json.loads(content)
            if isinstance(parsed, dict) and parsed.get("type") == "doc":
                return tiptap_to_html(parsed)
        except (json.JSONDecodeError, TypeError):
            pass
    if isinstance(content, dict):
        return tiptap_to_html(content)
    # Already plain text or HTML — wrap in <p> if not already HTML
    if "<" in content:
        return content
    return f"<p>{content}</p>"


# ---------------------------------------------------------------------------
# Format-specific exporters
# ---------------------------------------------------------------------------


def _export_docx(title: str, chapters: list[Chapter]) -> bytes:
    """Export to DOCX using python-docx."""
    try:
        from docx import Document
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.shared import Inches, Pt
    except ImportError:
        raise AppException(
            status_code=400,
            code="LIBRARY_NOT_AVAILABLE",
            message=("DOCX export requires the 'python-docx' library. " "Install it with: pip install python-docx"),
        ) from None

    doc = Document()

    # -- Title page --
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_para.add_run(title)
    title_run.bold = True
    title_run.font.size = Pt(28)
    doc.add_page_break()

    # -- Chapters --
    for chapter in chapters:
        doc.add_heading(chapter.title, level=1)
        text = _chapter_plain_text(chapter)
        if text:
            # Split into paragraphs to maintain structure
            paragraphs = text.split("\n\n")
            for para_text in paragraphs:
                para_text = para_text.strip()
                if para_text:
                    para = doc.add_paragraph(para_text)
                    para.paragraph_format.first_line_indent = Inches(0.5)
        doc.add_page_break()

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _export_epub(title: str, chapters: list[Chapter]) -> bytes:
    """Export to EPUB using ebooklib."""
    try:
        from ebooklib import epub
    except ImportError:
        raise AppException(
            status_code=400,
            code="LIBRARY_NOT_AVAILABLE",
            message=("EPUB export requires the 'ebooklib' library. " "Install it with: pip install ebooklib"),
        ) from None

    book = epub.EpubBook()
    book.set_identifier(f"spf-{_uuid.uuid4()}")
    book.set_title(title)
    book.set_language("en")

    # Default CSS for chapters
    style = epub.EpubItem(
        uid="style",
        file_name="style/default.css",
        media_type="text/css",
        content=b"""
body { font-family: Georgia, serif; line-height: 1.6; margin: 1em; }
h1 { text-align: center; margin-top: 2em; }
p { text-indent: 1.5em; margin: 0.5em 0; }
""",
    )
    book.add_item(style)

    # Title page
    title_chapter = epub.EpubHtml(
        title="Title Page",
        file_name="title.xhtml",
        lang="en",
    )
    title_chapter.content = (
        f"<html><body><h1 style='text-align:center; margin-top:40%'>{title}</h1></body></html>"
    ).encode()
    title_chapter.add_item(style)
    book.add_item(title_chapter)

    spine: list = ["nav", title_chapter]
    toc: list = []

    for i, chapter in enumerate(chapters):
        ch = epub.EpubHtml(
            title=chapter.title,
            file_name=f"chapter_{i + 1}.xhtml",
            lang="en",
        )
        html_content = _chapter_html(chapter)
        ch.content = (f"<html><body><h1>{chapter.title}</h1>{html_content}</body></html>").encode()
        ch.add_item(style)
        book.add_item(ch)
        spine.append(ch)
        toc.append(epub.Link(f"chapter_{i + 1}.xhtml", chapter.title, f"ch{i + 1}"))

    book.toc = toc
    book.spine = spine
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    buf = io.BytesIO()
    epub.write_epub(buf, book)
    return buf.getvalue()


def _export_pdf(title: str, chapters: list[Chapter]) -> bytes:
    """Export to PDF using reportlab."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
        )
    except ImportError:
        raise AppException(
            status_code=400,
            code="LIBRARY_NOT_AVAILABLE",
            message=("PDF export requires the 'reportlab' library. " "Install it with: pip install reportlab"),
        ) from None

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
        leftMargin=1.25 * inch,
        rightMargin=1.25 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ManuscriptTitle",
        parent=styles["Title"],
        fontSize=28,
        spaceAfter=40,
        alignment=1,  # CENTER
    )
    chapter_heading_style = ParagraphStyle(
        "ChapterHeading",
        parent=styles["Heading1"],
        fontSize=18,
        spaceBefore=20,
        spaceAfter=12,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=12,
        leading=18,
        firstLineIndent=36,
        spaceAfter=6,
    )

    story: list = []

    # Title page
    story.append(Spacer(1, 3 * inch))
    story.append(Paragraph(title, title_style))
    story.append(PageBreak())

    # Chapters
    for chapter in chapters:
        story.append(Paragraph(chapter.title, chapter_heading_style))
        story.append(Spacer(1, 12))

        text = _chapter_plain_text(chapter)
        if text:
            paragraphs = text.split("\n\n")
            for para_text in paragraphs:
                para_text = para_text.strip()
                if para_text:
                    # Escape XML special characters for reportlab
                    safe_text = para_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    story.append(Paragraph(safe_text, body_style))

        story.append(PageBreak())

    doc.build(story)
    return buf.getvalue()


def _export_txt(title: str, chapters: list[Chapter]) -> bytes:
    """Export to plain text."""
    lines: list[str] = []

    # Title
    lines.append(title.upper())
    lines.append("=" * len(title))
    lines.append("")
    lines.append("")

    for i, chapter in enumerate(chapters):
        lines.append(f"{'—' * 40}")
        lines.append(f"Chapter {i + 1}: {chapter.title}")
        lines.append(f"{'—' * 40}")
        lines.append("")

        text = _chapter_plain_text(chapter)
        if text:
            lines.append(text.strip())
        lines.append("")
        lines.append("")

    return "\n".join(lines).encode("utf-8")


def _export_markdown(title: str, chapters: list[Chapter]) -> bytes:
    """Export to Markdown."""
    lines: list[str] = []

    # Title
    lines.append(f"# {title}")
    lines.append("")

    for i, chapter in enumerate(chapters):
        lines.append(f"## Chapter {i + 1}: {chapter.title}")
        lines.append("")

        text = _chapter_plain_text(chapter)
        if text:
            lines.append(text.strip())
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines).encode("utf-8")
