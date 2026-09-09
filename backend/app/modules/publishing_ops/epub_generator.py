"""EPUB generator for the Publishing Operations Center.

Builds valid EPUB 3.0 files from a list of chapters with:
- Table of Contents (NCX + Navigation Document)
- Metadata injection (DC terms)
- Cover image embedding
- Style application from formatting templates
"""

from __future__ import annotations

import io
import uuid
import zipfile
from datetime import UTC, datetime
from xml.sax.saxutils import escape as xml_escape

from app.modules.publishing_ops.schemas import (
    ChapterInput,
    ExportRequest,
    TemplateStyleSettings,
)


def _default_style(settings: TemplateStyleSettings | None = None) -> str:
    """Generate CSS from template style settings."""
    s = settings or TemplateStyleSettings()
    css = f"""
body {{
    font-family: "{s.font_family}", serif;
    font-size: {s.font_size_pt}pt;
    line-height: {s.line_height};
    margin: {s.margin_top_in}in {s.margin_outer_in}in {s.margin_bottom_in}in {s.margin_inner_in}in;
}}
h1, h2 {{
    font-family: "{s.chapter_heading_font}", sans-serif;
    font-size: {s.chapter_heading_size_pt}pt;
    margin-top: 2em;
    margin-bottom: 1em;
    page-break-before: always;
}}
p {{
    text-indent: {s.paragraph_indent_em}em;
    margin-top: {s.paragraph_spacing_pt}pt;
    margin-bottom: {s.paragraph_spacing_pt}pt;
}}
"""
    if s.drop_cap:
        css += """
p:first-of-type::first-letter {
    font-size: 3em;
    float: left;
    line-height: 1;
    margin-right: 0.1em;
}
"""
    return css.strip()


def _build_container_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
        "  <rootfiles>\n"
        '    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>\n'
        "  </rootfiles>\n"
        "</container>"
    )


def _build_chapter_xhtml(title: str, body_html: str, css_path: str = "../style.css") -> str:
    safe_title = xml_escape(title)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<!DOCTYPE html>\n"
        '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">\n'
        "<head>\n"
        f"  <title>{safe_title}</title>\n"
        f'  <link rel="stylesheet" type="text/css" href="{css_path}"/>\n'
        "</head>\n"
        "<body>\n"
        f"  <h1>{safe_title}</h1>\n"
        f"  {body_html}\n"
        "</body>\n"
        "</html>"
    )


def _wrap_paragraphs(content: str) -> str:
    """Wrap plain-text content into <p> tags (one per paragraph)."""
    lines = content.strip().split("\n\n")
    parts: list[str] = []
    for line in lines:
        line = line.strip()
        if line:
            # If already has HTML tags, use as-is
            if line.startswith("<"):
                parts.append(line)
            else:
                parts.append(f"<p>{xml_escape(line)}</p>")
    return "\n  ".join(parts)


def _build_content_opf(
    book_id: uuid.UUID,
    title: str,
    authors: list[str],
    language: str,
    chapters: list[ChapterInput],
    has_cover: bool,
) -> str:
    uid = str(book_id)
    safe_title = xml_escape(title)
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    author_elements = "\n    ".join(f"<dc:creator>{xml_escape(a)}</dc:creator>" for a in (authors or ["Unknown"]))

    manifest_items = [
        '<item id="style" href="style.css" media-type="text/css"/>',
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
    ]
    spine_refs = []

    if has_cover:
        manifest_items.append(
            '<item id="cover-image" href="images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>'
        )

    for i, ch in enumerate(chapters):
        item_id = f"chapter{i + 1}"
        manifest_items.append(
            f'<item id="{item_id}" href="chapters/{item_id}.xhtml" media-type="application/xhtml+xml"/>'
        )
        spine_refs.append(f'<itemref idref="{item_id}"/>')

    manifest_str = "\n    ".join(manifest_items)
    spine_str = "\n    ".join(spine_refs)

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="3.0">\n'
        '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        f'    <dc:identifier id="BookId">urn:uuid:{uid}</dc:identifier>\n'
        f"    <dc:title>{safe_title}</dc:title>\n"
        f"    {author_elements}\n"
        f"    <dc:language>{language}</dc:language>\n"
        f'    <meta property="dcterms:modified">{now}</meta>\n'
        "  </metadata>\n"
        "  <manifest>\n"
        f"    {manifest_str}\n"
        "  </manifest>\n"
        f'  <spine toc="nav">\n'
        f"    {spine_str}\n"
        "  </spine>\n"
        "</package>"
    )


def _build_nav_xhtml(chapters: list[ChapterInput]) -> str:
    toc_items: list[str] = []
    for i, ch in enumerate(chapters):
        safe = xml_escape(ch.title)
        toc_items.append(f'      <li><a href="chapters/chapter{i + 1}.xhtml">{safe}</a></li>')
    toc_str = "\n".join(toc_items)

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<!DOCTYPE html>\n"
        '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">\n'
        "<head>\n"
        "  <title>Table of Contents</title>\n"
        "</head>\n<body>\n"
        '  <nav epub:type="toc">\n'
        "    <h1>Table of Contents</h1>\n"
        "    <ol>\n"
        f"{toc_str}\n"
        "    </ol>\n"
        "  </nav>\n"
        "</body>\n</html>"
    )


def generate_epub(
    request: ExportRequest,
    title: str = "Untitled",
    authors: list[str] | None = None,
    language: str = "en",
    style_settings: TemplateStyleSettings | None = None,
    cover_image_bytes: bytes | None = None,
) -> bytes:
    """Generate an EPUB 3.0 file and return the raw bytes.

    Parameters
    ----------
    request:
        The export request containing chapters, book_id, and options.
    title:
        Book title for metadata.
    authors:
        List of author names.
    language:
        BCP-47 language code.
    style_settings:
        Typography / layout settings from a formatting template.
    cover_image_bytes:
        Raw JPEG/PNG bytes for the cover image (optional).
    """
    chapters = sorted(request.chapters, key=lambda c: c.order)
    has_cover = cover_image_bytes is not None and request.include_cover

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. mimetype (must be first, stored uncompressed per EPUB spec)
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)

        # 2. META-INF/container.xml
        zf.writestr("META-INF/container.xml", _build_container_xml())

        # 3. Stylesheet
        zf.writestr("OEBPS/style.css", _default_style(style_settings))

        # 4. Cover image
        if has_cover and cover_image_bytes:
            zf.writestr("OEBPS/images/cover.jpg", cover_image_bytes)

        # 5. Chapter XHTML files
        for i, ch in enumerate(chapters):
            body = _wrap_paragraphs(ch.content)
            xhtml = _build_chapter_xhtml(ch.title, body, css_path="../style.css")
            zf.writestr(f"OEBPS/chapters/chapter{i + 1}.xhtml", xhtml)

        # 6. Navigation document
        if request.include_toc:
            zf.writestr("OEBPS/nav.xhtml", _build_nav_xhtml(chapters))
        else:
            # Minimal nav required by EPUB 3
            zf.writestr("OEBPS/nav.xhtml", _build_nav_xhtml([]))

        # 7. OPF package document
        opf = _build_content_opf(
            book_id=request.book_id,
            title=title,
            authors=authors or [],
            language=language,
            chapters=chapters,
            has_cover=has_cover,
        )
        zf.writestr("OEBPS/content.opf", opf)

    return buf.getvalue()
