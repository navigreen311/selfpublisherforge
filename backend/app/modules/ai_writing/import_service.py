"""Import service for manuscripts.

Supports importing manuscripts from uploaded files and automatically
splitting them into chapters:
- DOCX (python-docx) — split on Heading 1 styles
- EPUB (ebooklib) — extract chapters from spine
- TXT — split on "Chapter" headings or double newlines
- Markdown — split on ``#`` headings

Each import function returns the created :class:`Manuscript` with its
:class:`Chapter` records persisted to the database.
"""

from __future__ import annotations

import io
import json
import logging
import re
import uuid as _uuid
from typing import BinaryIO

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.content import (
    Chapter,
    ChapterStatus,
    ContentType,
    Manuscript,
    ManuscriptStatus,
)
from app.modules.ai_writing.tiptap_converter import text_to_tiptap

logger = logging.getLogger(__name__)

SUPPORTED_IMPORT_EXTENSIONS: set[str] = {".docx", ".epub", ".txt", ".md", ".markdown"}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def import_manuscript(
    db: AsyncSession,
    org_id: _uuid.UUID,
    user_id: _uuid.UUID,
    file: BinaryIO,
    filename: str,
) -> Manuscript:
    """Parse an uploaded file into a :class:`Manuscript` with chapters.

    Parameters
    ----------
    db:
        Async database session.
    org_id:
        Organisation that owns the manuscript.
    user_id:
        User performing the import (used for logging/audit).
    file:
        File-like object with the uploaded content.
    filename:
        Original filename (used to detect the format from the extension).

    Returns
    -------
    Manuscript
        The newly created manuscript, already flushed (but not yet committed).

    Raises
    ------
    AppException
        400 for unsupported format or missing optional library.
    """
    ext = _get_extension(filename)
    if ext not in SUPPORTED_IMPORT_EXTENSIONS:
        raise AppException(
            status_code=400,
            code="UNSUPPORTED_FORMAT",
            message=(
                f"Unsupported import format: '{ext}'. " f"Supported: {', '.join(sorted(SUPPORTED_IMPORT_EXTENSIONS))}"
            ),
        )

    raw_bytes = file.read() if hasattr(file, "read") else file  # type: ignore[arg-type]
    if isinstance(raw_bytes, memoryview):
        raw_bytes = bytes(raw_bytes)

    # Parse the file into a title and list of (chapter_title, chapter_text) tuples
    if ext == ".docx":
        title, raw_chapters = _parse_docx(raw_bytes)
    elif ext == ".epub":
        title, raw_chapters = _parse_epub(raw_bytes)
    elif ext in (".txt",):
        title, raw_chapters = _parse_txt(raw_bytes)
    elif ext in (".md", ".markdown"):
        title, raw_chapters = _parse_markdown(raw_bytes)
    else:
        raise AppException(status_code=400, code="UNSUPPORTED_FORMAT", message="Unknown format")

    # Fallback title from filename
    if not title:
        title = _title_from_filename(filename)

    # Create the Manuscript
    manuscript = Manuscript(
        id=_uuid.uuid4(),
        book_id=None,  # type: ignore[arg-type]  — will be linked later or left orphaned for import
        content_type=ContentType.FICTION,
        status=ManuscriptStatus.DRAFT,
    )
    db.add(manuscript)
    await db.flush()

    # Create Chapter records
    for idx, (ch_title, ch_text) in enumerate(raw_chapters):
        word_count = len(ch_text.split()) if ch_text else 0

        # Store content as TipTap JSON so the editor can load it directly
        tiptap_content = text_to_tiptap(ch_text)

        chapter = Chapter(
            id=_uuid.uuid4(),
            manuscript_id=manuscript.id,
            title=ch_title or f"Chapter {idx + 1}",
            order_index=idx,
            content=json.dumps(tiptap_content),
            word_count=word_count,
            status=ChapterStatus.DRAFT,
        )
        db.add(chapter)

    await db.flush()
    await db.refresh(manuscript)

    logger.info(
        "Imported manuscript %s (%d chapters) from '%s' for org %s",
        manuscript.id,
        len(raw_chapters),
        filename,
        org_id,
    )
    return manuscript


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------


def _get_extension(filename: str) -> str:
    """Return the lowercased file extension including the leading dot."""
    idx = filename.rfind(".")
    if idx == -1:
        return ""
    return filename[idx:].lower()


def _title_from_filename(filename: str) -> str:
    """Derive a manuscript title from the filename."""
    name = filename.rsplit(".", 1)[0] if "." in filename else filename
    # Replace underscores and hyphens with spaces
    name = re.sub(r"[_-]+", " ", name)
    return name.strip().title() or "Imported Manuscript"


# ---------------------------------------------------------------------------
# DOCX parser
# ---------------------------------------------------------------------------


def _parse_docx(raw_bytes: bytes) -> tuple[str, list[tuple[str, str]]]:
    """Parse a DOCX file into chapters by splitting on Heading 1 styles."""
    try:
        from docx import Document
    except ImportError:
        raise AppException(
            status_code=400,
            code="LIBRARY_NOT_AVAILABLE",
            message=("DOCX import requires the 'python-docx' library. " "Install it with: pip install python-docx"),
        ) from None

    buf = io.BytesIO(raw_bytes)
    doc = Document(buf)

    title = ""
    chapters: list[tuple[str, str]] = []
    current_title = ""
    current_paragraphs: list[str] = []

    for para in doc.paragraphs:
        style_name = (para.style.name or "").lower() if para.style else ""
        text = para.text.strip()

        # Detect heading 1 as chapter boundary
        if "heading 1" in style_name or style_name == "title":
            # If this is the very first heading and we have no title, use it as the book title
            if not title and style_name == "title":
                title = text
                continue

            # Save previous chapter
            if current_title or current_paragraphs:
                chapters.append((current_title, "\n\n".join(current_paragraphs)))

            current_title = text
            current_paragraphs = []
        elif text:
            current_paragraphs.append(text)

    # Save last chapter
    if current_title or current_paragraphs:
        chapters.append((current_title, "\n\n".join(current_paragraphs)))

    # If no chapters were detected, treat the whole document as one chapter
    if not chapters:
        all_text = "\n\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())
        chapters = [("Chapter 1", all_text)]

    return title, chapters


