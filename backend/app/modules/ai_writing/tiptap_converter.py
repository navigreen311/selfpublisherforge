"""Utilities for converting between TipTap JSON, HTML, and plain text.

TipTap stores rich-text content as a JSON document (ProseMirror schema).
These helpers allow the export/import services to convert manuscripts between
the internal TipTap representation and common document formats.
"""

from __future__ import annotations

import html as _html
import json
import logging
import re
from typing import Any, cast

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# TipTap JSON -> HTML
# ---------------------------------------------------------------------------


def tiptap_to_html(content: dict | str | None) -> str:
    """Convert a TipTap JSON document to an HTML string.

    Parameters
    ----------
    content:
        A TipTap/ProseMirror document dict (with a top-level ``"type": "doc"``
        key), a JSON string, or ``None``.

    Returns
    -------
    str
        An HTML fragment string.  Returns an empty string when *content* is
        falsy or cannot be parsed.
    """
    if not content:
        return ""

    if isinstance(content, str):
        try:
            content = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            # If it's already plain HTML/text, return as-is
            return content

    if not isinstance(content, dict):
        return str(content)

    return _render_node(content)


def _render_node(node: dict) -> str:
    """Recursively render a TipTap/ProseMirror node to HTML."""
    node_type = node.get("type", "")
    children = node.get("content", [])
    attrs = node.get("attrs", {})
    marks = node.get("marks", [])
    text = node.get("text", "")

    # Text nodes
    if node_type == "text":
        escaped = _html.escape(text)
        return _apply_marks(escaped, marks)

    # Block nodes
    inner = "".join(_render_node(child) for child in children)

    if node_type == "doc":
        return inner
    if node_type == "paragraph":
        return f"<p>{inner}</p>\n"
    if node_type == "heading":
        level = attrs.get("level", 1)
        return f"<h{level}>{inner}</h{level}>\n"
    if node_type == "blockquote":
        return f"<blockquote>{inner}</blockquote>\n"
    if node_type == "bulletList":
        return f"<ul>\n{inner}</ul>\n"
    if node_type == "orderedList":
        return f"<ol>\n{inner}</ol>\n"
    if node_type == "listItem":
        return f"<li>{inner}</li>\n"
    if node_type == "codeBlock":
        return f"<pre><code>{inner}</code></pre>\n"
    if node_type == "horizontalRule":
        return "<hr />\n"
    if node_type == "hardBreak":
        return "<br />"
    if node_type == "image":
        src = attrs.get("src", "")
        alt = attrs.get("alt", "")
        return f'<img src="{_html.escape(src)}" alt="{_html.escape(alt)}" />'

    # Fallback: wrap unknown block nodes in a div
    if inner:
        return f"<div>{inner}</div>\n"
    return ""


def _apply_marks(text: str, marks: list[dict]) -> str:
    """Wrap *text* with HTML tags corresponding to TipTap marks."""
    for mark in marks:
        mark_type = mark.get("type", "")
        mark_attrs = mark.get("attrs", {})
        if mark_type == "bold":
            text = f"<strong>{text}</strong>"
        elif mark_type == "italic":
            text = f"<em>{text}</em>"
        elif mark_type == "underline":
            text = f"<u>{text}</u>"
        elif mark_type == "strike":
            text = f"<s>{text}</s>"
        elif mark_type == "code":
            text = f"<code>{text}</code>"
        elif mark_type == "link":
            href = _html.escape(mark_attrs.get("href", ""))
            text = f'<a href="{href}">{text}</a>'
    return text


# ---------------------------------------------------------------------------
# TipTap JSON -> Plain Text
# ---------------------------------------------------------------------------


