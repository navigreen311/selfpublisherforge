"""
Fixed-Layout Kindle Pipeline

Generates KPF and EPUB 3 fixed-layout exports for specialty books,
with read-order mapping, text pop-up overlays, and read-aloud sync.
"""

import io
import json
import uuid
import zipfile
from datetime import datetime

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_BOOK_TYPE_META = {
    "childrens": {"viewport_w": 1024, "viewport_h": 1366, "rendition_spread": "landscape"},
    "coloring": {"viewport_w": 1024, "viewport_h": 1366, "rendition_spread": "none"},
    "puzzle": {"viewport_w": 1024, "viewport_h": 1366, "rendition_spread": "none"},
}


def _default_viewport(book_type: str) -> dict:
    return _BOOK_TYPE_META.get(book_type, _BOOK_TYPE_META["childrens"])


def _generate_opf(book_type: str, book_data: dict, pages: list) -> str:
    """Build the OPF package document for fixed-layout EPUB 3."""
    meta = _default_viewport(book_type)
    uid = book_data.get("id", str(uuid.uuid4()))
    title = book_data.get("title", "Untitled")
    author = book_data.get("author", "Unknown")
    lang = book_data.get("language", "en")

    manifest_items: list[str] = []
    spine_items: list[str] = []
    for idx, page in enumerate(pages):
        page_id = f"page{idx:04d}"
        manifest_items.append(
            f'    <item id="{page_id}" href="pages/{page_id}.xhtml" '
            f'media-type="application/xhtml+xml" />'
        )
        spine_items.append(f'    <itemref idref="{page_id}" />')
        if page.get("image_url"):
            img_id = f"img{idx:04d}"
            ext = page["image_url"].rsplit(".", 1)[-1] if "." in page["image_url"] else "png"
            media = f"image/{'jpeg' if ext in ('jpg', 'jpeg') else ext}"
            manifest_items.append(
                f'    <item id="{img_id}" href="images/{img_id}.{ext}" '
                f'media-type="{media}" />'
            )

    manifest_block = "\n".join(manifest_items)
    spine_block = "\n".join(spine_items)

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="uid">urn:uuid:{uid}</dc:identifier>
    <dc:title>{title}</dc:title>
    <dc:creator>{author}</dc:creator>
    <dc:language>{lang}</dc:language>
    <meta property="dcterms:modified">{datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}</meta>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:orientation">auto</meta>
    <meta property="rendition:spread">{meta["rendition_spread"]}</meta>
  </metadata>
  <manifest>
{manifest_block}
  </manifest>
  <spine>
{spine_block}
  </spine>