# ---------------------------------------------------------------------------
# EPUB parser
# ---------------------------------------------------------------------------


def _parse_epub(raw_bytes: bytes) -> tuple[str, list[tuple[str, str]]]:
    """Parse an EPUB file into chapters from its spine."""
    try:
        from ebooklib import epub
    except ImportError:
        raise AppException(
            status_code=400,
            code="LIBRARY_NOT_AVAILABLE",
            message=("EPUB import requires the 'ebooklib' library. " "Install it with: pip install ebooklib"),
        ) from None

    buf = io.BytesIO(raw_bytes)
    book = epub.read_epub(buf)

    title = book.get_metadata("DC", "title")
    book_title = title[0][0] if title else ""

    chapters: list[tuple[str, str]] = []
    chapter_num = 0

    for item in book.get_items_of_type(9):  # ITEM_DOCUMENT = 9
        content = item.get_content()
        if not content:
            continue

        html_text = content.decode("utf-8", errors="replace")

        # Extract title from first heading if present
        heading_match = re.search(r"<h[1-3][^>]*>(.*?)</h[1-3]>", html_text, re.DOTALL | re.IGNORECASE)
        ch_title = ""
        if heading_match:
            ch_title = re.sub(r"<[^>]+>", "", heading_match.group(1)).strip()

        # Extract body text
        body_match = re.search(r"<body[^>]*>(.*?)</body>", html_text, re.DOTALL | re.IGNORECASE)
        body_html = body_match.group(1) if body_match else html_text

        # Strip HTML tags for plain text extraction
        plain_text = _strip_html_tags(body_html)
        if not plain_text.strip():
            continue

        chapter_num += 1
        if not ch_title:
            ch_title = f"Chapter {chapter_num}"

        chapters.append((ch_title, plain_text.strip()))

    if not chapters:
        chapters = [("Chapter 1", "")]

    return book_title, chapters


def _strip_html_tags(html_text: str) -> str:
    """Remove HTML tags and decode entities, preserving paragraph breaks."""
    import html as _html_module

    # Convert block-level tags to double newlines
    text = re.sub(r"</(?:p|div|h[1-6]|blockquote|li|tr)>", "\n\n", html_text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    # Remove all remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode HTML entities
    text = _html_module.unescape(text)
    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# TXT parser
# ---------------------------------------------------------------------------


def _parse_txt(raw_bytes: bytes) -> tuple[str, list[tuple[str, str]]]:
    """Parse a plain-text file into chapters.

    Splitting heuristics (in priority order):
    1. Lines matching ``Chapter N`` (case-insensitive)
    2. Lines of ``===`` or ``---`` separators
    3. Fallback: entire file as one chapter
    """
    text = raw_bytes.decode("utf-8", errors="replace")
    title = ""

    # Try to split on "Chapter N" patterns
    chapter_pattern = re.compile(
        r"^(?:chapter\s+\d+[:\.\s]*.*|CHAPTER\s+\d+[:\.\s]*.*)$",
        re.MULTILINE | re.IGNORECASE,
    )
    matches = list(chapter_pattern.finditer(text))

    if matches:
        chapters: list[tuple[str, str]] = []
        for i, match in enumerate(matches):
            ch_title = match.group(0).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            ch_text = text[start:end].strip()
            chapters.append((ch_title, ch_text))

        # Text before first chapter heading might be a title/preamble
        preamble = text[: matches[0].start()].strip()
        if preamble:
            # Use first non-empty line as title
            first_line = preamble.split("\n")[0].strip()
            if first_line:
                title = first_line

        return title, chapters

    # Try separator-based splitting (===, ---, ***)
    separator_pattern = re.compile(r"^[=\-\*]{3,}\s*$", re.MULTILINE)
    parts = separator_pattern.split(text)
    if len(parts) > 1:
        chapters = []
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue
            # Use first line of each section as chapter title
            lines = part.split("\n", 1)
            ch_title = lines[0].strip()
            ch_text = lines[1].strip() if len(lines) > 1 else ""
            chapters.append((ch_title, ch_text))
        return title, chapters if chapters else [("Chapter 1", text.strip())]

    # Fallback: single chapter
    return title, [("Chapter 1", text.strip())]


# ---------------------------------------------------------------------------
# Markdown parser
# ---------------------------------------------------------------------------


def _parse_markdown(raw_bytes: bytes) -> tuple[str, list[tuple[str, str]]]:
    """Parse a Markdown file into chapters by splitting on ``#`` headings.

    The first ``#`` heading is treated as the book title. ``##`` headings
    become chapter boundaries.
    """
    text = raw_bytes.decode("utf-8", errors="replace")
    title = ""

    # Find all headings
    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    matches = list(heading_pattern.finditer(text))

    if not matches:
        return title, [("Chapter 1", text.strip())]

    # Use first h1 as book title
    first = matches[0]
    if len(first.group(1)) == 1:
        title = first.group(2).strip()
        matches = matches[1:]  # Remove the title heading

    if not matches:
        # Only had a title, rest is one chapter
        content_start = first.end()
        return title, [("Chapter 1", text[content_start:].strip())]

    chapters: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        ch_title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        ch_text = text[start:end].strip()
        chapters.append((ch_title, ch_text))

    return title, chapters