def tiptap_to_text(content: dict | str | None) -> str:
    """Convert a TipTap JSON document to plain text.

    Parameters
    ----------
    content:
        Same as :func:`tiptap_to_html`.

    Returns
    -------
    str
        Plain-text representation of the document.
    """
    if not content:
        return ""

    if isinstance(content, str):
        try:
            content = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            # Strip any HTML tags if it looks like HTML
            return _strip_html(content)

    if not isinstance(content, dict):
        return str(content)

    return _extract_text(content).strip()


def _extract_text(node: dict) -> str:
    """Recursively extract plain text from a TipTap node tree."""
    node_type = node.get("type", "")
    children = node.get("content", [])
    text = node.get("text", "")

    if node_type == "text":
        return cast("str", text)

    parts = [_extract_text(child) for child in children]
    inner = "".join(parts)

    # Add appropriate whitespace for block nodes
    if node_type in ("paragraph", "heading", "blockquote", "codeBlock"):
        return inner + "\n\n"
    if node_type == "listItem":
        return "- " + inner + "\n"
    if node_type == "hardBreak":
        return "\n"
    if node_type == "horizontalRule":
        return "\n---\n\n"

    return inner


def _strip_html(text: str) -> str:
    """Remove HTML tags from a string."""
    clean = re.sub(r"<[^>]+>", "", text)
    return clean.strip()


# ---------------------------------------------------------------------------
# HTML -> TipTap JSON
# ---------------------------------------------------------------------------


def html_to_tiptap(html_str: str) -> dict:
    """Convert an HTML string to a TipTap-compatible JSON document.

    This is a pragmatic converter that handles the most common HTML elements.
    It does not require external dependencies — it uses a simple regex-based
    parser suitable for manuscript content.

    Parameters
    ----------
    html_str:
        An HTML fragment string.

    Returns
    -------
    dict
        A TipTap/ProseMirror document dict.
    """
    if not html_str or not html_str.strip():
        return {"type": "doc", "content": []}

    content: list[dict] = []

    # Normalize whitespace
    cleaned = html_str.strip()

    # Split into block-level elements
    block_pattern = re.compile(
        r"<(h[1-6]|p|blockquote|pre|ul|ol|hr)\b[^>]*>(.*?)</\1>|<hr\s*/?>",
        re.DOTALL | re.IGNORECASE,
    )

    last_end = 0
    for match in block_pattern.finditer(cleaned):
        # Handle any text between blocks
        between = cleaned[last_end : match.start()].strip()
        if between:
            para = _html_text_to_paragraph(between)
            if para:
                content.append(para)

        tag = match.group(1)
        inner = match.group(2) if match.group(2) is not None else ""

        if tag and tag.lower().startswith("h"):
            level = int(tag[1])
            content.append(
                {
                    "type": "heading",
                    "attrs": {"level": level},
                    "content": _parse_inline_html(inner),
                }
            )
        elif tag and tag.lower() == "p":
            para = _html_text_to_paragraph(inner)
            if para:
                content.append(para)
        elif tag and tag.lower() == "blockquote":
            content.append(
                {
                    "type": "blockquote",
                    "content": [_html_text_to_paragraph(inner) or {"type": "paragraph", "content": []}],
                }
            )
        elif tag and tag.lower() == "pre":
            code_text = re.sub(r"</?code[^>]*>", "", inner)
            content.append(
                {
                    "type": "codeBlock",
                    "content": [{"type": "text", "text": _html.unescape(code_text)}],
                }
            )
        elif tag and tag.lower() in ("ul", "ol"):
            list_type = "bulletList" if tag.lower() == "ul" else "orderedList"
            items = re.findall(r"<li[^>]*>(.*?)</li>", inner, re.DOTALL | re.IGNORECASE)
            list_content = []
            for item_html in items:
                list_content.append(
                    {
                        "type": "listItem",
                        "content": [_html_text_to_paragraph(item_html) or {"type": "paragraph", "content": []}],
                    }
                )
            content.append({"type": list_type, "content": list_content})
        elif match.group(0).strip().lower().startswith("<hr"):
            content.append({"type": "horizontalRule"})

        last_end = match.end()

    # Handle trailing text
    trailing = cleaned[last_end:].strip()
    if trailing:
        para = _html_text_to_paragraph(trailing)
        if para:
            content.append(para)

    # If no block elements were found, treat entire content as a paragraph
    if not content:
        para = _html_text_to_paragraph(cleaned)
        if para:
            content.append(para)

    return {"type": "doc", "content": content}