</package>"""


def _build_page_xhtml(
    page: dict, idx: int, viewport_w: int, viewport_h: int
) -> str:
    """Build a single fixed-layout XHTML page."""
    text = page.get("text_content", "")
    img_tag = ""
    if page.get("image_url"):
        ext = page["image_url"].rsplit(".", 1)[-1] if "." in page["image_url"] else "png"
        img_tag = (
            f'<img src="../images/img{idx:04d}.{ext}" '
            f'style="width:100%;height:100%;position:absolute;top:0;left:0;" '
            f'alt="Page {idx + 1} illustration" />'
        )

    text_block = ""
    if text:
        font_size = page.get("text_font_size", 18)
        text_color = page.get("text_color", "#000000")
        position = page.get("text_position", "bottom")
        top_pct = {"top": "5%", "middle": "40%", "bottom": "70%"}.get(position, "70%")
        text_block = (
            f'<div class="text-overlay" style="position:absolute;top:{top_pct};'
            f"left:5%;right:5%;font-size:{font_size}px;color:{text_color};"
            f'text-align:center;z-index:10;">'
            f"<p>{text}</p></div>"
        )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width={viewport_w}, height={viewport_h}"/>
  <title>Page {idx + 1}</title>
  <style>
    body {{ margin:0; padding:0; width:{viewport_w}px; height:{viewport_h}px; overflow:hidden; }}
  </style>
</head>
<body>
  {img_tag}
  {text_block}
</body>
</html>"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_kpf(book_type: str, book_data: dict) -> bytes:
    """
    Build a Kindle Package Format (KPF) structure.

    KPF is essentially a ZIP containing the fixed-layout EPUB content plus
    Kindle-specific metadata (reading order, text pop-ups, read-aloud data).

    Parameters
    ----------
    book_type : str
        One of "childrens", "coloring", "puzzle".
    book_data : dict
        Must contain at minimum ``pages`` (list[dict]), ``title``, ``author``.

    Returns
    -------
    bytes
        The KPF file content as raw bytes.
    """
    pages = book_data.get("pages", [])
    meta = _default_viewport(book_type)
    vw, vh = meta["viewport_w"], meta["viewport_h"]

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # mimetype (must be first, stored uncompressed per EPUB convention)
        zf.writestr("mimetype", "application/x-kpf+zip", compress_type=zipfile.ZIP_STORED)

        # META-INF/container.xml
        zf.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0"?>\n'
            '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">\n'
            "  <rootfiles>\n"
            '    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>\n'
            "  </rootfiles>\n"
            "</container>",
        )

        # OPF
        zf.writestr("OEBPS/content.opf", _generate_opf(book_type, book_data, pages))

        # Pages
        for idx, page in enumerate(pages):
            xhtml = _build_page_xhtml(page, idx, vw, vh)
            zf.writestr(f"OEBPS/pages/page{idx:04d}.xhtml", xhtml)

        # Reading order metadata (Kindle-specific)
        read_order = create_read_order(pages)
        zf.writestr("OEBPS/reading-order.json", json.dumps(read_order, indent=2))

        # Text pop-up data
        popups: list[dict] = []
        for page in pages:
            popup = generate_text_popup(page)
            if popup.get("has_popup"):
                popups.append(popup)
        zf.writestr("OEBPS/text-popups.json", json.dumps(popups, indent=2))

        # Read-aloud sync
        sync = generate_read_aloud_sync(pages)
        zf.writestr("OEBPS/read-aloud.json", json.dumps(sync, indent=2))

    return buf.getvalue()


def generate_fixed_epub(book_type: str, book_data: dict) -> bytes:
    """
    Build an EPUB 3 fixed-layout ebook.

    Parameters
    ----------
    book_type : str
        One of "childrens", "coloring", "puzzle".
    book_data : dict
        Must contain ``pages`` (list[dict]), ``title``, ``author``.

    Returns
    -------
    bytes
        EPUB file content as raw bytes.
    """
    pages = book_data.get("pages", [])
    meta = _default_viewport(book_type)
    vw, vh = meta["viewport_w"], meta["viewport_h"]

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # mimetype (uncompressed, first entry)
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)

        # META-INF/container.xml
        zf.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0"?>\n'
            '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">\n'
            "  <rootfiles>\n"
            '    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>\n'
            "  </rootfiles>\n"
            "</container>",
        )

        # OPF
        zf.writestr("OEBPS/content.opf", _generate_opf(book_type, book_data, pages))

        # XHTML pages
        for idx, page in enumerate(pages):
            xhtml = _build_page_xhtml(page, idx, vw, vh)
            zf.writestr(f"OEBPS/pages/page{idx:04d}.xhtml", xhtml)

        # Navigation document (EPUB 3 requirement)
        nav_items = "\n".join(
            f'      <li><a href="pages/page{i:04d}.xhtml">Page {i + 1}</a></li>'
            for i in range(len(pages))
        )
        nav_doc = f"""<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Navigation</title></head>
<body>
  <nav epub:type="toc">
    <ol>
{nav_items}
    </ol>
  </nav>
