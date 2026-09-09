"""PDF generator for the Publishing Operations Center.

Produces print-ready PDFs with:
- Configurable trim sizes (6x9, 5.5x8.5, etc.)
- Proper margins (inner gutter wider for binding)
- Headers, footers, and page numbers
- ISBN barcode on the last page (optional)
- Chapter heading styles from formatting templates

Uses ReportLab for PDF rendering.
"""

from __future__ import annotations

import io
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

try:
    from reportlab.lib.colors import HexColor, black, gray, white
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
    from reportlab.lib.pagesizes import A4, inch, letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch as rl_inch
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        BaseDocTemplate,
        Frame,
        KeepTogether,
        NextPageTemplate,
        PageBreak,
        PageTemplate,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.platypus.flowables import HRFlowable

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from reportlab.graphics import renderPDF
    from reportlab.graphics.barcode.eanbc import Ean13BarcodeWidget
    from reportlab.graphics.shapes import Drawing

    BARCODE_WIDGET_AVAILABLE = True
except ImportError:
    BARCODE_WIDGET_AVAILABLE = False

import barcode
from barcode.writer import ImageWriter

from app.modules.publishing_ops.schemas import (
    ChapterInput,
    ExportRequest,
    TemplateStyleSettings,
    TrimSize,
)

logger = logging.getLogger(__name__)

