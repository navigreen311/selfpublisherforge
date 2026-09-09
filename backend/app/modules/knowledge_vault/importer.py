"""Content importer: URL scraping, file extraction, and AI fact extraction."""

from __future__ import annotations

import base64
import io
import logging
import re
from typing import Any, cast

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


# ── URL content extraction ───────────────────────────────────────


async def extract_from_url(url: str) -> dict[str, Any]:
    """
    Fetch a URL and extract its textual content.
    Returns {"title": str, "content": str, "source_url": str}.
    """
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "SelfPublisherForge/1.0"})
        resp.raise_for_status()
        html = resp.text

    title = _extract_html_title(html)
    text_content = _strip_html_tags(html)
    # Truncate very long pages
    if len(text_content) > 50_000:
        text_content = text_content[:50_000] + "\n...[truncated]"

    return {
        "title": title or url,
        "content": text_content,
        "source_url": url,
        "source_type": "url",
    }


def _extract_html_title(html: str) -> str:
    """Pull the <title> from raw HTML."""
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _strip_html_tags(html: str) -> str:
    """Rough conversion from HTML to plain text."""
    # Remove script / style blocks
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.IGNORECASE | re.DOTALL)
    # Convert <br>, <p>, <div> to newlines
    text = re.sub(r"<(br|/p|/div|/h[1-6])[^>]*>", "\n", text, flags=re.IGNORECASE)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Collapse whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ── File content extraction ──────────────────────────────────────


async def extract_from_file(file_name: str, file_content_base64: str) -> dict[str, Any]:
    """
    Decode a base64-encoded file and extract text.
    Supports .txt, .pdf (via basic extraction), and .docx.
    """
    raw_bytes = base64.b64decode(file_content_base64)
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""

    if ext == "txt":
        content = raw_bytes.decode("utf-8", errors="replace")
    elif ext == "pdf":
        content = _extract_pdf_text(raw_bytes)
    elif ext == "docx":
        content = _extract_docx_text(raw_bytes)
    else:
        content = raw_bytes.decode("utf-8", errors="replace")

    title = file_name.rsplit(".", 1)[0] if "." in file_name else file_name

    return {
        "title": title,
        "content": content,
        "source_type": "file",
    }


def _extract_pdf_text(data: bytes) -> str:
    """Extract text from PDF bytes. Requires PyPDF2 or falls back gracefully."""
    try:
        import PyPDF2

        reader = PyPDF2.PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)
    except ImportError:
        logger.warning("PyPDF2 not installed; falling back to raw decode for PDF")
        return data.decode("utf-8", errors="replace")


def _extract_docx_text(data: bytes) -> str:
    """Extract text from DOCX bytes."""
    try:
        from docx import Document

        doc = Document(io.BytesIO(data))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        logger.warning("python-docx not installed; falling back to raw decode for DOCX")
        return data.decode("utf-8", errors="replace")


# ── AI-powered key fact extraction ───────────────────────────────


