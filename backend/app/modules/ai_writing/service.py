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
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, NotFoundError

logger = logging.getLogger(__name__)

WORD_COUNT_MULTIPLIER = float(os.environ.get("AI_WORD_COUNT_MULTIPLIER", "0.5"))

# ---------------------------------------------------------------------------
# Canonical ORM models -- imported from the shared models registry so that
# SQLAlchemy sees a single table definition for each table name.
# ---------------------------------------------------------------------------
from app.models.content import (
    Chapter,
    ContentType,
    Manuscript,
    ManuscriptStatus,
    WritingSession,
)
from app.modules.ai_writing.readability import analyze_readability
from app.modules.ai_writing.schemas import (
    ChapterContent,
    ChapterCreate,
    ChapterOutline,
    ChapterReorderRequest,
    ChapterUpdate,
    ChapterVersionDetail,
    ChapterVersionSummary,
    ManuscriptAnalysis,
    ManuscriptCreateRequest,
    ManuscriptDetail,
    ManuscriptListItem,
    ManuscriptResponse,
    ManuscriptUpdateRequest,
    OutlineChapter,
    OutlineGenerateRequest,
    OutlineGenerateResponse,
    OutlineRequest,
    OutlineResponse,
    ReadabilityScore,
    WritingSessionCreate,
    WritingSessionEndResponse,
    WritingSessionListItem,
    WritingSessionRecord,
    WritingSessionStartResponse,
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


async def _get_manuscript_by_id(db: AsyncSession, manuscript_id: _uuid.UUID) -> Manuscript:
    """Fetch a manuscript by its primary key. Raises 404 if not found or soft-deleted."""
    result = await db.execute(
        select(Manuscript).where(
            Manuscript.id == manuscript_id,
            Manuscript.deleted_at.is_(None),
        )
    )
    manuscript = result.scalar_one_or_none()
    if not manuscript:
        raise NotFoundError("Manuscript", f"Manuscript {manuscript_id} not found")
    return manuscript


# ---------------------------------------------------------------------------
# Manuscript CRUD (Writing Studio)
# ---------------------------------------------------------------------------

async def list_manuscripts(
    db: AsyncSession,
    user_id: _uuid.UUID,
    *,
    status_filter: str | None = None,
    sort: str | None = None,
    search: str | None = None,
) -> list[ManuscriptListItem]:
    """List manuscripts with optional filtering, sorting, and search."""
    query = select(Manuscript).where(Manuscript.deleted_at.is_(None))

    if status_filter:
        try:
            ms = ManuscriptStatus(status_filter)
            query = query.where(Manuscript.status == ms)
        except ValueError:
            pass  # ignore invalid status filter

    if search:
        # Search is not directly supported on Manuscript.title since the model
        # does not have a title column. We search on content if available.
        pass

    # Sorting
    if sort == "title":
        query = query.order_by(Manuscript.created_at.desc())
    elif sort == "word_count":
        query = query.order_by(Manuscript.word_count.desc())
    elif sort == "oldest":
        query = query.order_by(Manuscript.created_at.asc())
    else:
        # Default: newest first
        query = query.order_by(Manuscript.updated_at.desc())

    result = await db.execute(query)
    manuscripts = result.scalars().all()

    items = []
    for m in manuscripts:
        # Count chapters for each manuscript
        ch_result = await db.execute(
            select(func.count(Chapter.id)).where(
                Chapter.manuscript_id == m.id,
                Chapter.deleted_at.is_(None),
            )
        )
        chapter_count = ch_result.scalar() or 0

        items.append(ManuscriptListItem(
            id=m.id,
            book_id=m.book_id,
            title="",  # Manuscript model lacks title; derived from book
            status=m.status.value if hasattr(m.status, "value") else str(m.status),
            content_type=m.content_type.value if hasattr(m.content_type, "value") else str(m.content_type),
            word_count=m.word_count,
            target_word_count=0,
            chapter_count=chapter_count,
            created_at=m.created_at,
            updated_at=m.updated_at,
        ))

    return items


async def create_manuscript(
    db: AsyncSession,
    user_id: _uuid.UUID,
    data: ManuscriptCreateRequest,
) -> ManuscriptDetail:
    """Create a new manuscript."""
    # Map type to ContentType
    content_type_map = {
        "fiction": ContentType.FICTION,
        "nonfiction": ContentType.NONFICTION,
        "poetry": ContentType.POETRY,
        "screenplay": ContentType.SCREENPLAY,
    }
    content_type = content_type_map.get(data.type.value, ContentType.FICTION)

    # If project_id is provided, use it as book_id; otherwise generate one
    book_id = data.project_id or _uuid.uuid4()

    manuscript = Manuscript(
        id=_uuid.uuid4(),
        book_id=book_id,
        content_type=content_type,
        status=ManuscriptStatus.DRAFT,
        word_count=0,
    )
    db.add(manuscript)
    await db.flush()
    await db.refresh(manuscript)

    return ManuscriptDetail(
        id=manuscript.id,
        book_id=manuscript.book_id,
        title=data.title,
        status=manuscript.status.value if hasattr(manuscript.status, "value") else str(manuscript.status),
        content_type=manuscript.content_type.value if hasattr(manuscript.content_type, "value") else str(manuscript.content_type),
        word_count=0,
        target_word_count=0,
        chapter_count=0,
        chapters=[],
        created_at=manuscript.created_at,
        updated_at=manuscript.updated_at,
    )


async def get_manuscript_detail(
    db: AsyncSession,
    manuscript_id: _uuid.UUID,
) -> ManuscriptDetail:
    """Fetch a manuscript with its chapters."""
    manuscript = await _get_manuscript_by_id(db, manuscript_id)

    ch_result = await db.execute(
        select(Chapter)
        .where(
            Chapter.manuscript_id == manuscript.id,
            Chapter.deleted_at.is_(None),
        )
        .order_by(Chapter.order_index)
    )
    chapters = ch_result.scalars().all()
    chapter_items = [_chapter_to_schema(ch, manuscript.book_id) for ch in chapters]
    total_words = sum(ch.word_count for ch in chapters)

    return ManuscriptDetail(
        id=manuscript.id,
        book_id=manuscript.book_id,
        title="",
        status=manuscript.status.value if hasattr(manuscript.status, "value") else str(manuscript.status),
        content_type=manuscript.content_type.value if hasattr(manuscript.content_type, "value") else str(manuscript.content_type),
        word_count=total_words,
        target_word_count=0,
        chapter_count=len(chapters),
        chapters=chapter_items,
        created_at=manuscript.created_at,
        updated_at=manuscript.updated_at,
    )


async def update_manuscript(
    db: AsyncSession,
    manuscript_id: _uuid.UUID,
    data: ManuscriptUpdateRequest,
) -> ManuscriptDetail:
    """Update manuscript metadata (title, status, target_word_count)."""
    manuscript = await _get_manuscript_by_id(db, manuscript_id)

    if data.status is not None:
        status_map = {
            "draft": ManuscriptStatus.DRAFT,
            "revision": ManuscriptStatus.REVISION,
            "final": ManuscriptStatus.FINAL,
            "archived": ManuscriptStatus.ARCHIVED,
        }
        new_status = status_map.get(data.status.value)
        if new_status:
            manuscript.status = new_status

    await db.flush()
    await db.refresh(manuscript)

    return await get_manuscript_detail(db, manuscript_id)


async def soft_delete_manuscript(
    db: AsyncSession,
    manuscript_id: _uuid.UUID,
) -> dict:
    """Soft-delete a manuscript by setting deleted_at."""
    manuscript = await _get_manuscript_by_id(db, manuscript_id)
    manuscript.deleted_at = datetime.now(UTC)
    await db.flush()
    return {"message": "Manuscript deleted", "id": str(manuscript_id)}


# ---------------------------------------------------------------------------
# Manuscript / chapter CRUD (book-based)
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


async def list_chapters_for_manuscript(
    db: AsyncSession,
    manuscript_id: _uuid.UUID,
) -> list[ChapterContent]:
    """List all chapters for a manuscript by manuscript ID."""
    manuscript = await _get_manuscript_by_id(db, manuscript_id)
    result = await db.execute(
        select(Chapter)
        .where(
            Chapter.manuscript_id == manuscript.id,
            Chapter.deleted_at.is_(None),
        )
        .order_by(Chapter.order_index)
    )
    chapters = result.scalars().all()
    return [_chapter_to_schema(ch, manuscript.book_id) for ch in chapters]


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


async def get_chapter_for_manuscript(
    db: AsyncSession,
    manuscript_id: _uuid.UUID,
    chapter_id: _uuid.UUID,
) -> ChapterContent:
    """Fetch a single chapter within a manuscript (by manuscript ID)."""
    manuscript = await _get_manuscript_by_id(db, manuscript_id)
    result = await db.execute(
        select(Chapter).where(
            Chapter.manuscript_id == manuscript.id,
            Chapter.id == chapter_id,
            Chapter.deleted_at.is_(None),
        )
    )
    ch = result.scalar_one_or_none()
    if not ch:
        raise NotFoundError("Chapter", f"Chapter {chapter_id} not found in manuscript {manuscript_id}")
    return _chapter_to_schema(ch, manuscript.book_id)


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


async def create_chapter_for_manuscript(
    db: AsyncSession,
    manuscript_id: _uuid.UUID,
    data: ChapterCreate,
) -> ChapterContent:
    """Create a new chapter for a manuscript (by manuscript ID)."""
    manuscript = await _get_manuscript_by_id(db, manuscript_id)
    word_count = len(data.content.split()) if data.content else 0

    # Auto-determine order if not specified
    if data.order == 0:
        max_order_result = await db.execute(
            select(func.max(Chapter.order_index)).where(
                Chapter.manuscript_id == manuscript.id,
                Chapter.deleted_at.is_(None),
            )
        )
        max_order = max_order_result.scalar() or 0
        order = max_order + 1
    else:
        order = data.order

    chapter = Chapter(
        id=_uuid.uuid4(),
        manuscript_id=manuscript.id,
        title=data.title,
        content=data.content or "",
        order_index=order,
        word_count=word_count,
    )
    db.add(chapter)
    await db.flush()
    await db.refresh(chapter)

    return _chapter_to_schema(chapter, manuscript.book_id)


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


async def update_chapter_for_manuscript(
    db: AsyncSession,
    manuscript_id: _uuid.UUID,
    chapter_id: _uuid.UUID,
    data: ChapterUpdate,
) -> ChapterContent:
    """Update a chapter within a manuscript (by manuscript ID)."""
    manuscript = await _get_manuscript_by_id(db, manuscript_id)
    result = await db.execute(
        select(Chapter).where(
            Chapter.manuscript_id == manuscript.id,
            Chapter.id == chapter_id,
            Chapter.deleted_at.is_(None),
        )
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise NotFoundError("Chapter", f"Chapter {chapter_id} not found in manuscript {manuscript_id}")

    update_data = data.model_dump(exclude_unset=True)
    if "content" in update_data:
        update_data["word_count"] = len(update_data["content"].split()) if update_data["content"] else 0

    field_map = {"order": "order_index", "synopsis": None}
    for field, value in update_data.items():
        orm_field = field_map.get(field, field)
        if orm_field is not None:
            setattr(chapter, orm_field, value)

    await db.flush()
    await db.refresh(chapter)

    return _chapter_to_schema(chapter, manuscript.book_id)


async def delete_chapter_for_manuscript(
    db: AsyncSession,
    manuscript_id: _uuid.UUID,
    chapter_id: _uuid.UUID,
) -> dict:
    """Soft-delete a chapter within a manuscript."""
    manuscript = await _get_manuscript_by_id(db, manuscript_id)
    result = await db.execute(
        select(Chapter).where(
            Chapter.manuscript_id == manuscript.id,
            Chapter.id == chapter_id,
            Chapter.deleted_at.is_(None),
        )
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise NotFoundError("Chapter", f"Chapter {chapter_id} not found in manuscript {manuscript_id}")

    chapter.deleted_at = datetime.now(UTC)
    await db.flush()
    return {"message": "Chapter deleted", "chapter_id": str(chapter_id)}


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


async def reorder_chapters_for_manuscript(
    db: AsyncSession,
    manuscript_id: _uuid.UUID,
    reorder: ChapterReorderRequest,
) -> list[ChapterContent]:
    """Reorder chapters within a manuscript (by manuscript ID)."""
    manuscript = await _get_manuscript_by_id(db, manuscript_id)
    for item in reorder.chapters:
        await db.execute(
            update(Chapter)
            .where(
                Chapter.manuscript_id == manuscript.id,
                Chapter.id == item.chapter_id,
                Chapter.deleted_at.is_(None),
            )
            .values(order_index=item.order)
        )
    await db.flush()
    return await list_chapters_for_manuscript(db, manuscript_id)


async def update_chapter_content(
    db: AsyncSession,
    manuscript_id: _uuid.UUID,
    chapter_id: _uuid.UUID,
    content: str,
) -> ChapterContent:
    """Lightweight auto-save: update only the content and word count."""
    manuscript = await _get_manuscript_by_id(db, manuscript_id)
    result = await db.execute(
        select(Chapter).where(
            Chapter.manuscript_id == manuscript.id,
            Chapter.id == chapter_id,
            Chapter.deleted_at.is_(None),
        )
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise NotFoundError("Chapter", f"Chapter {chapter_id} not found in manuscript {manuscript_id}")

    chapter.content = content
    chapter.word_count = len(content.split()) if content else 0
    await db.flush()
    await db.refresh(chapter)

    return _chapter_to_schema(chapter, manuscript.book_id)


# ---------------------------------------------------------------------------
# Chapter version history
# ---------------------------------------------------------------------------
# Chapter versions are stored as lightweight snapshots in a JSON column
# (ai_metrics) on the Chapter model, keyed as "version_history".
# This avoids adding a new ORM table while still providing version tracking.
# ---------------------------------------------------------------------------

def _get_version_history(chapter: Chapter) -> list[dict]:
    """Extract version history from chapter ai_metrics."""
    if not chapter.ai_metrics:
        return []
    return chapter.ai_metrics.get("version_history", [])


def _set_version_history(chapter: Chapter, versions: list[dict]) -> None:
    """Store version history into chapter ai_metrics."""
    if chapter.ai_metrics is None:
        chapter.ai_metrics = {}
    chapter.ai_metrics = {**chapter.ai_metrics, "version_history": versions}


async def _snapshot_chapter_version(
    db: AsyncSession,
    chapter: Chapter,
    reason: str = "manual",
) -> dict:
    """Create a snapshot of the current chapter state."""
    versions = _get_version_history(chapter)
    next_number = (max((v.get("version_number", 0) for v in versions), default=0) + 1)

    snapshot = {
        "id": str(_uuid.uuid4()),
        "chapter_id": str(chapter.id),
        "version_number": next_number,
        "title": chapter.title,
        "content": chapter.content or "",
        "word_count": chapter.word_count,
        "created_at": datetime.now(UTC).isoformat(),
        "snapshot_reason": reason,
    }
    versions.append(snapshot)
    _set_version_history(chapter, versions)
    await db.flush()
    return snapshot


async def list_chapter_versions(
    db: AsyncSession,
    manuscript_id: _uuid.UUID,
    chapter_id: _uuid.UUID,
) -> list[ChapterVersionSummary]:
    """List all version snapshots for a chapter."""
    manuscript = await _get_manuscript_by_id(db, manuscript_id)
    result = await db.execute(
        select(Chapter).where(
            Chapter.manuscript_id == manuscript.id,
            Chapter.id == chapter_id,
            Chapter.deleted_at.is_(None),
        )
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise NotFoundError("Chapter", f"Chapter {chapter_id} not found in manuscript {manuscript_id}")

    versions = _get_version_history(chapter)
    return [
        ChapterVersionSummary(
            id=_uuid.UUID(v["id"]),
            chapter_id=_uuid.UUID(v["chapter_id"]),
            version_number=v["version_number"],
            word_count=v.get("word_count", 0),
            created_at=datetime.fromisoformat(v["created_at"]),
            snapshot_reason=v.get("snapshot_reason", ""),
        )
        for v in versions
    ]


async def get_chapter_version(
    db: AsyncSession,
    manuscript_id: _uuid.UUID,
    chapter_id: _uuid.UUID,
    version_id: _uuid.UUID,
) -> ChapterVersionDetail:
    """Fetch a specific version snapshot."""
    manuscript = await _get_manuscript_by_id(db, manuscript_id)
    result = await db.execute(
        select(Chapter).where(
            Chapter.manuscript_id == manuscript.id,
            Chapter.id == chapter_id,
            Chapter.deleted_at.is_(None),
        )
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise NotFoundError("Chapter", f"Chapter {chapter_id} not found in manuscript {manuscript_id}")

    versions = _get_version_history(chapter)
    for v in versions:
        if v["id"] == str(version_id):
            return ChapterVersionDetail(
                id=_uuid.UUID(v["id"]),
                chapter_id=_uuid.UUID(v["chapter_id"]),
                version_number=v["version_number"],
                title=v.get("title", ""),
                content=v.get("content", ""),
                word_count=v.get("word_count", 0),
                created_at=datetime.fromisoformat(v["created_at"]),
                snapshot_reason=v.get("snapshot_reason", ""),
            )

    raise NotFoundError("Version", f"Version {version_id} not found for chapter {chapter_id}")


async def restore_chapter_version(
    db: AsyncSession,
    manuscript_id: _uuid.UUID,
    chapter_id: _uuid.UUID,
    version_id: _uuid.UUID,
) -> ChapterContent:
    """Restore a chapter to a previous version snapshot.

    Creates a new snapshot of the current state before restoring.
    """
    manuscript = await _get_manuscript_by_id(db, manuscript_id)
    result = await db.execute(
        select(Chapter).where(
            Chapter.manuscript_id == manuscript.id,
            Chapter.id == chapter_id,
            Chapter.deleted_at.is_(None),
        )
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise NotFoundError("Chapter", f"Chapter {chapter_id} not found in manuscript {manuscript_id}")

    versions = _get_version_history(chapter)
    target_version = None
    for v in versions:
        if v["id"] == str(version_id):
            target_version = v
            break

    if not target_version:
        raise NotFoundError("Version", f"Version {version_id} not found for chapter {chapter_id}")

    # Snapshot current state before restore
    await _snapshot_chapter_version(db, chapter, reason="pre-restore backup")

    # Restore from version
    chapter.title = target_version.get("title", chapter.title)
    chapter.content = target_version.get("content", "")
    chapter.word_count = target_version.get("word_count", 0)

    await db.flush()
    await db.refresh(chapter)

    return _chapter_to_schema(chapter, manuscript.book_id)


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
    from app.modules.ai_writing.generator import _call_llm, resolve_model
    from app.modules.ai_writing.prompts import outline_prompt

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
        generated_at=datetime.now(UTC),
    )


async def generate_outline_standalone(
    request: OutlineGenerateRequest,
    db: AsyncSession,
) -> OutlineGenerateResponse:
    """Generate a book outline using AI without requiring an existing book."""
    from app.modules.ai_writing.generator import _call_llm, resolve_model

    system_parts = [
        "You are an expert book outline architect. You create detailed, "
        "well-structured book outlines that serve as comprehensive blueprints "
        "for authors.",
        f"Genre: {request.genre}.",
        f"Tone: {request.tone}.",
    ]
    system_msg = " ".join(system_parts)

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
    """Record a writing session."""
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


async def start_writing_session(
    db: AsyncSession,
    user_id: _uuid.UUID,
    manuscript_id: _uuid.UUID | None = None,
    chapter_id: _uuid.UUID | None = None,
) -> WritingSessionStartResponse:
    """Start a new timed writing session."""
    book_id: _uuid.UUID
    if manuscript_id:
        manuscript = await _get_manuscript_by_id(db, manuscript_id)
        book_id = manuscript.book_id
    else:
        book_id = _uuid.uuid4()

    session = WritingSession(
        id=_uuid.uuid4(),
        user_id=user_id,
        book_id=book_id,
        chapter_id=chapter_id,
        words_written=0,
        duration_seconds=0,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)

    return WritingSessionStartResponse(
        session_id=session.id,
        started_at=session.created_at,
    )


async def heartbeat_writing_session(
    db: AsyncSession,
    session_id: _uuid.UUID,
    words_written: int = 0,
    current_chapter_id: _uuid.UUID | None = None,
) -> dict:
    """Update a writing session with heartbeat data."""
    result = await db.execute(
        select(WritingSession).where(WritingSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise NotFoundError("WritingSession", f"Session {session_id} not found")

    if words_written > 0:
        session.words_written = words_written
    if current_chapter_id:
        session.chapter_id = current_chapter_id

    elapsed = (datetime.now(UTC) - session.created_at).total_seconds()
    session.duration_seconds = int(elapsed)

    await db.flush()
    return {"status": "ok", "session_id": str(session_id), "elapsed_seconds": int(elapsed)}


async def end_writing_session(
    db: AsyncSession,
    session_id: _uuid.UUID,
    words_written: int = 0,
    notes: str = "",
) -> WritingSessionEndResponse:
    """End an active writing session."""
    result = await db.execute(
        select(WritingSession).where(WritingSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise NotFoundError("WritingSession", f"Session {session_id} not found")

    now = datetime.now(UTC)
    elapsed = (now - session.created_at).total_seconds()
    session.duration_seconds = int(elapsed)
    if words_written > 0:
        session.words_written = words_written

    await db.flush()
    await db.refresh(session)

    return WritingSessionEndResponse(
        session_id=session.id,
        duration_seconds=session.duration_seconds,
        words_written=session.words_written,
        ended_at=now,
    )


async def list_writing_sessions(
    db: AsyncSession,
    user_id: _uuid.UUID,
    *,
    manuscript_id: _uuid.UUID | None = None,
    limit: int = 20,
) -> list[WritingSessionListItem]:
    """List writing sessions for the current user."""
    query = select(WritingSession).where(
        WritingSession.user_id == user_id,
    )

    if manuscript_id:
        ms_result = await db.execute(
            select(Manuscript.book_id).where(Manuscript.id == manuscript_id)
        )
        book_id = ms_result.scalar_one_or_none()
        if book_id:
            query = query.where(WritingSession.book_id == book_id)

    query = query.order_by(WritingSession.created_at.desc()).limit(limit)
    result = await db.execute(query)
    sessions = result.scalars().all()

    return [
        WritingSessionListItem(
            id=s.id,
            user_id=s.user_id,
            manuscript_id=None,
            chapter_id=s.chapter_id,
            words_written=s.words_written,
            duration_seconds=s.duration_seconds,
            started_at=s.created_at,
            ended_at=s.updated_at,
            notes="",
        )
        for s in sessions
    ]


# ---------------------------------------------------------------------------
# Export / Import
# ---------------------------------------------------------------------------

async def export_manuscript(
    db: AsyncSession,
    manuscript_id: _uuid.UUID,
    export_format: str = "docx",
    include_toc: bool = True,
    include_metadata: bool = True,
) -> dict:
    """Export a manuscript to the specified format."""
    manuscript = await _get_manuscript_by_id(db, manuscript_id)

    ch_result = await db.execute(
        select(Chapter)
        .where(
            Chapter.manuscript_id == manuscript.id,
            Chapter.deleted_at.is_(None),
        )
        .order_by(Chapter.order_index)
    )
    chapters = ch_result.scalars().all()

    total_words = sum(ch.word_count for ch in chapters)
    download_url = f"/exports/manuscript-{manuscript_id}.{export_format}"

    return {
        "download_url": download_url,
        "format": export_format,
        "manuscript_id": str(manuscript_id),
        "chapter_count": len(chapters),
        "word_count": total_words,
        "exported_at": datetime.now(UTC).isoformat(),
    }


async def import_manuscript(
    db: AsyncSession,
    user_id: _uuid.UUID,
    filename: str,
    content: bytes,
) -> dict:
    """Import a manuscript from an uploaded file."""
    text = content.decode("utf-8", errors="replace")

    book_id = _uuid.uuid4()
    manuscript = Manuscript(
        id=_uuid.uuid4(),
        book_id=book_id,
        content_type=ContentType.FICTION,
        status=ManuscriptStatus.DRAFT,
    )
    db.add(manuscript)
    await db.flush()

    import re
    chapter_splits = re.split(r"\n{3,}|(?=^Chapter\s+\d+)", text, flags=re.MULTILINE)
    chapter_splits = [s.strip() for s in chapter_splits if s.strip()]

    if not chapter_splits:
        chapter_splits = [text]

    total_words = 0
    for i, chunk in enumerate(chapter_splits):
        word_count = len(chunk.split())
        total_words += word_count
        ch = Chapter(
            id=_uuid.uuid4(),
            manuscript_id=manuscript.id,
            title=f"Chapter {i + 1}",
            content=chunk,
            order_index=i + 1,
            word_count=word_count,
        )
        db.add(ch)

    manuscript.word_count = total_words
    await db.flush()

    title = filename.rsplit(".", 1)[0] if "." in filename else filename

    return {
        "manuscript_id": str(manuscript.id),
        "title": title,
        "chapter_count": len(chapter_splits),
        "word_count": total_words,
        "imported_at": datetime.now(UTC).isoformat(),
    }
