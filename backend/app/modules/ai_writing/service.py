"""Business logic for the AI Writing Studio.

Handles chapter CRUD, manuscript management, outline generation,
writing session tracking, and readability analysis.

Uses the canonical ORM models from app.models.content rather than
defining module-local duplicates, to avoid table-definition conflicts
during integration.
"""

from __future__ import annotations

import json
import logging
import os
import uuid as _uuid
from datetime import datetime, timezone
from sqlalchemy import select, update, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

WORD_COUNT_MULTIPLIER = float(os.environ.get("AI_WORD_COUNT_MULTIPLIER", "0.5"))

from app.modules.ai_writing.readability import analyze_readability
from app.modules.ai_writing.schemas import (
    ChapterContent,
    ChapterCreate,
    ChapterReorderRequest,
    ChapterUpdate,
    ManuscriptAnalysis,
    ManuscriptResponse,
    OutlineRequest,
    OutlineResponse,
    OutlineChapter,
    OutlineGenerateRequest,
    OutlineGenerateResponse,
    ChapterOutline,
    ReadabilityScore,
    WritingSessionCreate,
    WritingSessionRecord,
)

# ---------------------------------------------------------------------------
# Canonical ORM models -- imported from the shared models registry so that
# SQLAlchemy sees a single table definition for each table name.
# ---------------------------------------------------------------------------
from app.models.content import (
    Manuscript,
    Chapter,
    WritingSession,
    ContentType,
    ManuscriptStatus,
)


# ---------------------------------------------------------------------------
# Manuscript helpers
# ---------------------------------------------------------------------------

async def _get_or_create_manuscript(db: AsyncSession, book_id: _uuid.UUID) -> Manuscript:
    """Return existing manuscript or create a new one for the given book."""
    result = await db.execute(select(Manuscript).where(Manuscript.book_id == book_id))
    manuscript = result.scalar_one_or_none()
    if not manuscript:
        manuscript = Manuscript(
            id=_uuid.uuid4(),
            book_id=book_id,
            content_type=ContentType.FICTION,
            status=ManuscriptStatus.DRAFT,
        )
        db.add(manuscript)
        await db.flush()
    return manuscript


# ---------------------------------------------------------------------------
# Manuscript / chapter CRUD
# ---------------------------------------------------------------------------

def _chapter_to_schema(ch: Chapter, book_id: _uuid.UUID) -> ChapterContent:
    """Map a canonical Chapter ORM instance to the API schema."""
    return ChapterContent(
        id=ch.id,
        book_id=book_id,
        title=ch.title,
        content=ch.content or "",
        order=ch.order_index,
        synopsis="",
        word_count=ch.word_count,
        created_at=ch.created_at,
        updated_at=ch.updated_at,
    )


async def get_manuscript(db: AsyncSession, book_id: _uuid.UUID) -> ManuscriptResponse:
    """Fetch the full manuscript with all chapters."""
    manuscript = await _get_or_create_manuscript(db, book_id)
    result = await db.execute(
        select(Chapter)
        .where(Chapter.manuscript_id == manuscript.id)
        .order_by(Chapter.order_index)
    )
    chapters = result.scalars().all()

    chapter_items = [_chapter_to_schema(ch, book_id) for ch in chapters]
    total_words = sum(ch.word_count for ch in chapters)
    return ManuscriptResponse(
        book_id=book_id,
        title="",
        chapters=chapter_items,
        total_word_count=total_words,
    )


async def list_chapters(db: AsyncSession, book_id: _uuid.UUID) -> list[ChapterContent]:
    """List all chapters for a book, ordered."""
    manuscript = await _get_or_create_manuscript(db, book_id)
    result = await db.execute(
        select(Chapter)
        .where(Chapter.manuscript_id == manuscript.id)
        .order_by(Chapter.order_index)
    )
    chapters = result.scalars().all()
    return [_chapter_to_schema(ch, book_id) for ch in chapters]


async def get_chapter(
    db: AsyncSession, book_id: _uuid.UUID, chapter_id: _uuid.UUID
) -> ChapterContent:
    """Fetch a single chapter."""
    manuscript = await _get_or_create_manuscript(db, book_id)
    result = await db.execute(
        select(Chapter).where(
            Chapter.manuscript_id == manuscript.id,
            Chapter.id == chapter_id,
        )
    )
    ch = result.scalar_one_or_none()
    if not ch:
        raise AppException(
            status_code=404,
            code="CHAPTER_NOT_FOUND",
            message=f"Chapter {chapter_id} not found for book {book_id}",
        )
    return _chapter_to_schema(ch, book_id)


async def create_chapter(
    db: AsyncSession, book_id: _uuid.UUID, data: ChapterCreate
) -> ChapterContent:
    """Create a new chapter for a book."""
    manuscript = await _get_or_create_manuscript(db, book_id)
    word_count = len(data.content.split()) if data.content else 0

    chapter = Chapter(
        id=_uuid.uuid4(),
        manuscript_id=manuscript.id,
        title=data.title,
        content=data.content or "",
        order_index=data.order,
        word_count=word_count,
    )
    db.add(chapter)
    await db.flush()
    await db.refresh(chapter)

    return _chapter_to_schema(chapter, book_id)