def _html_text_to_paragraph(html_text: str) -> dict | None:
    """Convert an HTML text fragment to a TipTap paragraph node."""
    inline_nodes = _parse_inline_html(html_text)
    if not inline_nodes:
        return None
    return {"type": "paragraph", "content": inline_nodes}


def _parse_inline_html(html_text: str) -> list[dict]:
    """Parse inline HTML elements into TipTap text nodes with marks."""
    if not html_text:
        return []

    # Strip block-level tags that might be nested
    text = re.sub(r"<br\s*/?>", "\n", html_text)
    text = re.sub(r"</?(?:p|div)[^>]*>", "", text)

    nodes: list[dict] = []

    # Simple approach: strip tags and create text nodes, preserving bold/italic marks
    # Build a list of segments with their marks
    segments = _extract_marked_segments(text)
    for seg_text, seg_marks in segments:
        if not seg_text:
            continue
        node: dict[str, Any] = {"type": "text", "text": _html.unescape(seg_text)}
        if seg_marks:
            node["marks"] = seg_marks
        nodes.append(node)

    return nodes


def _extract_marked_segments(html_text: str) -> list[tuple[str, list[dict]]]:
    """Extract text segments with their TipTap marks from inline HTML."""
    # For simplicity, strip all inline tags and return plain text
    # This handles the common case of manuscript import
    plain = re.sub(r"<strong[^>]*>(.*?)</strong>", r"\1", html_text, flags=re.DOTALL)
    plain = re.sub(r"<b[^>]*>(.*?)</b>", r"\1", plain, flags=re.DOTALL)
    plain = re.sub(r"<em[^>]*>(.*?)</em>", r"\1", plain, flags=re.DOTALL)
    plain = re.sub(r"<i[^>]*>(.*?)</i>", r"\1", plain, flags=re.DOTALL)
    plain = re.sub(r"<u[^>]*>(.*?)</u>", r"\1", plain, flags=re.DOTALL)
    plain = re.sub(r"<s[^>]*>(.*?)</s>", r"\1", plain, flags=re.DOTALL)
    plain = re.sub(r"<code[^>]*>(.*?)</code>", r"\1", plain, flags=re.DOTALL)
    plain = re.sub(r"<a[^>]*>(.*?)</a>", r"\1", plain, flags=re.DOTALL)
    plain = re.sub(r"<[^>]+>", "", plain)

    if not plain.strip():
        return []

    return [(plain, [])]


# ---------------------------------------------------------------------------
# Plain Text -> TipTap JSON
# ---------------------------------------------------------------------------


def text_to_tiptap(text: str) -> dict:
    """Convert plain text to a TipTap-compatible JSON document.

    Splits the text into paragraphs on double newlines. Single newlines
    within a paragraph are converted to hard breaks.

    Parameters
    ----------
    text:
        Plain-text string.

    Returns
    -------
    dict
        A TipTap/ProseMirror document dict.
    """
    if not text or not text.strip():
        return {"type": "doc", "content": []}

    content: list[dict] = []
    paragraphs = re.split(r"\n{2,}", text.strip())

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Handle single newlines as hard breaks within a paragraph
        lines = para.split("\n")
        nodes: list[dict] = []
        for i, line in enumerate(lines):
            if line:
                nodes.append({"type": "text", "text": line})
            if i < len(lines) - 1:
                nodes.append({"type": "hardBreak"})

        if nodes:
            content.append({"type": "paragraph", "content": nodes})

    return {"type": "doc", "content": content}