if not REPORTLAB_AVAILABLE:
    logger.error("reportlab is not installed. PDF generation will not work. " "Install it with: pip install reportlab")


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
    """Represents a print-ready PDF document with actual PDF binary content."""

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
    _pdf_bytes: bytes = field(default=b"", repr=False)

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation of the document metadata."""
        d = asdict(self)
        d.pop("_pdf_bytes", None)
        return d

    def to_json(self) -> str:
        """Return a JSON string of the document metadata."""
        return json.dumps(self.to_dict(), indent=2)

    def to_bytes(self) -> bytes:
        """Return the rendered PDF binary content."""
        return self._pdf_bytes


def _estimate_pages_for_chapter(content: str, chars_per_page: int = 2000) -> int:
    """Rough page count estimate based on character count."""
    return max(1, (len(content) + chars_per_page - 1) // chars_per_page)


def _build_chapter_html(title: str, content: str, style: TemplateStyleSettings) -> str:
    """Build HTML representation for a single chapter.

    This is retained for backward compatibility and testing. The actual PDF
    rendering uses ReportLab flowables directly.
    """
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


def _validate_isbn13(isbn: str) -> str:
    """Validate and normalize an ISBN-13 string.

    Strips hyphens/spaces, checks length and digit-only content,
    and verifies the ISBN-13 check digit.

    Returns
    -------
    str
        The 13-digit normalized ISBN.

    Raises
    ------
    ValueError
        If the ISBN is invalid.
    """
    cleaned = isbn.replace("-", "").replace(" ", "").strip()
    if len(cleaned) != 13:
        raise ValueError(
            f"ISBN must be exactly 13 digits after removing hyphens/spaces, " f"got {len(cleaned)} characters: '{isbn}'"
        )
    if not cleaned.isdigit():
        raise ValueError(f"ISBN must contain only digits (and optional hyphens), got: '{isbn}'")

    total = sum(int(digit) * (1 if i % 2 == 0 else 3) for i, digit in enumerate(cleaned))
    if total % 10 != 0:
        raise ValueError(
            f"ISBN-13 check digit is invalid for '{isbn}'. "
            f"Expected checksum divisible by 10, got remainder {total % 10}."
        )

    return cleaned


def render_isbn_barcode(isbn: str) -> bytes:
    """Render an ISBN-13 as an EAN-13 barcode PNG image.

    Parameters
    ----------
    isbn:
        A valid ISBN-13 string (hyphens allowed, will be stripped).

    Returns
    -------
    bytes
        PNG image data of the rendered barcode.

    Raises
    ------
    ValueError
        If the ISBN is malformed or has an invalid check digit.
    """
    cleaned = _validate_isbn13(isbn)

    ean = barcode.get("ean13", cleaned, writer=ImageWriter())
    buffer = io.BytesIO()
    ean.write(buffer)
    return buffer.getvalue()


# ---------- ReportLab PDF rendering helpers ----------


def _get_font_name(requested_font: str) -> str:
    """Map a requested font family to a ReportLab built-in font name.

    ReportLab ships with a limited set of built-in fonts.  We map common
    font family names to their closest built-in equivalents.
    """
    font_map = {
        "georgia": "Times-Roman",
        "times": "Times-Roman",
        "times new roman": "Times-Roman",
        "serif": "Times-Roman",
        "arial": "Helvetica",
        "helvetica": "Helvetica",
        "sans-serif": "Helvetica",
        "courier": "Courier",
        "courier new": "Courier",
        "monospace": "Courier",
    }
    return font_map.get(requested_font.lower(), "Times-Roman")


def _get_bold_font_name(base_font: str) -> str:
    """Return the bold variant of a ReportLab built-in font."""
    bold_map = {
        "Times-Roman": "Times-Bold",
        "Helvetica": "Helvetica-Bold",
        "Courier": "Courier-Bold",
    }
    return bold_map.get(base_font, "Times-Bold")


def _get_italic_font_name(base_font: str) -> str:
    """Return the italic variant of a ReportLab built-in font."""
    italic_map = {
        "Times-Roman": "Times-Italic",
        "Helvetica": "Helvetica-Oblique",
        "Courier": "Courier-Oblique",
    }
    return italic_map.get(base_font, "Times-Italic")


class _PageNumberCanvas:
    """Mixin-style helper that draws headers and footers on each page.

    This is used as a canvasmaker callback within the doc build process.
    """

    def __init__(
        self,
        title: str,
        authors: list[str],
        font_name: str,
        font_size: float,
        show_page_numbers: bool,
        header_template: str | None,
        footer_template: str | None,
        margin_bottom: float,
        margin_top: float,
        margin_outer: float,
        page_width: float,
        page_height: float,
    ):
        self.title = title
        self.authors = authors
        self.font_name = font_name
        self.font_size = font_size
        self.show_page_numbers = show_page_numbers
        self.header_template = header_template
        self.footer_template = footer_template
        self.margin_bottom = margin_bottom
        self.margin_top = margin_top
        self.margin_outer = margin_outer
        self.page_width = page_width
        self.page_height = page_height


def _resolve_template(template: str | None, title: str, authors: list[str], page_num: int) -> str | None:
    """Resolve header/footer template placeholders."""
    if template is None:
        return None
    return template.replace("{title}", title).replace("{author}", ", ".join(authors)).replace("{page}", str(page_num))


def _build_isbn_barcode_flowable(isbn: str, page_width: float) -> list:
    """Build ReportLab flowables for an ISBN barcode.

    Attempts to use reportlab.graphics.barcode for a native vector barcode.
    Falls back to a placeholder rectangle with the ISBN text.
    """
    flowables = []
    flowables.append(Spacer(1, 2 * inch))

    if BARCODE_WIDGET_AVAILABLE:
        try:
            cleaned = _validate_isbn13(isbn)
            barcode_widget = Ean13BarcodeWidget(
                value=cleaned,
                barHeight=25 * mm,
                barWidth=0.33 * mm,
            )
            bounds = barcode_widget.getBounds()
            widget_width = bounds[2] - bounds[0]
            widget_height = bounds[3] - bounds[1]

            # Centre the barcode within the available page width
            avail_width = page_width - 2 * inch  # approximate content width
            drawing_width = max(widget_width, avail_width)
            drawing = Drawing(drawing_width, widget_height)
            x_offset = (drawing_width - widget_width) / 2
            barcode_widget.x = x_offset
            barcode_widget.y = 0
            drawing.add(barcode_widget)

            flowables.append(drawing)
            flowables.append(Spacer(1, 8))
            isbn_style = ParagraphStyle(
                "ISBNText",
                fontName="Helvetica-Bold",
                fontSize=11,
                alignment=TA_CENTER,
            )
            formatted_isbn = f"{cleaned[0:3]}-{cleaned[3]}-{cleaned[4:6]}-" f"{cleaned[6:12]}-{cleaned[12]}"
            flowables.append(Paragraph(f"ISBN {formatted_isbn}", isbn_style))
            return flowables
        except ValueError as exc:
            logger.warning("Invalid ISBN '%s' for barcode rendering: %s", isbn, exc)
        except Exception as exc:
            logger.warning("ReportLab barcode widget failed for '%s': %s", isbn, exc)

    # Fallback: draw a placeholder box with ISBN text
    isbn_style = ParagraphStyle(
        "ISBNPlaceholder",
        fontName="Helvetica-Bold",
        fontSize=14,
        alignment=TA_CENTER,
        borderWidth=2,
        borderColor=black,
        borderPadding=10,
    )
    flowables.append(Paragraph(f"ISBN: {isbn}", isbn_style))
    flowables.append(Spacer(1, 6))
    note_style = ParagraphStyle(
        "ISBNNote",
        fontName="Helvetica",
        fontSize=9,
        alignment=TA_CENTER,
        textColor=gray,
    )
    flowables.append(Paragraph("[Barcode rendered at print time]", note_style))
    return flowables


def _render_pdf(
    title: str,
    authors: list[str],
    chapters: list[ChapterInput],
    trim_size: tuple[float, float],
    style: TemplateStyleSettings,
    isbn: str | None,
    include_isbn_barcode: bool,
) -> tuple[bytes, int]:
    """Render a complete PDF and return (pdf_bytes, page_count).

    Parameters
    ----------
    title : str
        The book title.
    authors : list[str]
        Author name(s).
    chapters : list[ChapterInput]
        Sorted list of chapters.
    trim_size : tuple[float, float]
        (width_inches, height_inches).
    style : TemplateStyleSettings
        Typography and layout settings.
    isbn : str or None
        ISBN-13 string for barcode page.
    include_isbn_barcode : bool
        Whether to add a barcode page at the end.

    Returns
    -------
    tuple[bytes, int]
        The PDF content as bytes and the total page count.
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is not installed. Cannot generate PDF. " "Install it with: pip install reportlab")

    page_width = trim_size[0] * inch
    page_height = trim_size[1] * inch
    pagesize = (page_width, page_height)

    margin_top = max(style.margin_top_in, 0.75) * inch
    margin_bottom = max(style.margin_bottom_in, 0.75) * inch
    margin_inner = max(style.margin_inner_in, 0.75) * inch
    margin_outer = max(style.margin_outer_in, 0.75) * inch

    base_font = _get_font_name(style.font_family)
    _get_bold_font_name(base_font)
    italic_font = _get_italic_font_name(base_font)
    heading_font = _get_font_name(style.chapter_heading_font)
    heading_bold = _get_bold_font_name(heading_font)

    # Resolve footer/header templates once (page numbers added per-page)
    header_template = style.header_text
    footer_template = style.footer_text
    show_page_numbers = style.page_numbers

    buffer = io.BytesIO()

    # We track the page count using a list (mutable in closure)
    page_counter = [0]

    def on_page(canvas, doc):
        """Draw header, footer, and page numbers on each page."""
        page_counter[0] += 1
        page_num = page_counter[0]
        canvas.saveState()

        # Footer with page number
        if show_page_numbers:
            footer_y = margin_bottom - 0.4 * inch
            if footer_y < 0.3 * inch:
                footer_y = 0.3 * inch
            canvas.setFont(base_font, 9)
            canvas.setFillColor(gray)

            # Resolve footer template
            footer_text_resolved = _resolve_template(footer_template, title, authors, page_num)
            display_footer = f"{footer_text_resolved} | Page {page_num}" if footer_text_resolved else f"Page {page_num}"

            canvas.drawCentredString(page_width / 2, footer_y, display_footer)

        elif footer_template:
            footer_y = margin_bottom - 0.4 * inch
            if footer_y < 0.3 * inch:
                footer_y = 0.3 * inch
            canvas.setFont(base_font, 9)
            canvas.setFillColor(gray)
            footer_text_resolved = _resolve_template(footer_template, title, authors, page_num)
            if footer_text_resolved:
                canvas.drawCentredString(page_width / 2, footer_y, footer_text_resolved)

        # Header
        if header_template:
            header_y = page_height - margin_top + 0.25 * inch
            canvas.setFont(italic_font, 8)
            canvas.setFillColor(gray)
            header_text_resolved = _resolve_template(header_template, title, authors, page_num)
            if header_text_resolved:
                canvas.drawCentredString(page_width / 2, header_y, header_text_resolved)

        canvas.restoreState()

    def on_title_page(canvas, doc):
        """Title page has no header/footer/page number."""
        page_counter[0] += 1

    # Build the document template with two page templates:
    # one for the title page (no headers/footers) and one for body pages
    frame_body = Frame(
        margin_inner,
        margin_bottom,
        page_width - margin_inner - margin_outer,
        page_height - margin_top - margin_bottom,
        id="body_frame",
    )
    frame_title = Frame(
        margin_outer,
        margin_bottom,
        page_width - 2 * margin_outer,
        page_height - margin_top - margin_bottom,
        id="title_frame",
    )

    title_template = PageTemplate(
        id="title_page",
        frames=[frame_title],
        onPage=on_title_page,
    )
    body_template = PageTemplate(
        id="body_page",
        frames=[frame_body],
        onPage=on_page,
    )

    doc = BaseDocTemplate(
        buffer,
        pagesize=pagesize,
        topMargin=margin_top,
        bottomMargin=margin_bottom,
        leftMargin=margin_inner,
        rightMargin=margin_outer,
        title=title,
        author=", ".join(authors),
    )
    doc.addPageTemplates([title_template, body_template])

    # ---------- Build styles ----------
    body_style = ParagraphStyle(
        "BookBody",
        fontName=base_font,
        fontSize=style.font_size_pt,
        leading=style.font_size_pt * style.line_height,
        alignment=TA_JUSTIFY,
        firstLineIndent=style.paragraph_indent_em * style.font_size_pt,
        spaceBefore=style.paragraph_spacing_pt,
        spaceAfter=style.paragraph_spacing_pt,
    )
    body_first_style = ParagraphStyle(
        "BookBodyFirst",
        parent=body_style,
        firstLineIndent=0,
    )
    chapter_heading_style = ParagraphStyle(
        "ChapterHeading",
        fontName=heading_bold,
        fontSize=style.chapter_heading_size_pt,
        leading=style.chapter_heading_size_pt * 1.3,
        alignment=TA_CENTER,
        spaceBefore=36,
        spaceAfter=24,
        textColor=black,
    )
    title_style = ParagraphStyle(
        "BookTitle",
        fontName=heading_bold,
        fontSize=28,
        leading=34,
        alignment=TA_CENTER,
        spaceBefore=0,
        spaceAfter=12,
    )
    ParagraphStyle(
        "BookSubtitle",
        fontName=italic_font,
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        spaceBefore=6,
        spaceAfter=12,
        textColor=HexColor("#444444"),
    )
    author_style = ParagraphStyle(
        "BookAuthor",
        fontName=base_font,
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        spaceBefore=12,
        spaceAfter=6,
    )
    toc_title_style = ParagraphStyle(
        "TOCTitle",
        fontName=heading_bold,
        fontSize=20,
        leading=26,
        alignment=TA_CENTER,
        spaceBefore=24,
        spaceAfter=24,
    )
    toc_entry_style = ParagraphStyle(
        "TOCEntry",
        fontName=base_font,
        fontSize=style.font_size_pt,
        leading=style.font_size_pt * 1.8,
        alignment=TA_LEFT,
        leftIndent=20,
    )

    # ---------- Build flowables ----------
    story = []

    # -- Title page --
    story.append(NextPageTemplate("title_page"))
    story.append(Spacer(1, page_height * 0.25))
    story.append(Paragraph(title, title_style))

    # Add subtitle if available (we check for a subtitle in the title string
    # separated by a colon, or callers can embed it)
    story.append(Spacer(1, 12))
    story.append(
        HRFlowable(
            width="40%",
            thickness=1,
            color=HexColor("#999999"),
            spaceAfter=18,
            spaceBefore=6,
        )
    )

    if authors:
        author_text = " &amp; ".join(authors) if len(authors) > 1 else authors[0]
        story.append(Paragraph(author_text, author_style))

    story.append(PageBreak())

    # -- Table of Contents --
    story.append(NextPageTemplate("body_page"))
    story.append(Paragraph("Table of Contents", toc_title_style))
    story.append(Spacer(1, 12))

    for idx, ch in enumerate(chapters, start=1):
        toc_text = f"{idx}. &nbsp;&nbsp;{ch.title}"
        story.append(Paragraph(toc_text, toc_entry_style))

    story.append(Spacer(1, 24))
    story.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=HexColor("#cccccc"),
            spaceAfter=12,
        )
    )
    story.append(PageBreak())

    # -- Chapter pages --
    for ch_idx, ch in enumerate(chapters):
        # Chapter heading
        story.append(Spacer(1, 48))
        story.append(Paragraph(ch.title, chapter_heading_style))
        story.append(Spacer(1, 18))
        story.append(
            HRFlowable(
                width="30%",
                thickness=0.5,
                color=HexColor("#999999"),
                spaceAfter=24,
                spaceBefore=6,
            )
        )

        # Chapter body: split on double newlines for paragraphs
        paragraphs = ch.content.strip().split("\n\n")
        for p_idx, para_text in enumerate(paragraphs):
            para_text = para_text.strip()
            if not para_text:
                continue

            # Handle lines within a paragraph (single newlines become spaces)
            para_text = para_text.replace("\n", " ")

            # Escape XML-sensitive characters for ReportLab Paragraph
            para_text = para_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

            # First paragraph of chapter: no indent
            if p_idx == 0:
                story.append(Paragraph(para_text, body_first_style))
            else:
                story.append(Paragraph(para_text, body_style))

        # Page break after each chapter (except the last if barcode follows or it's the end)
        if ch_idx < len(chapters) - 1 or (include_isbn_barcode and isbn):
            story.append(PageBreak())

    # -- ISBN barcode page --
    if include_isbn_barcode and isbn:
        barcode_flowables = _build_isbn_barcode_flowable(isbn, page_width)
        story.extend(barcode_flowables)

    # ---------- Build the PDF ----------
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    total_pages = page_counter[0]

    return pdf_bytes, total_pages


