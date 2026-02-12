"""Service layer for audiobook project CRUD operations."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audiobook import AudiobookChapter, AudiobookProject
from app.models.content import Chapter, Manuscript
from app.models.project import Book, Project

logger = logging.getLogger(__name__)


# ── Create ────────────────────────────────────────────────────────────────


async def create_project(
    db: AsyncSession,
    org_id: uuid.UUID,
    data: dict,
) -> AudiobookProject:
    """Create a new audiobook project linked to a book.

    - Validate book_id belongs to org
    - Auto-populate chapters from the book's manuscript chapters
    - Set initial status to 'draft'
    - Calculate estimated word count from chapters
    """
    book_id = data["book_id"]

    # Validate book belongs to org via Project
    book_stmt = (
        select(Book)
        .join(Project, Book.project_id == Project.id)
        .where(
            Book.id == book_id,
            Project.org_id == org_id,
            Book.deleted_at.is_(None),
            Project.deleted_at.is_(None),
        )
    )
    result = await db.execute(book_stmt)
    book = result.scalar_one_or_none()
    if not book:
        raise ValueError(f"Book {book_id} not found or does not belong to this org")

    # Create the project
    project = AudiobookProject(
        org_id=org_id,
        book_id=book_id,
        title=data.get("title") or book.title,
        status="draft",
        narrator_voice_id=data.get("narrator_voice_id"),
        character_voices=data.get("character_voices", {}),
        narration_style=data.get("narration_style", {}),
        output_format=data.get("output_format", "mp3"),
        sample_rate=data.get("sample_rate", 44100),
        bit_rate=data.get("bit_rate", 192),
        channels=data.get("channels", 1),
        target_platform=data.get("target_platform", "acx"),
        settings=data.get("settings", {}),
        created_by=data.get("created_by"),
    )
    db.add(project)
    await db.flush()

    # Auto-populate chapters from the book's manuscript chapters
    manuscript_stmt = (
        select(Manuscript)
        .where(
            Manuscript.book_id == book_id,
            Manuscript.deleted_at.is_(None),
        )
        .order_by(Manuscript.created_at.desc())
        .limit(1)
    )
    ms_result = await db.execute(manuscript_stmt)
    manuscript = ms_result.scalar_one_or_none()

    total_word_count = 0
    chapter_count = 0

    if manuscript:
        chapter_stmt = (
            select(Chapter)
            .where(
                Chapter.manuscript_id == manuscript.id,
                Chapter.deleted_at.is_(None),
            )
            .order_by(Chapter.order_index)
        )
        ch_result = await db.execute(chapter_stmt)
        chapters = list(ch_result.scalars().all())

        for ch in chapters:
            word_count = ch.word_count or (len(ch.content.split()) if ch.content else 0)
            ab_chapter = AudiobookChapter(
                audiobook_project_id=project.id,
                chapter_id=ch.id,
                chapter_number=ch.order_index + 1,
                chapter_title=ch.title,
                source_text=ch.content or "",
                word_count=word_count,
                status="pending",
            )
            db.add(ab_chapter)
            total_word_count += word_count
            chapter_count += 1

    project.total_chapters = chapter_count
    project.metadata_ = {
        **(project.metadata_ or {}),
        "estimated_word_count": total_word_count,
    }

    await db.commit()
    await db.refresh(project)
    return project


# ── List ──────────────────────────────────────────────────────────────────


async def list_projects(
    db: AsyncSession,
    org_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
) -> dict:
    """List audiobook projects for an org with pagination.

    - Filter by org_id, optional status filter
    - Exclude soft-deleted
    - Order by created_at desc
    - Return {items: [...], total: int, page: int, per_page: int}
    """
    base = select(AudiobookProject).where(
        AudiobookProject.org_id == org_id,
        AudiobookProject.deleted_at.is_(None),
    )
    if status:
        base = base.where(AudiobookProject.status == status)

    # Total count
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Paginated items
    offset = (page - 1) * per_page
    items_stmt = base.order_by(AudiobookProject.created_at.desc()).offset(offset).limit(per_page)
    result = await db.execute(items_stmt)
    items = list(result.scalars().all())

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


# ── Get ───────────────────────────────────────────────────────────────────


async def get_project(
    db: AsyncSession,
    project_id: uuid.UUID,
    org_id: uuid.UUID,
) -> AudiobookProject | None:
    """Get a single project with its chapters loaded.

    - Use selectinload for chapters relationship
    - Filter by org_id for tenant isolation
    """
    stmt = (
        select(AudiobookProject)
        .options(selectinload(AudiobookProject.chapters))
        .where(
            AudiobookProject.id == project_id,
            AudiobookProject.org_id == org_id,
            AudiobookProject.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# ── Update ────────────────────────────────────────────────────────────────

_UPDATABLE_FIELDS = frozenset(
    {
        "title",
        "narrator_voice_id",
        "character_voices",
        "narration_style",
        "output_format",
        "sample_rate",
        "bit_rate",
        "channels",
        "target_platform",
        "settings",
    }
)


async def update_project(
    db: AsyncSession,
    project_id: uuid.UUID,
    org_id: uuid.UUID,
    data: dict,
) -> AudiobookProject | None:
    """Update project settings.

    - Only update fields that are provided (partial update)
    - Can update: title, narrator_voice_id, character_voices, narration_style,
      output_format, sample_rate, bit_rate, channels, target_platform, settings
    """
    stmt = select(AudiobookProject).where(
        AudiobookProject.id == project_id,
        AudiobookProject.org_id == org_id,
        AudiobookProject.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        return None

    for field, value in data.items():
        if field in _UPDATABLE_FIELDS:
            setattr(project, field, value)

    await db.commit()
    await db.refresh(project)
    return project


# ── Delete ────────────────────────────────────────────────────────────────


async def delete_project(
    db: AsyncSession,
    project_id: uuid.UUID,
    org_id: uuid.UUID,
) -> bool:
    """Soft-delete a project.

    - Set deleted_at timestamp
    - Return True if found and deleted, False if not found
    """
    stmt = select(AudiobookProject).where(
        AudiobookProject.id == project_id,
        AudiobookProject.org_id == org_id,
        AudiobookProject.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        return False

    project.deleted_at = datetime.now(UTC)
    await db.commit()
    return True
