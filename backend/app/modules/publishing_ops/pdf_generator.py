"""PDF generator for the Publishing Operations Center.

Produces print-ready PDFs with:
- Configurable trim sizes (6x9, 5.5x8.5, etc.)
- Proper margins (inner gutter wider for binding)
- Headers, footers, and page numbers
- ISBN barcode on the last page (optional)
- Chapter heading styles from formatting templates

This module generates a lightweight HTML-based PDF representation.
In production it would delegate to a headless browser or
reportlab/weasyprint; here we produce a structured intermediate
representation that can be consumed by any PDF rendering backend.
"""

from __future__ import annotations

import io
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

from app.modules.publishing_ops.schemas import (
    ChapterInput,
    ExportRequest,
    TemplateStyleSettings,
    TrimSize,
)


# ---------- Trim size dimensions (width x height in inches) ----------

TRIM_DIMENSIONS: dict[TrimSize, tuple[float, float]] = {
    TrimSize.SIZE_5x8: (5.0, 8.0),
    TrimSize.SIZE_5_25x8: (5.25, 8.0),
    TrimSize.SIZE_5_5x8_5: (5.5, 8.5),
    TrimSize.SIZE_6x9: (6.0, 9.0),
    TrimSize.SIZE_7x10: (7.0, 10.0),
    TrimSize.SIZE_8_5x11: (8.5, 11.0),
}


@dataclass
class PDFPage:
    """Represents a single page in the PDF output."""
    page_number: int
    content_html: str
    is_chapter_start: bool = False
    header: str | None = None
    footer: str | None = None


@dataclass
class PDFDocument:
    """Structured representation of a print-ready PDF document."""
    book_id: str
    title: str
    authors: list[str]
    trim_width_in: float
    trim_height_in: float
    margin_top_in: float
    margin_bottom_in: float
    margin_inner_in: float
    margin_outer_in: float
    font_family: str
    font_size_pt: float
    line_height: float
    pages: list[PDFPage] = field(default_factory=list)
    isbn: str | None = None
    include_isbn_barcode: bool = False
    total_pages: int = 0
    generated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def to_bytes(self) -> bytes:
        """Return a byte representation (JSON) of the PDF document spec.

        In production this would be actual PDF binary content rendered by
        weasyprint / reportlab / headless Chrome.  For now we return the
        structured JSON that a renderer would consume.
        """
        return self.to_json().encode("utf-8")


def _estimate_pages_for_chapter(content: str, chars_per_page: int = 2000) -> int:
    """Rough page count estimate based on character count."""
    return max(1, (len(content) + chars_per_page - 1) // chars_per_page)


def _build_chapter_html(title: str, content: str, style: TemplateStyleSettings) -> str:
    """Build HTML for a single chapter."""
    paragraphs = content.strip().split("\n\n")
    p_tags: list[str] = []
    for para in paragraphs:
        para = para.strip()
        if para:
            if para.startswith("<"):
                p_tags.append(para)
            else:
                p_tags.append(f"<p>{para}</p>")
    body = "\n".join(p_tags)
    return (
        f'<div class="chapter">\n'
        f'  <h1 style="font-family: {style.chapter_heading_font}; '
        f'font-size: {style.chapter_heading_size_pt}pt;">{title}</h1>\n'
        f"  {body}\n"
        f"</div>"
    )


def _isbn_barcode_html(isbn: str) -> str:
    """Placeholder for ISBN barcode rendering."""
    return (
        f'<div class="isbn-barcode" style="text-align: center; margin-top: 2em;">\n'
        f"  <p><strong>ISBN: {isbn}</strong></p>\n"
        f'  <div style="border: 2px solid #000; padding: 10px; display: inline-block;">\n'
        f"    <code>|||| {isbn} ||||</code>\n"
        f"  </div>\n"
        f"</div>"
    )


def generate_pdf(
    request: ExportRequest,
    title: str = "Untitled",
    authors: list[str] | None = None,
    style_settings: TemplateStyleSettings | None = None,
) -> PDFDocument:
    """Generate a structured PDF document representation.

    Parameters
    ----------
    request:
        Export request with chapters, trim size, ISBN options, etc.
    title:
        Book title.
    authors:
        List of author names.
    style_settings:
        Typography / layout settings from a formatting template.

    Returns
    -------
    PDFDocument
        A structured document that can be serialised or rendered to
        actual PDF bytes by a rendering backend.
    """
    style = style_settings or TemplateStyleSettings()
    trim = TRIM_DIMENSIONS.get(request.trim_size, TRIM_DIMENSIONS[TrimSize.SIZE_6x9])
    chapters = sorted(request.chapters, key=lambda c: c.order)
    authors = authors or []

    doc = PDFDocument(
        book_id=str(request.book_id),
        title=title,
        authors=authors,
        trim_width_in=trim[0],
        trim_height_in=trim[1],
        margin_top_in=style.margin_top_in,
        margin_bottom_in=style.margin_bottom_in,
        margin_inner_in=style.margin_inner_in,
        margin_outer_in=style.margin_outer_in,
        font_family=style.font_family,
        font_size_pt=style.font_size_pt,
        line_height=style.line_height,
        isbn=request.isbn,
        include_isbn_barcode=request.include_isbn_barcode,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )

    page_number = 1

    # Header / footer templates
    header_template = style.header_text
    footer_template = style.footer_text

    def _resolve_template(template: str | None, page_num: int) -> str | None:
        if template is None:
            return None
        return template.replace("{title}", title).replace(
            "{author}", ", ".join(authors)
        ).replace("{page}", str(page_num))

    for ch in chapters:
        chapter_html = _build_chapter_html(ch.title, ch.content, style)
        estimated_pages = _estimate_pages_for_chapter(ch.content)

        for p in range(estimated_pages):
            header = _resolve_template(header_template, page_number)
            footer = _resolve_template(footer_template, page_number)
            if style.page_numbers:
                footer = f"{footer or ''} | Page {page_number}".strip(" |")

            doc.pages.append(
                PDFPage(
                    page_number=page_number,
                    content_html=chapter_html if p == 0 else "<p>(continued)</p>",
                    is_chapter_start=(p == 0),
                    header=header,
                    footer=footer,
                )
            )
            page_number += 1

    # ISBN barcode page
    if request.include_isbn_barcode and request.isbn:
        doc.pages.append(
            PDFPage(
                page_number=page_number,
                content_html=_isbn_barcode_html(request.isbn),
                is_chapter_start=False,
                header=None,
                footer=f"Page {page_number}" if style.page_numbers else None,
            )
        )
        page_number += 1

    doc.total_pages = len(doc.pages)
    return doc


def generate_pdf_bytes(
    request: ExportRequest,
    title: str = "Untitled",
    authors: list[str] | None = None,
    style_settings: TemplateStyleSettings | None = None,
) -> bytes:
    """Convenience wrapper that returns raw bytes."""
    doc = generate_pdf(request, title, authors, style_settings)
    return doc.to_bytes()