def generate_pdf(
    request: ExportRequest,
    title: str = "Untitled",
    authors: list[str] | None = None,
    style_settings: TemplateStyleSettings | None = None,
) -> PDFDocument:
    """Generate a print-ready PDF document.

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
        A document object containing rendered PDF binary content
        accessible via ``to_bytes()``.
    """
    style = style_settings or TemplateStyleSettings()
    trim = TRIM_DIMENSIONS.get(request.trim_size, TRIM_DIMENSIONS[TrimSize.SIZE_6x9])
    chapters = sorted(request.chapters, key=lambda c: c.order)
    authors = authors or []

    pdf_bytes, total_pages = _render_pdf(
        title=title,
        authors=authors,
        chapters=chapters,
        trim_size=trim,
        style=style,
        isbn=request.isbn,
        include_isbn_barcode=request.include_isbn_barcode,
    )

    # Build a page list for metadata / backward compatibility.
    # The actual PDF content is in _pdf_bytes; the pages list provides
    # a structural summary with chapter HTML for inspection.
    pages: list[PDFPage] = []
    page_number = 1

    header_template = style.header_text
    footer_template = style.footer_text

    def _resolve_tpl(template: str | None, page_num: int) -> str | None:
        if template is None:
            return None
        return (
            template.replace("{title}", title).replace("{author}", ", ".join(authors)).replace("{page}", str(page_num))
        )

    for ch in chapters:
        chapter_html = _build_chapter_html(ch.title, ch.content, style)
        estimated = _estimate_pages_for_chapter(ch.content)

        for p in range(estimated):
            header = _resolve_tpl(header_template, page_number)
            footer = _resolve_tpl(footer_template, page_number)
            if style.page_numbers:
                footer = f"{footer or ''} | Page {page_number}".strip(" |")

            pages.append(
                PDFPage(
                    page_number=page_number,
                    content_html=chapter_html if p == 0 else "<p>(continued)</p>",
                    is_chapter_start=(p == 0),
                    header=header,
                    footer=footer,
                )
            )
            page_number += 1

    if request.include_isbn_barcode and request.isbn:
        pages.append(
            PDFPage(
                page_number=page_number,
                content_html=f'<div class="isbn-barcode"><p>ISBN: {request.isbn}</p></div>',
                is_chapter_start=False,
                header=None,
                footer=f"Page {page_number}" if style.page_numbers else None,
            )
        )
        page_number += 1

    return PDFDocument(
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
        pages=pages,
        isbn=request.isbn,
        include_isbn_barcode=request.include_isbn_barcode,
        generated_at=datetime.now(UTC).isoformat(),
        total_pages=total_pages,
        _pdf_bytes=pdf_bytes,
    )


def generate_pdf_bytes(
    request: ExportRequest,
    title: str = "Untitled",
    authors: list[str] | None = None,
    style_settings: TemplateStyleSettings | None = None,
) -> bytes:
    """Convenience wrapper that returns raw PDF bytes."""
    doc = generate_pdf(request, title, authors, style_settings)
    return doc.to_bytes()