async def update_chapter(
    db: AsyncSession,
    book_id: _uuid.UUID,
    chapter_id: _uuid.UUID,
    data: ChapterUpdate,
) -> ChapterContent:
    """Update an existing chapter."""
    manuscript = await _get_or_create_manuscript(db, book_id)
    result = await db.execute(
        select(Chapter).where(
            Chapter.manuscript_id == manuscript.id,
            Chapter.id == chapter_id,
        )
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise AppException(
            status_code=404,
            code="CHAPTER_NOT_FOUND",
            message=f"Chapter {chapter_id} not found for book {book_id}",
        )

    update_data = data.model_dump(exclude_unset=True)
    if "content" in update_data:
        update_data["word_count"] = len(update_data["content"].split()) if update_data["content"] else 0

    # Map schema field names to canonical ORM column names
    field_map = {"order": "order_index", "synopsis": None}
    for field, value in update_data.items():
        orm_field = field_map.get(field, field)
        if orm_field is not None:
            setattr(chapter, orm_field, value)

    await db.flush()
    await db.refresh(chapter)

    return _chapter_to_schema(chapter, book_id)


async def reorder_chapters(
    db: AsyncSession, book_id: _uuid.UUID, reorder: ChapterReorderRequest
) -> list[ChapterContent]:
    """Reorder chapters based on the provided order mapping."""
    manuscript = await _get_or_create_manuscript(db, book_id)
    for item in reorder.chapters:
        await db.execute(
            update(Chapter)
            .where(
                Chapter.manuscript_id == manuscript.id,
                Chapter.id == item.chapter_id,
            )
            .values(order_index=item.order)
        )
    await db.flush()
    return await list_chapters(db, book_id)


# ---------------------------------------------------------------------------
# Readability / analysis
# ---------------------------------------------------------------------------

async def get_readability_score(
    db: AsyncSession, book_id: _uuid.UUID
) -> ReadabilityScore:
    """Compute readability metrics for the full manuscript."""
    manuscript = await _get_or_create_manuscript(db, book_id)
    result = await db.execute(
        select(Chapter.content)
        .where(Chapter.manuscript_id == manuscript.id)
        .order_by(Chapter.order_index)
    )
    contents = result.scalars().all()
    full_text = "\n\n".join(c for c in contents if c)
    metrics = analyze_readability(full_text)

    return ReadabilityScore(
        flesch_kincaid_grade=metrics.flesch_kincaid_grade,
        flesch_reading_ease=metrics.flesch_reading_ease,
        gunning_fog=metrics.gunning_fog,
        smog_index=metrics.smog_index,
        word_count=metrics.word_count,
        sentence_count=metrics.sentence_count,
        syllable_count=metrics.syllable_count,
        avg_words_per_sentence=metrics.avg_words_per_sentence,
        avg_syllables_per_word=metrics.avg_syllables_per_word,
        reading_level=metrics.reading_level,
    )


async def analyze_manuscript(
    db: AsyncSession, book_id: _uuid.UUID
) -> ManuscriptAnalysis:
    """Full manuscript analysis including readability, pacing, word count."""
    readability = await get_readability_score(db, book_id)

    manuscript = await _get_or_create_manuscript(db, book_id)
    result = await db.execute(
        select(Chapter)
        .where(Chapter.manuscript_id == manuscript.id)
        .order_by(Chapter.order_index)
    )
    chapters = result.scalars().all()
    chapter_count = len(chapters)
    word_counts = [ch.word_count for ch in chapters]
    total_words = sum(word_counts)
    avg_chapter_wc = round(total_words / chapter_count, 1) if chapter_count else 0.0

    # Simple pacing analysis
    pacing_notes: list[str] = []
    if chapter_count > 0:
        if avg_chapter_wc < 1500:
            pacing_notes.append("Chapters are short. Consider expanding key scenes.")
        elif avg_chapter_wc > 5000:
            pacing_notes.append("Chapters are long. Consider splitting for better pacing.")

        for ch in chapters:
            if ch.word_count > 0 and ch.word_count < avg_chapter_wc * WORD_COUNT_MULTIPLIER:
                pacing_notes.append(
                    f"Chapter '{ch.title}' (#{ch.order_index}) is significantly shorter than average."
                )
            elif ch.word_count > avg_chapter_wc * 1.5:
                pacing_notes.append(
                    f"Chapter '{ch.title}' (#{ch.order_index}) is significantly longer than average."
                )

    return ManuscriptAnalysis(
        book_id=book_id,
        readability=readability,
        total_word_count=total_words,
        chapter_count=chapter_count,
        avg_chapter_word_count=avg_chapter_wc,
        pacing_notes=pacing_notes,
    )


# ---------------------------------------------------------------------------
# Outline generation
# ---------------------------------------------------------------------------

async def generate_outline(
    db: AsyncSession,
    book_id: _uuid.UUID,
    request: OutlineRequest,
) -> OutlineResponse:
    """Generate a book outline using AI and optionally save chapters."""
    from app.modules.ai_writing.prompts import outline_prompt
    from app.modules.ai_writing.generator import _call_llm, resolve_model

    context = {
        "genre": request.genre,
        "premise": request.premise,
        "num_chapters": request.num_chapters,
        "tone": request.tone,
        "target_audience": request.target_audience,
        "additional_instructions": request.additional_instructions,
    }
    system_msg, user_msg = outline_prompt(context)
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]
    model = resolve_model("auto")
    raw = await _call_llm(messages, model)

    # Parse the JSON from the LLM response
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        import re
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
        else:
            data = {"chapters": [], "summary": raw}

    chapters = [
        OutlineChapter(
            title=ch.get("title", f"Chapter {i + 1}"),
            synopsis=ch.get("synopsis", ""),
            key_points=ch.get("key_points", []),
        )
        for i, ch in enumerate(data.get("chapters", []))
    ]

    return OutlineResponse(
        book_id=book_id,
        chapters=chapters,
        summary=data.get("summary", ""),
        generated_at=datetime.now(timezone.utc),
    )


