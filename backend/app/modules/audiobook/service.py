"""Service layer for audiobook SSML generation and pronunciation dictionary."""

from __future__ import annotations

import logging
import re
import uuid
from xml.etree import ElementTree

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audiobook import AudiobookChapter, AudiobookPronunciation
from app.modules.audiobook.schemas import PronunciationCreate

logger = logging.getLogger(__name__)


# ── SSML ───────────────────────────────────────────────────────────────────


async def generate_ssml(
    db: AsyncSession,
    project_id: uuid.UUID,
    chapter_id: uuid.UUID,
    org_id: uuid.UUID,
    options: dict | None = None,
) -> dict:
    """Generate SSML from a chapter's plain text.

    Steps:
      1. Get chapter source_text
      2. Get project's pronunciation dictionary
      3. Generate SSML via SSMLGenerator
      4. Save ssml_text to chapter
      5. Return SSML result with dialogue/emotion segments
    """
    chapter = await _get_chapter(db, project_id, chapter_id)
    if not chapter:
        return None  # type: ignore[return-value]

    # Fetch pronunciation dictionary for the project (project-specific + org-wide)
    pron_entries = await list_pronunciation(db, org_id, project_id=project_id)
    pron_dict = {e.word: e.ssml_phoneme or e.phonetic for e in pron_entries}

    # Build project config from options
    project_config = options or {}

    # Try to use SSMLGenerator service; fall back to basic conversion
    try:
        from app.services.voiceforge.ssml_generator import SSMLGenerator

        generator = SSMLGenerator()
        result = await generator.generate_ssml(
            text=chapter.source_text,
            project_config=project_config,
            pronunciation_dict=pron_dict,
        )
        ssml_text = result.ssml_text
        dialogue_segments = [
            {
                "character": seg.character,
                "text": seg.text,
                "emotion": seg.emotion,
                "start_index": seg.start_index,
                "end_index": seg.end_index,
            }
            for seg in result.dialogue_segments
        ]
        emotion_segments = [
            {
                "text": seg.text,
                "emotion": seg.emotion,
                "intensity": seg.intensity,
                "start_index": seg.start_index,
                "end_index": seg.end_index,
            }
            for seg in result.emotion_segments
        ]
    except (ImportError, Exception):
        logger.info(
            "SSMLGenerator unavailable, using basic SSML conversion for chapter %s",
            chapter_id,
        )
        ssml_text = _basic_ssml_conversion(chapter.source_text, pron_dict)
        dialogue_segments = _detect_dialogue_basic(chapter.source_text)
        emotion_segments = []

    # Save to chapter
    chapter.ssml_text = ssml_text
    await db.flush()

    return {
        "chapter_id": chapter.id,
        "original_text": chapter.source_text,
        "ssml_text": ssml_text,
        "dialogue_segments": dialogue_segments,
        "emotion_segments": emotion_segments,
    }


async def update_ssml(
    db: AsyncSession,
    project_id: uuid.UUID,
    chapter_id: uuid.UUID,
    org_id: uuid.UUID,
    ssml_text: str,
) -> dict:
    """Update a chapter's SSML text (manual edits).

    Validates SSML syntax before saving.
    """
    chapter = await _get_chapter(db, project_id, chapter_id)
    if not chapter:
        return None  # type: ignore[return-value]

    # Validate SSML syntax
    validation = _validate_ssml(ssml_text)
    if not validation["valid"]:
        raise ValueError(f"Invalid SSML: {validation['error']}")

    chapter.ssml_text = ssml_text
    await db.flush()

    return {
        "chapter_id": chapter.id,
        "original_text": chapter.source_text,
        "ssml_text": ssml_text,
        "dialogue_segments": [],
        "emotion_segments": [],
    }


# ── Pronunciation ──────────────────────────────────────────────────────────


