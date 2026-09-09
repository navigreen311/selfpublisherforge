"""Business logic for the AI Writing Studio.

Handles manuscript CRUD, chapter management, version history, outline
generation, writing session tracking, auto-save, and readability analysis.

Uses the canonical ORM models from app.models.content rather than
defining module-local duplicates, to avoid table-definition conflicts
during integration.
"""

from __future__ import annotations

import json
import logging
import os
import uuid as _uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, NotFoundError

logger = logging.getLogger(__name__)

WORD_COUNT_MULTIPLIER = float(os.environ.get("AI_WORD_COUNT_MULTIPLIER", "0.5"))

# Auto-save versioning thresholds
_VERSION_TIME_THRESHOLD = timedelta(minutes=5)
_VERSION_WORD_CHANGE_THRESHOLD = 100

# ---------------------------------------------------------------------------
# Canonical ORM models -- imported from the shared models registry so that
# SQLAlchemy sees a single table definition for each table name.
# ---------------------------------------------------------------------------
from app.models.content import (
    Chapter,
    ChapterVersion,
    ContentType,
    Manuscript,
    ManuscriptStatus,
    WritingSession,
)
from app.modules.ai_writing.readability import (
    analyze_readability,
    compute_readability,
)
from app.modules.ai_writing.schemas import (
    ChapterContent,
    ChapterCreate,
    ChapterOutline,
    ChapterReorderRequest,
    ChapterUpdate,
    ManuscriptAnalysis,
    ManuscriptResponse,
    OutlineChapter,
    OutlineGenerateRequest,
    OutlineGenerateResponse,
    OutlineRequest,
    OutlineResponse,
    ReadabilityScore,
    WritingSessionCreate,
    WritingSessionRecord,
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


async def _require_manuscript(db: AsyncSession, manuscript_id: _uuid.UUID) -> Manuscript:
    """Load a manuscript by ID or raise 404."""
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


async def _require_chapter(db: AsyncSession, chapter_id: _uuid.UUID) -> Chapter:
    """Load a chapter by ID or raise 404."""
    result = await db.execute(
        select(Chapter).where(
            Chapter.id == chapter_id,
            Chapter.deleted_at.is_(None),
        )
    )
    chapter = result.scalar_one_or_none()
    if not chapter:
        raise NotFoundError("Chapter", f"Chapter {chapter_id} not found")
    return chapter


# ---------------------------------------------------------------------------
# Manuscript CRUD (enhanced)
# ---------------------------------------------------------------------------


async def list_manuscripts(
    db: AsyncSession,
    org_id: _uuid.UUID,
    status: str | None = None,
    sort: str = "recent",
    search: str | None = None,
) -> list[dict]:
    """List manuscripts for an organization with optional filters.

    Args:
        db: Async database session.
        org_id: Organization ID (tenant scope).
        status: Optional manuscript status filter (draft, revision, final, archived).
        sort: Sort order - 'recent' (default), 'oldest', 'title', 'word_count'.
        search: Optional search term for manuscript/book title.

    Returns:
        List of manuscript dicts with chapter metadata.
    """
    from app.models.project import Book

    stmt = (
        select(Manuscript, Book.title.label("book_title"))
        .join(Book, Manuscript.book_id == Book.id)
        .where(Manuscript.deleted_at.is_(None))
    )

    # Filter by org: books belong to projects which belong to orgs
    from app.models.project import Project

    stmt = stmt.join(Project, Book.project_id == Project.id).where(Project.org_id == org_id)

    if status:
        try:
            ms_status = ManuscriptStatus(status)
            stmt = stmt.where(Manuscript.status == ms_status)
        except ValueError:
            pass  # ignore invalid status

    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Book.title.ilike(search_pattern),
                Manuscript.content.ilike(search_pattern),
            )
        )

    if sort == "oldest":
        stmt = stmt.order_by(Manuscript.created_at.asc())
    elif sort == "title":
        stmt = stmt.order_by(Book.title.asc())
    elif sort == "word_count":
        stmt = stmt.order_by(Manuscript.word_count.desc())
    else:  # 'recent' (default)
        stmt = stmt.order_by(Manuscript.updated_at.desc())

    result = await db.execute(stmt)
    rows = result.all()

    manuscripts = []
    for manuscript, book_title in rows:
        # Get chapter count
        ch_count_result = await db.execute(
            select(func.count(Chapter.id)).where(
                Chapter.manuscript_id == manuscript.id,
                Chapter.deleted_at.is_(None),
            )
        )
        chapter_count = ch_count_result.scalar() or 0

        manuscripts.append(
            {
                "id": manuscript.id,
                "book_id": manuscript.book_id,
                "title": book_title or "",
                "status": manuscript.status.value if manuscript.status else "draft",
                "content_type": manuscript.content_type.value if manuscript.content_type else "fiction",
                "word_count": manuscript.word_count,
                "chapter_count": chapter_count,
                "created_at": manuscript.created_at,
                "updated_at": manuscript.updated_at,
            }
        )

    return manuscripts


