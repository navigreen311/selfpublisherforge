"""Text Ingestion & Preprocessing — extract text from DOCX/EPUB/PDF/TXT,
normalize, and segment into sentences, paragraphs, and chapters."""

from __future__ import annotations

import io
import re
from collections.abc import Sequence
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class SegmentedText:
    """Result of ingestion: the full text broken into structural units."""

    raw_text: str = ""
    sentences: list[str] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)
    chapters: list[str] = field(default_factory=list)
    word_count: int = 0


# ---------------------------------------------------------------------------
# Sentence-splitting helpers
# ---------------------------------------------------------------------------

_SENTENCE_END = re.compile(
    r"(?<=[.!?])"  # after sentence-ending punctuation
    r'(?:\s*["\u201D])?'  # optional closing quote
    r"\s+"  # whitespace
    r'(?=[A-Z\u201C"])',  # next sentence starts with upper-case or opening quote
)

_ABBREVIATIONS = frozenset(
    [
        "mr",
        "mrs",
        "ms",
        "dr",
        "prof",
        "sr",
        "jr",
        "st",
        "vs",
        "etc",
        "inc",
        "ltd",
        "co",
        "corp",
        "dept",
        "univ",
        "approx",
        "vol",
        "no",
        "fig",
        "e.g",
        "i.e",
        "al",
    ]
)


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences using regex heuristics."""
    rough = _SENTENCE_END.split(text)
    sentences: list[str] = []
    carry = ""
    for chunk in rough:
        chunk = chunk.strip()
        if not chunk:
            continue
        combined = f"{carry} {chunk}".strip() if carry else chunk
        # If the chunk ends with an abbreviation, don't finalize yet
        last_word = combined.rstrip(".!?").rsplit(None, 1)[-1].lower().rstrip(".")
        if last_word in _ABBREVIATIONS and not chunk.endswith(("!", "?")):
            carry = combined
        else:
            sentences.append(combined)
            carry = ""
    if carry:
        sentences.append(carry)
    return [s for s in sentences if len(s.split()) >= 2]


def _split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs on blank lines or indent boundaries."""
    parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if p.strip()]


def _split_chapters(text: str) -> list[str]:
    """Best-effort chapter splitting based on common markers."""
    pattern = re.compile(
        r"^(?:chapter|part)\s+\w+",
        re.IGNORECASE | re.MULTILINE,
    )
    positions = [m.start() for m in pattern.finditer(text)]
    if len(positions) < 2:
        return [text]
    chapters: list[str] = []
    for i, pos in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(text)
        chapter = text[pos:end].strip()
        if chapter:
            chapters.append(chapter)
    return chapters


# ---------------------------------------------------------------------------
# Format-specific extractors
# ---------------------------------------------------------------------------


def _extract_txt(content: bytes) -> str:
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            return content.decode(encoding)
        except (UnicodeDecodeError, ValueError):
            continue
    return content.decode("utf-8", errors="replace")


def _extract_docx(content: bytes) -> str:
    try:
        from docx import Document  # python-docx
    except ImportError:
        raise RuntimeError("python-docx is required for DOCX ingestion") from None
    doc = Document(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def _extract_epub(content: bytes) -> str:
    try:
        import ebooklib
        from ebooklib import epub
    except ImportError:
        raise RuntimeError("ebooklib is required for EPUB ingestion") from None
    from html.parser import HTMLParser

    class _TagStripper(HTMLParser):
        def __init__(self):
            super().__init__()
            self._parts: list[str] = []

        def handle_data(self, data: str):
            self._parts.append(data)

        def get_text(self) -> str:
            return " ".join(self._parts)

    book = epub.read_epub(io.BytesIO(content))
    texts: list[str] = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        raw_html = item.get_content().decode("utf-8", errors="replace")
        stripper = _TagStripper()
        stripper.feed(raw_html)
        part = stripper.get_text().strip()
        if part:
            texts.append(part)
    return "\n\n".join(texts)


def _extract_pdf(content: bytes) -> str:
    """Extract text from PDF using a lightweight approach."""
    try:
        import io as _io

        # Try PyPDF2 / pypdf first (lightweight)
        try:
            from pypdf import PdfReader
        except ImportError:
            from PyPDF2 import PdfReader  # type: ignore[assignment,no-redef,misc]

        reader = PdfReader(_io.BytesIO(content))
        pages: list[str] = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
        return "\n\n".join(pages)
    except ImportError:
        raise RuntimeError("pypdf or PyPDF2 is required for PDF ingestion") from None


# ---------------------------------------------------------------------------
# Normalizer
# ---------------------------------------------------------------------------


def _normalize(text: str) -> str:
    """Normalize whitespace, strip control chars, unify quotes."""
    # Replace various Unicode dashes/hyphens with standard
    text = text.replace("\u2013", "-").replace("\u2014", " -- ")
    # Collapse multiple spaces
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse more than two newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

EXTRACTORS = {
    "txt": _extract_txt,
    "docx": _extract_docx,
    "epub": _extract_epub,
    "pdf": _extract_pdf,
}

MIN_WORDS = 10_000
HIGH_CONFIDENCE_WORDS = 50_000


def ingest_text(raw: str) -> SegmentedText:
    """Ingest already-extracted plain text."""
    text = _normalize(raw)
    sentences = _split_sentences(text)
    paragraphs = _split_paragraphs(text)
    chapters = _split_chapters(text)
    word_count = len(text.split())
    return SegmentedText(
        raw_text=text,
        sentences=sentences,
        paragraphs=paragraphs,
        chapters=chapters,
        word_count=word_count,
    )


def ingest_file(content: bytes, fmt: str) -> SegmentedText:
    """Ingest a manuscript file. *fmt* is one of txt/docx/epub/pdf."""
    fmt = fmt.lower().strip(".")
    extractor = EXTRACTORS.get(fmt)
    if extractor is None:
        raise ValueError(f"Unsupported format: {fmt}")
    raw = extractor(content)
    return ingest_text(raw)


def merge_segmented(segments: Sequence[SegmentedText]) -> SegmentedText:
    """Merge multiple ingested texts into one SegmentedText."""
    raw_parts: list[str] = []
    sentences: list[str] = []
    paragraphs: list[str] = []
    chapters: list[str] = []
    word_count = 0
    for seg in segments:
        raw_parts.append(seg.raw_text)
        sentences.extend(seg.sentences)
        paragraphs.extend(seg.paragraphs)
        chapters.extend(seg.chapters)
        word_count += seg.word_count
    return SegmentedText(
        raw_text="\n\n".join(raw_parts),
        sentences=sentences,
        paragraphs=paragraphs,
        chapters=chapters,
        word_count=word_count,
    )