</body>
</html>"""
        zf.writestr("OEBPS/nav.xhtml", nav_doc)

    return buf.getvalue()


def create_read_order(pages: list[dict]) -> list[dict]:
    """
    Map visual page layout to a logical reading order for accessibility.

    Each entry in the returned list contains the page index, reading-order
    position, text regions sorted top-to-bottom / left-to-right, and
    whether the page is a spread.

    Parameters
    ----------
    pages : list[dict]
        Page data dicts.  Recognised keys: ``page_number``, ``layout``,
        ``text_content``, ``text_position``.

    Returns
    -------
    list[dict]
        Ordered list of ``{"page_index", "read_position", "layout",
        "text_regions", "is_spread"}`` dicts.
    """
    read_order: list[dict] = []

    for idx, page in enumerate(pages):
        layout = page.get("layout", "full_bleed")
        text = page.get("text_content", "")
        position = page.get("text_position", "bottom")

        # Determine text region ordering based on layout
        text_regions: list[dict] = []
        if text:
            text_regions.append(
                {
                    "type": "text",
                    "content": text,
                    "position": position,
                    "sort_key": {"top": 0, "middle": 1, "bottom": 2}.get(position, 2),
                }
            )

        # Image alt-text region
        if page.get("image_url") or layout not in ("text_only",):
            alt = page.get("image_alt", f"Illustration for page {idx + 1}")
            img_sort = 1 if position == "top" else 0
            text_regions.append(
                {"type": "image_alt", "content": alt, "sort_key": img_sort}
            )

        # Sort regions for logical reading order (top-to-bottom)
        text_regions.sort(key=lambda r: r["sort_key"])

        is_spread = layout in ("left_image_right_text", "right_image_left_text")

        read_order.append(
            {
                "page_index": idx,
                "read_position": idx,
                "layout": layout,
                "text_regions": text_regions,
                "is_spread": is_spread,
            }
        )

    return read_order


def generate_text_popup(page: dict) -> dict:
    """
    Generate text pop-up overlay data for a single page.

    Text pop-ups allow readers to tap on small text to see an enlarged
    readable version -- critical for fixed-layout books on small screens.

    Parameters
    ----------
    page : dict
        Page data with ``text_content``, ``text_font_size``, ``text_position``.

    Returns
    -------
    dict
        ``{"has_popup", "page_number", "popup_text", "popup_region",
        "font_size_original", "font_size_popup", "background"}``.
    """
    text = page.get("text_content", "")
    font_size = page.get("text_font_size", 18)
    page_num = page.get("page_number", 0)
    position = page.get("text_position", "bottom")

    if not text or font_size >= 16:
        return {
            "has_popup": False,
            "page_number": page_num,
            "popup_text": None,
            "popup_region": None,
            "font_size_original": font_size,
            "font_size_popup": None,
            "background": None,
        }

    # Calculate popup region based on text position
    region_map = {
        "top": {"x": 5, "y": 5, "width": 90, "height": 30},
        "middle": {"x": 5, "y": 35, "width": 90, "height": 30},
        "bottom": {"x": 5, "y": 65, "width": 90, "height": 30},
    }
    region = region_map.get(position, region_map["bottom"])

    # Pop-up font size: scale up to at least 24px for readability
    popup_font = max(24, int(font_size * 1.8))

    return {
        "has_popup": True,
        "page_number": page_num,
        "popup_text": text,
        "popup_region": region,
        "font_size_original": font_size,
        "font_size_popup": popup_font,
        "background": "rgba(255, 255, 255, 0.95)",
    }


def generate_read_aloud_sync(pages: list[dict]) -> dict:
    """
    Generate word-level timing data for Kindle read-aloud highlighting.

    Produces timing entries that allow the Kindle app to highlight each
    word as it is read by the text-to-speech engine.

    Parameters
    ----------
    pages : list[dict]
        Page data with ``text_content`` and ``page_number``.

    Returns
    -------
    dict
        ``{"version", "total_duration_ms", "pages": [...]}``.
        Each page entry has ``{"page_number", "duration_ms",
        "words": [{"word", "start_ms", "end_ms", "char_offset",
        "char_length"}]}``.
    """
    # Average speaking rate: ~150 words per minute -> ~400ms per word
    WORD_DURATION_MS = 400
    PAUSE_AFTER_SENTENCE_MS = 300
    PAUSE_AFTER_PAGE_MS = 800

    result_pages: list[dict] = []
    global_offset_ms = 0

    for page in pages:
        text = page.get("text_content", "")
        page_num = page.get("page_number", 0)

        if not text:
            result_pages.append(
                {
                    "page_number": page_num,
                    "duration_ms": PAUSE_AFTER_PAGE_MS,
                    "words": [],
                }
            )
            global_offset_ms += PAUSE_AFTER_PAGE_MS
            continue

        words_data: list[dict] = []
        char_offset = 0
        page_start = global_offset_ms

        raw_words = text.split()
        for word in raw_words:
            start = global_offset_ms
            end = start + WORD_DURATION_MS

            words_data.append(
                {
                    "word": word,
                    "start_ms": start,
                    "end_ms": end,
                    "char_offset": char_offset,
                    "char_length": len(word),
                }
            )
            global_offset_ms = end

            # Add sentence-end pause
            if word and word[-1] in ".!?":
                global_offset_ms += PAUSE_AFTER_SENTENCE_MS

            char_offset += len(word) + 1  # +1 for the space

        global_offset_ms += PAUSE_AFTER_PAGE_MS
        page_duration = global_offset_ms - page_start

        result_pages.append(
            {
                "page_number": page_num,
                "duration_ms": page_duration,
                "words": words_data,
            }
        )

    return {
        "version": "1.0",
        "total_duration_ms": global_offset_ms,
        "pages": result_pages,
    }