async def add_pronunciation(
    db: AsyncSession,
    org_id: uuid.UUID,
    request: PronunciationCreate,
) -> AudiobookPronunciation:
    """Add a word to the pronunciation dictionary."""
    entry = AudiobookPronunciation(
        org_id=org_id,
        audiobook_project_id=request.audiobook_project_id,
        word=request.word,
        phonetic=request.phonetic,
        ssml_phoneme=request.ssml_phoneme,
        context=request.context,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


async def list_pronunciation(
    db: AsyncSession,
    org_id: uuid.UUID,
    project_id: uuid.UUID | None = None,
) -> list[AudiobookPronunciation]:
    """List pronunciation entries for an org, optionally filtered by project."""
    query = select(AudiobookPronunciation).where(
        AudiobookPronunciation.org_id == org_id,
        AudiobookPronunciation.active.is_(True),
        AudiobookPronunciation.deleted_at.is_(None),
    )
    if project_id:
        query = query.where(
            (AudiobookPronunciation.audiobook_project_id == project_id)
            | (AudiobookPronunciation.audiobook_project_id.is_(None))
        )
    query = query.order_by(AudiobookPronunciation.word)
    result = await db.execute(query)
    return list(result.scalars().all())


async def delete_pronunciation(
    db: AsyncSession,
    pron_id: uuid.UUID,
    org_id: uuid.UUID,
) -> bool:
    """Soft-delete a pronunciation entry."""
    stmt = select(AudiobookPronunciation).where(
        AudiobookPronunciation.id == pron_id,
        AudiobookPronunciation.org_id == org_id,
        AudiobookPronunciation.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()
    if not entry:
        return False
    entry.active = False
    from datetime import UTC, datetime

    entry.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


# ── Internal helpers ───────────────────────────────────────────────────────


async def _get_chapter(
    db: AsyncSession,
    project_id: uuid.UUID,
    chapter_id: uuid.UUID,
) -> AudiobookChapter | None:
    """Fetch a chapter belonging to the given project."""
    stmt = select(AudiobookChapter).where(
        AudiobookChapter.id == chapter_id,
        AudiobookChapter.audiobook_project_id == project_id,
        AudiobookChapter.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def _basic_ssml_conversion(text: str, pronunciation_dict: dict[str, str]) -> str:
    """Convert plain text to basic SSML when the full generator is unavailable."""
    # Escape XML special characters
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )

    # Split into paragraphs and add breaks
    paragraphs = [p.strip() for p in escaped.split("\n\n") if p.strip()]
    ssml_parts: list[str] = []
    for para in paragraphs:
        ssml_parts.append(f"<p>{para}</p>")

    ssml_body = '\n<break time="500ms"/>\n'.join(ssml_parts)
    ssml_text = f'<speak>\n{ssml_body}\n</speak>'

    # Apply pronunciation dictionary
    for word, phoneme in pronunciation_dict.items():
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        replacement = f'<phoneme alphabet="ipa" ph="{phoneme}">{word}</phoneme>'
        ssml_text = pattern.sub(replacement, ssml_text)

    return ssml_text


def _detect_dialogue_basic(text: str) -> list[dict]:
    """Basic regex-based dialogue detection for fallback."""
    segments: list[dict] = []
    # Match quoted speech: "..." or \u201c...\u201d
    dialogue_re = (
        r'["\u201c]([^"\u201d]+)["\u201d]'
        r"\s*(?:,?\s*(?:said|asked|replied|whispered|shouted|exclaimed|muttered)\s+(\w+))?"
    )
    pattern = re.compile(dialogue_re, re.IGNORECASE)
    for match in pattern.finditer(text):
        character = match.group(2) or "narrator"
        segments.append(
            {
                "character": character,
                "text": match.group(1),
                "emotion": None,
                "start_index": match.start(),
                "end_index": match.end(),
            }
        )
    return segments


def _validate_ssml(ssml_text: str) -> dict:
    """Validate SSML syntax by parsing as XML."""
    try:
        ElementTree.fromstring(ssml_text)  # noqa: S314
        return {"valid": True, "error": None}
    except ElementTree.ParseError as e:
        return {"valid": False, "error": str(e)}