async def create_manuscript(
    db: AsyncSession,
    org_id: _uuid.UUID,
    user_id: _uuid.UUID,
    data: dict,
) -> dict:
    """Create a new manuscript with an optional initial chapter.

    Args:
        db: Async database session.
        org_id: Organization ID (for authorization context).
        user_id: Creating user's ID.
        data: Dict with keys: book_id, content_type (optional), title (optional).

    Returns:
        Dict with manuscript details and initial chapter.
    """
    book_id = data.get("book_id")
    if not book_id:
        raise AppException(
            status_code=422,
            code="VALIDATION_ERROR",
            message="book_id is required",
        )

    content_type_str = data.get("content_type", "fiction")
    try:
        content_type = ContentType(content_type_str)
    except ValueError:
        content_type = ContentType.FICTION

    manuscript = Manuscript(
        id=_uuid.uuid4(),
        book_id=_uuid.UUID(str(book_id)) if not isinstance(book_id, _uuid.UUID) else book_id,
        content_type=content_type,
        status=ManuscriptStatus.DRAFT,
        word_count=0,
    )
    db.add(manuscript)
    await db.flush()

    # Create initial chapter
    initial_title = data.get("initial_chapter_title", "Chapter 1")
    chapter = Chapter(
        id=_uuid.uuid4(),
        manuscript_id=manuscript.id,
        title=initial_title,
        content="",
        order_index=1,
        word_count=0,
    )
    db.add(chapter)
    await db.flush()
    await db.refresh(manuscript)
    await db.refresh(chapter)

    return {
        "id": manuscript.id,
        "book_id": manuscript.book_id,
        "status": manuscript.status.value,
        "content_type": manuscript.content_type.value,
        "word_count": 0,
        "created_at": manuscript.created_at,
        "updated_at": manuscript.updated_at,
        "chapters": [
            {
                "id": chapter.id,
                "title": chapter.title,
                "order": chapter.order_index,
                "word_count": 0,
            }
        ],
    }