async def extract_key_facts(content: str) -> dict[str, Any]:
    """
    Use the configured LLM to pull out key facts, suggested tags,
    and a credibility assessment from raw content.
    Returns {"key_facts": str, "tags": list[str], "credibility_score": float}.
    """
    settings = get_settings()

    prompt = (
        "You are a research assistant. Given the following content, extract:\n"
        "1. Key facts (bullet points)\n"
        "2. 3-7 relevant tags (single words or short phrases)\n"
        "3. A credibility score from 0.0 to 1.0\n\n"
        "Return ONLY valid JSON with keys: key_facts (string), tags (list of strings), "
        "credibility_score (float).\n\n"
        f"Content:\n{content[:8000]}"
    )

    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        message = await client.messages.create(
            model=settings.DEFAULT_LLM_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        content_block = message.content[0]
        raw_text = content_block.text if hasattr(content_block, "text") else str(content_block)  # type: ignore[union-attr]
        return _parse_extraction_response(raw_text)
    except (ConnectionError, anthropic.APIConnectionError, anthropic.APITimeoutError):
        logger.error("AI fact extraction failed due to connection issue", exc_info=True)
        return {
            "key_facts": "",
            "tags": [],
            "credibility_score": None,
        }
    except (anthropic.APIStatusError, anthropic.APIError) as exc:
        logger.error("AI fact extraction failed due to API error: %s", exc, exc_info=True)
        return {
            "key_facts": "",
            "tags": [],
            "credibility_score": None,
        }
    except (ValueError, KeyError, IndexError):
        logger.error("AI fact extraction failed due to response parsing error", exc_info=True)
        return {
            "key_facts": "",
            "tags": [],
            "credibility_score": None,
        }


async def summarize_content(content: str) -> dict[str, Any]:
    """
    Generate an AI summary of a knowledge entry's content.
    Returns {"summary": str, "key_points": list[str], "suggested_tags": list[str]}.
    """
    settings = get_settings()

    prompt = (
        "Summarize the following research content. Provide:\n"
        "1. A concise summary (2-4 sentences)\n"
        "2. Key points as a bullet list\n"
        "3. 3-5 suggested tags\n\n"
        "Return ONLY valid JSON with keys: summary (string), "
        "key_points (list of strings), suggested_tags (list of strings).\n\n"
        f"Content:\n{content[:8000]}"
    )

    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        message = await client.messages.create(
            model=settings.DEFAULT_LLM_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        content_block = message.content[0]
        raw_text = content_block.text if hasattr(content_block, "text") else str(content_block)  # type: ignore[union-attr]
        return _parse_summary_response(raw_text)
    except (ConnectionError, anthropic.APIConnectionError, anthropic.APITimeoutError):
        logger.error("AI summarization failed due to connection issue", exc_info=True)
        return {
            "summary": "Summary could not be generated.",
            "key_points": [],
            "suggested_tags": [],
        }
    except (anthropic.APIStatusError, anthropic.APIError) as exc:
        logger.error("AI summarization failed due to API error: %s", exc, exc_info=True)
        return {
            "summary": "Summary could not be generated.",
            "key_points": [],
            "suggested_tags": [],
        }
    except (ValueError, KeyError, IndexError):
        logger.error("AI summarization failed due to response parsing error", exc_info=True)
        return {
            "summary": "Summary could not be generated.",
            "key_points": [],
            "suggested_tags": [],
        }


async def suggest_research(existing_tags: list[str], recent_titles: list[str]) -> list[dict[str, str]]:
    """
    Suggest new research topics based on existing vault content.
    Returns a list of {"topic": str, "reason": str, "search_query": str}.
    """
    settings = get_settings()

    prompt = (
        "You are a research advisor for self-publishing authors. "
        "Based on the user's existing research library:\n"
        f"Tags: {', '.join(existing_tags[:30])}\n"
        f"Recent entries: {', '.join(recent_titles[:20])}\n\n"
        "Suggest 5 new research topics they should investigate. "
        "Return ONLY valid JSON: a list of objects with keys: "
        "topic (string), reason (string), search_query (string)."
    )

    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        message = await client.messages.create(
            model=settings.DEFAULT_LLM_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        content_block = message.content[0]
        raw_text = content_block.text if hasattr(content_block, "text") else str(content_block)  # type: ignore[union-attr]
        import json

        data = json.loads(raw_text)
        if isinstance(data, list):
            return data
        return cast("list[dict[str, str]]", data.get("suggestions", []))
    except (ConnectionError, anthropic.APIConnectionError, anthropic.APITimeoutError):
        logger.error("AI suggestion failed due to connection issue", exc_info=True)
        return []
    except (anthropic.APIStatusError, anthropic.APIError) as exc:
        logger.error("AI suggestion failed due to API error: %s", exc, exc_info=True)
        return []
    except (ValueError, json.JSONDecodeError, KeyError, IndexError):
        logger.error("AI suggestion failed due to response parsing error", exc_info=True)
        return []


# ── Helpers ──────────────────────────────────────────────────────


def _parse_extraction_response(raw: str) -> dict[str, Any]:
    import json

    try:
        data = json.loads(raw)
        return {
            "key_facts": data.get("key_facts", ""),
            "tags": data.get("tags", []),
            "credibility_score": data.get("credibility_score"),
        }
    except json.JSONDecodeError:
        return {"key_facts": raw, "tags": [], "credibility_score": None}


def _parse_summary_response(raw: str) -> dict[str, Any]:
    import json

    try:
        data = json.loads(raw)
        return {
            "summary": data.get("summary", ""),
            "key_points": data.get("key_points", []),
            "suggested_tags": data.get("suggested_tags", []),
        }
    except json.JSONDecodeError:
        return {"summary": raw, "key_points": [], "suggested_tags": []}