async def generate_outline_standalone(
    request: OutlineGenerateRequest,
    db: AsyncSession,
) -> OutlineGenerateResponse:
    """Generate a book outline using AI without requiring an existing book.

    Builds a structured system prompt for outline generation, calls the LLM
    following the same pattern as the book-bound outline endpoint, and parses
    the response into typed ChapterOutline objects.
    """
    from app.modules.ai_writing.generator import _call_llm, resolve_model

    # -- Build the system prompt ------------------------------------------------
    system_parts = [
        "You are an expert book outline architect. You create detailed, "
        "well-structured book outlines that serve as comprehensive blueprints "
        "for authors.",
        f"Genre: {request.genre}.",
        f"Tone: {request.tone}.",
    ]
    system_msg = " ".join(system_parts)

    # -- Build the user prompt --------------------------------------------------
    user_parts = [
        f'Generate a detailed outline for a book titled "{request.book_title}".',
        f"Genre: {request.genre}.",
        f"Number of chapters: {request.num_chapters}.",
    ]
    if request.premise:
        user_parts.append(f"Premise: {request.premise}")
    if request.target_audience:
        user_parts.append(f"Target audience: {request.target_audience}")

    user_parts.append(
        "\nFor each chapter provide:\n"
        "- chapter_number (integer)\n"
        "- title (string)\n"
        "- description (2-3 sentence summary)\n"
        "- key_points (list of 2-4 bullet points)\n"
        "- estimated_word_count (integer)\n\n"
        "Also include a 'synopsis' field with a 2-3 paragraph overall book synopsis.\n\n"
        "Return ONLY valid JSON with the structure:\n"
        '{"chapters": [{"chapter_number": 1, "title": "...", "description": "...", '
        '"key_points": ["..."], "estimated_word_count": 3000}], '
        '"synopsis": "overall book synopsis"}'
    )
    user_msg = "\n".join(user_parts)

    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]
    model = resolve_model("auto")
    raw = await _call_llm(messages, model)

    # -- Parse the LLM JSON response -------------------------------------------
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        import re as _re
        json_match = _re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, _re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
        else:
            data = {"chapters": [], "synopsis": raw}

    chapters = [
        ChapterOutline(
            chapter_number=ch.get("chapter_number", i + 1),
            title=ch.get("title", f"Chapter {i + 1}"),
            description=ch.get("description", ch.get("synopsis", "")),
            key_points=ch.get("key_points", []),
            estimated_word_count=ch.get("estimated_word_count", 3000),
        )
        for i, ch in enumerate(data.get("chapters", []))
    ]

    return OutlineGenerateResponse(
        book_title=request.book_title,
        genre=request.genre,
        total_chapters=len(chapters),
        chapters=chapters,
        synopsis=data.get("synopsis", ""),
    )


# ---------------------------------------------------------------------------
# Writing sessions
# ---------------------------------------------------------------------------

async def record_writing_session(
    db: AsyncSession,
    user_id: _uuid.UUID,
    data: WritingSessionCreate,
) -> WritingSessionRecord:
    """Record a writing session.

    The canonical WritingSession model stores duration in seconds, so we
    convert from the API's minutes representation.
    """
    session = WritingSession(
        id=_uuid.uuid4(),
        user_id=user_id,
        book_id=data.book_id,
        chapter_id=data.chapter_id,
        words_written=data.words_written,
        duration_seconds=data.duration_minutes * 60,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)

    return WritingSessionRecord(
        id=session.id,
        user_id=session.user_id,
        book_id=session.book_id,
        words_written=session.words_written,
        duration_minutes=session.duration_seconds // 60,
        chapter_id=session.chapter_id,
        notes=data.notes,
        created_at=session.created_at,
    )
