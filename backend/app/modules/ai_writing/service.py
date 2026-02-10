"""Business logic for the AI Writing Studio.

Handles chapter CRUD, manuscript management, outline generation,
writing session tracking, and readability analysis.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import BaseModel as DBBaseModel
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
    ReadabilityScore,
    WritingSessionCreate,
    WritingSessionRecord,
)


# ---------------------------------------------------------------------------
# Lightweight ORM models (module-local so we don't modify shared models)
# ---------------------------------------------------------------------------
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid as _uuid


class Manuscript(DBBaseModel):
    __tablename__ = "manuscripts"
    __table_args__ = {"extend_existing": True}

    book_id: Mapped[_uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[str] = mapped_column(String(50), default="draft")


class Chapter(DBBaseModel):
    __tablename__ = "chapters"
    __table_args__ = {"extend_existing": True}

    manuscript_id: Mapped[_uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("manuscripts.id"), index=True)
    book_id: Mapped[_uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), index=True)
    title: Mapped[str] = mapped_column(String(500), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    synopsis: Mapped[str] = mapped_column(Text, default="")
    order: Mapped[int] = mapped_column(Integer, default=0)
    word_count: Mapped[int] = mapped_column(Integer, default=0)


class WritingSession(DBBaseModel):
    __tablename__ = "writing_sessions"
    __table_args__ = {"extend_existing": True}

    user_id: Mapped[_uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), index=True)
    book_id: Mapped[_uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), index=True)
    chapter_id: Mapped[_uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    words_written: Mapped[int] = mapped_column(Integer, default=0)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")


# ---------------------------------------------------------------------------
# Manuscript helpers
# ---------------------------------------------------------------------------

async def _get_or_create_manuscript(db: AsyncSession, book_id: _uuid.UUID) -> Manuscript:
    """Return existing manuscript or create a new one for the given book."""
    result = await db.execute(select(Manuscript).where(Manuscript.book_id == book_id))
    manuscript = result.scalar_one_or_none()
    if not manuscript:
        manuscript = Manuscript(id=_uuid.uuid4(), book_id=book_id, title="", status="draft")
        db.add(manuscript)
        await db.flush()
    return manuscript


# ---------------------------------------------------------------------------
# Manuscript / chapter CRUD
# ---------------------------------------------------------------------------

async def get_manuscript(db: AsyncSession, book_id: _uuid.UUID) -> ManuscriptResponse:
    """Fetch the full manuscript with all chapters."""
    manuscript = await _get_or_create_manuscript(db, book_id)
    result = await db.execute(
        select(Chapter).where(Chapter.book_id == book_id).order_by(Chapter.order)
    )
    chapters = result.scalars().all()

    chapter_items = [
        ChapterContent(
            id=ch.id,
            book_id=ch.book_id,
            title=ch.title,
            content=ch.content,
            order=ch.order,
            synopsis=ch.synopsis,
            word_count=ch.word_count,
            created_at=ch.created_at,
            updated_at=ch.updated_at,
        )
        for ch in chapters
    ]
    total_words = sum(ch.word_count for ch in chapters)
    return ManuscriptResponse(
        book_id=book_id,
        title=manuscript.title,
        chapters=chapter_items,
        total_word_count=total_words,
    )


async def list_chapters(db: AsyncSession, book_id: _uuid.UUID) -> list[ChapterContent]:
    """List all chapters for a book, ordered."""
    result = await db.execute(
        select(Chapter).where(Chapter.book_id == book_id).order_by(Chapter.order)
    )
    chapters = result.scalars().all()
    return [
        ChapterContent(
            id=ch.id,
            book_id=ch.book_id,
            title=ch.title,
            content=ch.content,
            order=ch.order,
            synopsis=ch.synopsis,
            word_count=ch.word_count,
            created_at=ch.created_at,
            updated_at=ch.updated_at,
        )
        for ch in chapters
    ]


async def get_chapter(
    db: AsyncSession, book_id: _uuid.UUID, chapter_id: _uuid.UUID
) -> ChapterContent | None:
    """Fetch a single chapter."""
    result = await db.execute(
        select(Chapter).where(Chapter.book_id == book_id, Chapter.id == chapter_id)
    )
    ch = result.scalar_one_or_none()
    if not ch:
        return None
    return ChapterContent(
        id=ch.id,
        book_id=ch.book_id,
        title=ch.title,
        content=ch.content,
        order=ch.order,
        synopsis=ch.synopsis,
        word_count=ch.word_count,
        created_at=ch.created_at,
        updated_at=ch.updated_at,
    )


async def create_chapter(
    db: AsyncSession, book_id: _uuid.UUID, data: ChapterCreate
) -> ChapterContent:
    """Create a new chapter for a book."""
    manuscript = await _get_or_create_manuscript(db, book_id)
    word_count = len(data.content.split()) if data.content else 0

    chapter = Chapter(
        id=_uuid.uuid4(),
        manuscript_id=manuscript.id,
        book_id=book_id,
        title=data.title,
        content=data.content,
        synopsis=data.synopsis,
        order=data.order,
        word_count=word_count,
    )
    db.add(chapter)
    await db.flush()
    await db.refresh(chapter)

    return ChapterContent(
        id=chapter.id,
        book_id=chapter.book_id,
        title=chapter.title,
        content=chapter.content,
        order=chapter.order,
        synopsis=chapter.synopsis,
        word_count=chapter.word_count,
        created_at=chapter.created_at,
        updated_at=chapter.updated_at,
    )


async def update_chapter(
    db: AsyncSession,
    book_id: _uuid.UUID,
    chapter_id: _uuid.UUID,
    data: ChapterUpdate,
) -> ChapterContent | None:
    """Update an existing chapter."""
    result = await db.execute(
        select(Chapter).where(Chapter.book_id == book_id, Chapter.id == chapter_id)
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        return None

    update_data = data.model_dump(exclude_unset=True)
    if "content" in update_data:
        update_data["word_count"] = len(update_data["content"].split()) if update_data["content"] else 0

    for field, value in update_data.items():
        setattr(chapter, field, value)

    await db.flush()
    await db.refresh(chapter)

    return ChapterContent(
        id=chapter.id,
        book_id=chapter.book_id,
        title=chapter.title,
        content=chapter.content,
        order=chapter.order,
        synopsis=chapter.synopsis,
        word_count=chapter.word_count,
        created_at=chapter.created_at,
        updated_at=chapter.updated_at,
    )


async def reorder_chapters(
    db: AsyncSession, book_id: _uuid.UUID, reorder: ChapterReorderRequest
) -> list[ChapterContent]:
    """Reorder chapters based on the provided order mapping."""
    for item in reorder.chapters:
        await db.execute(
            update(Chapter)
            .where(Chapter.book_id == book_id, Chapter.id == item.chapter_id)
            .values(order=item.order)
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
    result = await db.execute(
        select(Chapter.content).where(Chapter.book_id == book_id).order_by(Chapter.order)
    )
    contents = result.scalars().all()
    full_text = "\n\n".join(contents)
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

    result = await db.execute(
        select(Chapter).where(Chapter.book_id == book_id).order_by(Chapter.order)
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
            if ch.word_count > 0 and ch.word_count < avg_chapter_wc * 0.5:
                pacing_notes.append(
                    f"Chapter '{ch.title}' (#{ch.order}) is significantly shorter than average."
                )
            elif ch.word_count > avg_chapter_wc * 1.5:
                pacing_notes.append(
                    f"Chapter '{ch.title}' (#{ch.order}) is significantly longer than average."
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


# ---------------------------------------------------------------------------
# Writing sessions
# ---------------------------------------------------------------------------

async def record_writing_session(
    db: AsyncSession,
    user_id: _uuid.UUID,
    data: WritingSessionCreate,
) -> WritingSessionRecord:
    """Record a writing session."""
    session = WritingSession(
        id=_uuid.uuid4(),
        user_id=user_id,
        book_id=data.book_id,
        chapter_id=data.chapter_id,
        words_written=data.words_written,
        duration_minutes=data.duration_minutes,
        notes=data.notes,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)

    return WritingSessionRecord(
        id=session.id,
        user_id=session.user_id,
        book_id=session.book_id,
        words_written=session.words_written,
        duration_minutes=session.duration_minutes,
        chapter_id=session.chapter_id,
        notes=session.notes,
        created_at=session.created_at,
    )