async def get_manuscript(db: AsyncSession, book_id: _uuid.UUID) -> ManuscriptResponse:
    """Fetch the full manuscript with all chapters."""
    manuscript = await _get_or_create_manuscript(db, book_id)
    result = await db.execute(
        select(Chapter)
        .where(
            Chapter.manuscript_id == manuscript.id,
            Chapter.deleted_at.is_(None),
        )
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


async def get_manuscript_by_id(db: AsyncSession, manuscript_id: _uuid.UUID) -> dict:
    """Fetch a manuscript by its ID with chapters metadata.

    Returns:
        Dict with manuscript details and chapters list.
    """
    manuscript = await _require_manuscript(db, manuscript_id)

    result = await db.execute(
        select(Chapter)
        .where(
            Chapter.manuscript_id == manuscript.id,
            Chapter.deleted_at.is_(None),
        )
        .order_by(Chapter.order_index)
    )
    chapters = result.scalars().all()
    total_words = sum(ch.word_count for ch in chapters)

    return {
        "id": manuscript.id,
        "book_id": manuscript.book_id,
        "status": manuscript.status.value if manuscript.status else "draft",
        "content_type": manuscript.content_type.value if manuscript.content_type else "fiction",
        "word_count": total_words,
        "created_at": manuscript.created_at,
        "updated_at": manuscript.updated_at,
        "chapters": [
            {
                "id": ch.id,
                "title": ch.title,
                "order": ch.order_index,
                "word_count": ch.word_count,
                "status": ch.status.value if ch.status else "outline",
                "created_at": ch.created_at,
                "updated_at": ch.updated_at,
            }
            for ch in chapters
        ],
    }


async def update_manuscript(
    db: AsyncSession,
    manuscript_id: _uuid.UUID,
    data: dict,
) -> dict:
    """Partial update of manuscript metadata.

    Supported fields: status, content_type.
    """
    manuscript = await _require_manuscript(db, manuscript_id)

    if "status" in data:
        try:
            manuscript.status = ManuscriptStatus(data["status"])
        except ValueError:
            raise AppException(
                status_code=422,
                code="VALIDATION_ERROR",
                message=f"Invalid status: {data['status']}",
            ) from None

    if "content_type" in data:
        try:
            manuscript.content_type = ContentType(data["content_type"])
        except ValueError:
            raise AppException(
                status_code=422,
                code="VALIDATION_ERROR",
                message=f"Invalid content_type: {data['content_type']}",
            ) from None

    await db.flush()
    await db.refresh(manuscript)

    return {
        "id": manuscript.id,
        "book_id": manuscript.book_id,
        "status": manuscript.status.value,
        "content_type": manuscript.content_type.value,
        "word_count": manuscript.word_count,
        "updated_at": manuscript.updated_at,
    }


async def delete_manuscript(db: AsyncSession, manuscript_id: _uuid.UUID) -> dict:
    """Soft delete a manuscript by setting deleted_at."""
    manuscript = await _require_manuscript(db, manuscript_id)
    now = datetime.now(UTC)
    manuscript.deleted_at = now

    # Also soft-delete all chapters
    await db.execute(
        update(Chapter)
        .where(
            Chapter.manuscript_id == manuscript.id,
            Chapter.deleted_at.is_(None),
        )
        .values(deleted_at=now)
    )

    await db.flush()
    return {"id": manuscript.id, "deleted_at": now.isoformat()}


async def duplicate_manuscript(db: AsyncSession, manuscript_id: _uuid.UUID) -> dict:
    """Deep copy a manuscript with all its chapters.

    Creates a new manuscript linked to the same book, copies all
    non-deleted chapters with their content and order.
    """
    source = await _require_manuscript(db, manuscript_id)

    new_manuscript = Manuscript(
        id=_uuid.uuid4(),
        book_id=source.book_id,
        content_type=source.content_type,
        status=ManuscriptStatus.DRAFT,
        word_count=source.word_count,
    )
    db.add(new_manuscript)
    await db.flush()

    # Copy chapters
    result = await db.execute(
        select(Chapter)
        .where(
            Chapter.manuscript_id == source.id,
            Chapter.deleted_at.is_(None),
        )
        .order_by(Chapter.order_index)
    )
    source_chapters = result.scalars().all()

    new_chapters = []
    for ch in source_chapters:
        new_ch = Chapter(
            id=_uuid.uuid4(),
            manuscript_id=new_manuscript.id,
            title=ch.title,
            content=ch.content,
            order_index=ch.order_index,
            word_count=ch.word_count,
            status=ch.status,
        )
        db.add(new_ch)
        new_chapters.append(new_ch)

    await db.flush()
    await db.refresh(new_manuscript)

    return {
        "id": new_manuscript.id,
        "book_id": new_manuscript.book_id,
        "status": new_manuscript.status.value,
        "source_manuscript_id": source.id,
        "chapter_count": len(new_chapters),
        "created_at": new_manuscript.created_at,
    }


async def archive_manuscript(db: AsyncSession, manuscript_id: _uuid.UUID) -> dict:
    """Set a manuscript's status to 'archived'."""
    manuscript = await _require_manuscript(db, manuscript_id)
    manuscript.status = ManuscriptStatus.ARCHIVED
    await db.flush()
    await db.refresh(manuscript)

    return {
        "id": manuscript.id,
        "status": manuscript.status.value,
        "updated_at": manuscript.updated_at,
    }


# ---------------------------------------------------------------------------
# Manuscript / chapter CRUD (existing)
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


async def list_chapters(db: AsyncSession, book_id: _uuid.UUID) -> list[ChapterContent]:
    """List all chapters for a book, ordered."""
    manuscript = await _get_or_create_manuscript(db, book_id)
    result = await db.execute(
        select(Chapter)
        .where(
            Chapter.manuscript_id == manuscript.id,
            Chapter.deleted_at.is_(None),
        )
        .order_by(Chapter.order_index)
    )
    chapters = result.scalars().all()
    return [_chapter_to_schema(ch, book_id) for ch in chapters]


async def get_chapter(db: AsyncSession, book_id: _uuid.UUID, chapter_id: _uuid.UUID) -> ChapterContent:
    """Fetch a single chapter."""
    manuscript = await _get_or_create_manuscript(db, book_id)
    result = await db.execute(
        select(Chapter).where(
            Chapter.manuscript_id == manuscript.id,
            Chapter.id == chapter_id,
            Chapter.deleted_at.is_(None),
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


async def create_chapter(db: AsyncSession, book_id: _uuid.UUID, data: ChapterCreate) -> ChapterContent:
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
            Chapter.deleted_at.is_(None),
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
# Chapter Version History
# ---------------------------------------------------------------------------


async def create_version_snapshot(
    db: AsyncSession,
    chapter_id: _uuid.UUID,
    content: str,
    word_count: int,
    user_id: _uuid.UUID | None = None,
) -> dict:
    """Create a version snapshot of a chapter's content.

    Args:
        db: Async database session.
        chapter_id: Chapter to snapshot.
        content: Content at time of snapshot.
        word_count: Word count at time of snapshot.
        user_id: Optional user who triggered the snapshot.

    Returns:
        Dict with version details.
    """
    # Verify chapter exists
    await _require_chapter(db, chapter_id)

    version = ChapterVersion(
        id=_uuid.uuid4(),
        chapter_id=chapter_id,
        content=content,
        word_count=word_count,
        snapshot_by=user_id,
    )
    db.add(version)
    await db.flush()
    await db.refresh(version)

    return {
        "id": version.id,
        "chapter_id": version.chapter_id,
        "word_count": version.word_count,
        "snapshot_by": version.snapshot_by,
        "created_at": version.created_at,
    }


async def list_versions(db: AsyncSession, chapter_id: _uuid.UUID) -> list[dict]:
    """List version snapshots for a chapter, newest first, limit 50.

    Returns:
        List of version dicts (without full content for performance).
    """
    result = await db.execute(
        select(ChapterVersion)
        .where(
            ChapterVersion.chapter_id == chapter_id,
            ChapterVersion.deleted_at.is_(None),
        )
        .order_by(ChapterVersion.created_at.desc())
        .limit(50)
    )
    versions = result.scalars().all()

    return [
        {
            "id": v.id,
            "chapter_id": v.chapter_id,
            "word_count": v.word_count,
            "snapshot_by": v.snapshot_by,
            "created_at": v.created_at,
        }
        for v in versions
    ]


async def get_version(db: AsyncSession, version_id: _uuid.UUID) -> dict:
    """Get a full version snapshot including content.

    Returns:
        Dict with version details and content.

    Raises:
        NotFoundError: If version not found.
    """
    result = await db.execute(
        select(ChapterVersion).where(
            ChapterVersion.id == version_id,
            ChapterVersion.deleted_at.is_(None),
        )
    )
    version = result.scalar_one_or_none()
    if not version:
        raise NotFoundError("ChapterVersion", f"Version {version_id} not found")

    return {
        "id": version.id,
        "chapter_id": version.chapter_id,
        "content": version.content,
        "word_count": version.word_count,
        "snapshot_by": version.snapshot_by,
        "created_at": version.created_at,
    }


async def restore_version(
    db: AsyncSession,
    chapter_id: _uuid.UUID,
    version_id: _uuid.UUID,
) -> dict:
    """Restore a chapter to a previous version.

    Workflow:
        1. Snapshot current content as a new version (so nothing is lost).
        2. Replace chapter content with the target version's content.

    Returns:
        Dict with restored chapter details and new version ID.
    """
    chapter = await _require_chapter(db, chapter_id)

    # Load the target version
    result = await db.execute(
        select(ChapterVersion).where(
            ChapterVersion.id == version_id,
            ChapterVersion.chapter_id == chapter_id,
            ChapterVersion.deleted_at.is_(None),
        )
    )
    target_version = result.scalar_one_or_none()
    if not target_version:
        raise NotFoundError(
            "ChapterVersion",
            f"Version {version_id} not found for chapter {chapter_id}",
        )

    # Snapshot current content before overwriting
    current_snapshot = ChapterVersion(
        id=_uuid.uuid4(),
        chapter_id=chapter_id,
        content=chapter.content,
        word_count=chapter.word_count,
    )
    db.add(current_snapshot)

    # Restore content from target version
    chapter.content = target_version.content
    chapter.word_count = target_version.word_count

    await db.flush()
    await db.refresh(chapter)
    await db.refresh(current_snapshot)

    return {
        "chapter_id": chapter.id,
        "restored_from_version_id": version_id,
        "backup_version_id": current_snapshot.id,
        "word_count": chapter.word_count,
        "updated_at": chapter.updated_at,
    }


async def prune_old_versions(
    db: AsyncSession,
    chapter_id: _uuid.UUID,
    keep: int = 50,
) -> dict:
    """Remove oldest version snapshots beyond the keep limit.

    Args:
        db: Async database session.
        chapter_id: Chapter whose versions to prune.
        keep: Number of most recent versions to keep.

    Returns:
        Dict with pruned count.
    """
    # Find IDs to keep (most recent N)
    keep_subq = (
        select(ChapterVersion.id)
        .where(
            ChapterVersion.chapter_id == chapter_id,
            ChapterVersion.deleted_at.is_(None),
        )
        .order_by(ChapterVersion.created_at.desc())
        .limit(keep)
        .subquery()
    )

    # Count versions to prune
    count_result = await db.execute(
        select(func.count(ChapterVersion.id)).where(
            ChapterVersion.chapter_id == chapter_id,
            ChapterVersion.deleted_at.is_(None),
            ChapterVersion.id.not_in(select(keep_subq.c.id)),
        )
    )
    prune_count = count_result.scalar() or 0

    if prune_count > 0:
        # Soft-delete old versions
        now = datetime.now(UTC)
        await db.execute(
            update(ChapterVersion)
            .where(
                ChapterVersion.chapter_id == chapter_id,
                ChapterVersion.deleted_at.is_(None),
                ChapterVersion.id.not_in(select(keep_subq.c.id)),
            )
            .values(deleted_at=now)
        )
        await db.flush()

    return {"chapter_id": chapter_id, "pruned": prune_count, "kept": keep}


# ---------------------------------------------------------------------------
# Auto-save with versioning
# ---------------------------------------------------------------------------


async def save_chapter_content(
    db: AsyncSession,
    chapter_id: _uuid.UUID,
    content: str,
    word_count: int,
    user_id: _uuid.UUID | None = None,
) -> dict:
    """Save chapter content with intelligent auto-versioning.

    Creates a version snapshot if:
      - More than 5 minutes since last version, OR
      - Word count changed by more than 100 words since last version.

    Args:
        db: Async database session.
        chapter_id: Chapter to save.
        content: New content.
        word_count: New word count.
        user_id: User performing the save.

    Returns:
        Dict with save details and optional version info.
    """
    chapter = await _require_chapter(db, chapter_id)

    # Check if we should create a version snapshot
    should_snapshot = False
    now = datetime.now(UTC)

    # Find the most recent version
    last_version_result = await db.execute(
        select(ChapterVersion)
        .where(
            ChapterVersion.chapter_id == chapter_id,
            ChapterVersion.deleted_at.is_(None),
        )
        .order_by(ChapterVersion.created_at.desc())
        .limit(1)
    )
    last_version = last_version_result.scalar_one_or_none()

    if last_version is None:
        # No versions yet -- always snapshot
        should_snapshot = True
    else:
        time_since_last = (
            now - last_version.created_at.replace(tzinfo=UTC)
            if last_version.created_at.tzinfo is None
            else now - last_version.created_at
        )
        word_delta = abs(word_count - (last_version.word_count or 0))

        if time_since_last >= _VERSION_TIME_THRESHOLD or word_delta >= _VERSION_WORD_CHANGE_THRESHOLD:
            should_snapshot = True

    version_id = None
    if should_snapshot:
        # Snapshot the CURRENT content before replacing
        snapshot = await create_version_snapshot(db, chapter_id, chapter.content or "", chapter.word_count, user_id)
        version_id = snapshot["id"]

    # Update chapter content
    chapter.content = content
    chapter.word_count = word_count

    await db.flush()
    await db.refresh(chapter)

    return {
        "chapter_id": chapter.id,
        "word_count": chapter.word_count,
        "updated_at": chapter.updated_at,
        "version_created": version_id is not None,
        "version_id": version_id,
    }


# ---------------------------------------------------------------------------
# Writing Sessions (enhanced)
# ---------------------------------------------------------------------------


async def start_session(
    db: AsyncSession,
    user_id: _uuid.UUID,
    org_id: _uuid.UUID,
    manuscript_id: _uuid.UUID,
    chapter_id: _uuid.UUID | None = None,
) -> dict:
    """Start a new writing session.

    Args:
        db: Async database session.
        user_id: User starting the session.
        org_id: Organization ID.
        manuscript_id: Manuscript being worked on.
        chapter_id: Optional specific chapter.

    Returns:
        Dict with session details.
    """
    # Resolve book_id from manuscript
    manuscript = await _require_manuscript(db, manuscript_id)

    session = WritingSession(
        id=_uuid.uuid4(),
        user_id=user_id,
        book_id=manuscript.book_id,
        chapter_id=chapter_id,
        words_written=0,
        duration_seconds=0,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)

    return {
        "id": session.id,
        "user_id": session.user_id,
        "book_id": session.book_id,
        "manuscript_id": manuscript_id,
        "chapter_id": session.chapter_id,
        "words_written": session.words_written,
        "started_at": session.created_at,
    }


async def heartbeat_session(
    db: AsyncSession,
    session_id: _uuid.UUID,
    words_written: int,
) -> dict:
    """Update a writing session's word count (heartbeat).

    Called periodically by the frontend to track progress.

    Args:
        db: Async database session.
        session_id: Session to update.
        words_written: Total words written so far in this session.

    Returns:
        Dict with updated session details.
    """
    result = await db.execute(select(WritingSession).where(WritingSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise NotFoundError("WritingSession", f"Session {session_id} not found")

    session.words_written = words_written
    await db.flush()
    await db.refresh(session)

    return {
        "id": session.id,
        "words_written": session.words_written,
        "updated_at": session.updated_at,
    }


async def end_session(
    db: AsyncSession,
    session_id: _uuid.UUID,
    words_written: int,
    duration: int,
) -> dict:
    """End a writing session, recording final word count and duration.

    Args:
        db: Async database session.
        session_id: Session to end.
        words_written: Final words written count.
        duration: Duration in seconds.

    Returns:
        Dict with completed session details.
    """
    result = await db.execute(select(WritingSession).where(WritingSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise NotFoundError("WritingSession", f"Session {session_id} not found")

    session.words_written = words_written
    session.duration_seconds = duration
    await db.flush()
    await db.refresh(session)

    return {
        "id": session.id,
        "user_id": session.user_id,
        "book_id": session.book_id,
        "chapter_id": session.chapter_id,
        "words_written": session.words_written,
        "duration_seconds": session.duration_seconds,
        "duration_minutes": session.duration_seconds // 60,
        "started_at": session.created_at,
        "ended_at": session.updated_at,
    }


async def list_sessions(
    db: AsyncSession,
    manuscript_id: _uuid.UUID | None = None,
    user_id: _uuid.UUID | None = None,
    limit: int = 20,
) -> list[dict]:
    """List writing sessions with optional filters.

    Includes book title and chapter title for display purposes.

    Args:
        db: Async database session.
        manuscript_id: Optional filter by manuscript (via book_id).
        user_id: Optional filter by user.
        limit: Maximum number of sessions to return.

    Returns:
        List of session dicts with book/chapter titles.
    """
    from app.models.project import Book

    stmt = select(
        WritingSession,
        Book.title.label("book_title"),
    ).join(Book, WritingSession.book_id == Book.id)

    if manuscript_id:
        # Resolve book_id from manuscript
        ms_result = await db.execute(select(Manuscript.book_id).where(Manuscript.id == manuscript_id))
        book_id = ms_result.scalar_one_or_none()
        if book_id:
            stmt = stmt.where(WritingSession.book_id == book_id)

    if user_id:
        stmt = stmt.where(WritingSession.user_id == user_id)

    stmt = stmt.order_by(WritingSession.created_at.desc()).limit(limit)

    result = await db.execute(stmt)
    rows = result.all()

    sessions = []
    for session, book_title in rows:
        # Resolve chapter title if applicable
        chapter_title = None
        if session.chapter_id:
            ch_result = await db.execute(select(Chapter.title).where(Chapter.id == session.chapter_id))
            chapter_title = ch_result.scalar_one_or_none()

        sessions.append(
            {
                "id": session.id,
                "user_id": session.user_id,
                "book_id": session.book_id,
                "book_title": book_title or "",
                "chapter_id": session.chapter_id,
                "chapter_title": chapter_title,
                "words_written": session.words_written,
                "duration_seconds": session.duration_seconds,
                "duration_minutes": session.duration_seconds // 60,
                "started_at": session.created_at,
            }
        )

    return sessions


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


# ---------------------------------------------------------------------------
# Readability / analysis (enhanced)
# ---------------------------------------------------------------------------


async def get_readability_score(db: AsyncSession, book_id: _uuid.UUID) -> ReadabilityScore:
    """Compute readability metrics for the full manuscript."""
    manuscript = await _get_or_create_manuscript(db, book_id)
    result = await db.execute(
        select(Chapter.content)
        .where(
            Chapter.manuscript_id == manuscript.id,
            Chapter.deleted_at.is_(None),
        )
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


async def get_computed_readability(text: str) -> dict:
    """Compute enhanced readability metrics for the Writing Studio.

    Returns dict with: grade_level, flesch_ease, flesch_label,
    passive_voice_pct, avg_sentence_length, word_count, suggestions[].
    """
    result = compute_readability(text)
    return {
        "grade_level": result.grade_level,
        "flesch_ease": result.flesch_ease,
        "flesch_label": result.flesch_label,
        "passive_voice_pct": result.passive_voice_pct,
        "avg_sentence_length": result.avg_sentence_length,
        "word_count": result.word_count,
        "suggestions": list(result.suggestions),
    }


async def analyze_manuscript(db: AsyncSession, book_id: _uuid.UUID) -> ManuscriptAnalysis:
    """Full manuscript analysis including readability, pacing, word count."""
    readability = await get_readability_score(db, book_id)

    manuscript = await _get_or_create_manuscript(db, book_id)
    result = await db.execute(
        select(Chapter)
        .where(
            Chapter.manuscript_id == manuscript.id,
            Chapter.deleted_at.is_(None),
        )
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
                pacing_notes.append(f"Chapter '{ch.title}' (#{ch.order_index}) is significantly shorter than average.")
            elif ch.word_count > avg_chapter_wc * 1.5:
                pacing_notes.append(f"Chapter '{ch.title}' (#{ch.order_index}) is significantly longer than average.")

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
