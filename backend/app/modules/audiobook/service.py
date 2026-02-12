"""Business logic for audiobook projects and voices."""

from __future__ import annotations

import logging
import uuid as _uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.content import Chapter, Manuscript
from app.modules.audiobook.models import (
    AudiobookChapter,
    AudiobookProject,
    AudiobookVoice,
    VoiceType,
)
from app.modules.audiobook.schemas import (
    AudiobookChapterResponse,
    AudiobookProjectCreate,
    AudiobookProjectListItem,
    AudiobookProjectListResponse,
    AudiobookProjectResponse,
    AudiobookProjectUpdate,
    AudiobookVoiceCreate,
    AudiobookVoiceResponse,
    VoicePreviewResponse,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _project_to_response(project: AudiobookProject) -> AudiobookProjectResponse:
    """Map an AudiobookProject ORM instance to the API response schema."""
    chapters = [
        AudiobookChapterResponse(
            id=ch.id,
            project_id=ch.project_id,
            source_chapter_id=ch.source_chapter_id,
            title=ch.title,
            order_index=ch.order_index,
            status=ch.status.value,
            voice_id=ch.voice_id,
            audio_url=ch.audio_url,
            duration_seconds=ch.duration_seconds,
            word_count=ch.word_count,
            created_at=ch.created_at,
            updated_at=ch.updated_at,
        )
        for ch in (project.chapters or [])
    ]
    return AudiobookProjectResponse(
        id=project.id,
        org_id=project.org_id,
        book_id=project.book_id,
        title=project.title,
        status=project.status.value,
        narrator_voice_id=project.narrator_voice_id,
        settings=project.settings,
        total_duration_seconds=project.total_duration_seconds,
        created_by=project.created_by,
        chapters=chapters,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def _project_to_list_item(project: AudiobookProject) -> AudiobookProjectListItem:
    """Map an AudiobookProject to a list item (no chapter details)."""
    return AudiobookProjectListItem(
        id=project.id,
        org_id=project.org_id,
        book_id=project.book_id,
        title=project.title,
        status=project.status.value,
        narrator_voice_id=project.narrator_voice_id,
        total_duration_seconds=project.total_duration_seconds,
        chapter_count=len(project.chapters) if project.chapters else 0,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def _voice_to_response(voice: AudiobookVoice) -> AudiobookVoiceResponse:
    """Map an AudiobookVoice ORM instance to the API response schema."""
    return AudiobookVoiceResponse(
        id=voice.id,
        org_id=voice.org_id,
        name=voice.name,
        voice_type=voice.voice_type.value,
        provider=voice.provider.value,
        external_voice_id=voice.external_voice_id,
        preview_url=voice.preview_url,
        accent=voice.accent,
        language=voice.language,
        gender=voice.gender,
        settings=voice.settings,
        created_at=voice.created_at,
        updated_at=voice.updated_at,
    )


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------

async def create_project(
    db: AsyncSession,
    org_id: _uuid.UUID,
    user_id: _uuid.UUID,
    request: AudiobookProjectCreate,
) -> AudiobookProjectResponse:
    """Create a new audiobook project and auto-import chapters from the book's manuscript."""
    project = AudiobookProject(
        id=_uuid.uuid4(),
        org_id=org_id,
        book_id=request.book_id,
        title=request.title,
        narrator_voice_id=request.narrator_voice_id,
        settings=request.settings,
        created_by=user_id,
    )
    db.add(project)
    await db.flush()

    # Auto-import chapters from book's manuscript
    result = await db.execute(
        select(Manuscript).where(Manuscript.book_id == request.book_id)
    )
    manuscript = result.scalar_one_or_none()

    if manuscript:
        chapter_result = await db.execute(
            select(Chapter)
            .where(Chapter.manuscript_id == manuscript.id)
            .order_by(Chapter.order_index)
        )
        source_chapters = chapter_result.scalars().all()

        for ch in source_chapters:
            audiobook_chapter = AudiobookChapter(
                id=_uuid.uuid4(),
                org_id=org_id,
                project_id=project.id,
                source_chapter_id=ch.id,
                title=ch.title,
                order_index=ch.order_index,
                word_count=ch.word_count,
            )
            db.add(audiobook_chapter)

        await db.flush()

    await db.refresh(project)
    return _project_to_response(project)


async def get_project(
    db: AsyncSession,
    project_id: _uuid.UUID,
    org_id: _uuid.UUID,
) -> AudiobookProjectResponse:
    """Fetch an audiobook project with its chapters."""
    result = await db.execute(
        select(AudiobookProject).where(
            AudiobookProject.id == project_id,
            AudiobookProject.org_id == org_id,
            AudiobookProject.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("AudiobookProject")
    return _project_to_response(project)


async def list_projects(
    db: AsyncSession,
    org_id: _uuid.UUID,
    page: int,
    page_size: int,
    status_filter: str | None,
) -> AudiobookProjectListResponse:
    """List audiobook projects for an organization with pagination."""
    base_filter = [
        AudiobookProject.org_id == org_id,
        AudiobookProject.deleted_at.is_(None),
    ]
    if status_filter:
        base_filter.append(AudiobookProject.status == status_filter)

    # Total count
    count_q = select(func.count(AudiobookProject.id)).where(*base_filter)
    total = (await db.execute(count_q)).scalar_one()

    # Paginated results
    offset = (page - 1) * page_size
    data_q = (
        select(AudiobookProject)
        .where(*base_filter)
        .order_by(AudiobookProject.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(data_q)
    projects = result.scalars().all()

    return AudiobookProjectListResponse(
        items=[_project_to_list_item(p) for p in projects],
        total=total,
        page=page,
        page_size=page_size,
    )


async def update_project(
    db: AsyncSession,
    project_id: _uuid.UUID,
    org_id: _uuid.UUID,
    request: AudiobookProjectUpdate,
) -> AudiobookProjectResponse:
    """Update an audiobook project's settings."""
    result = await db.execute(
        select(AudiobookProject).where(
            AudiobookProject.id == project_id,
            AudiobookProject.org_id == org_id,
            AudiobookProject.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("AudiobookProject")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.flush()
    await db.refresh(project)
    return _project_to_response(project)


async def delete_project(
    db: AsyncSession,
    project_id: _uuid.UUID,
    org_id: _uuid.UUID,
) -> bool:
    """Soft-delete an audiobook project."""
    result = await db.execute(
        select(AudiobookProject).where(
            AudiobookProject.id == project_id,
            AudiobookProject.org_id == org_id,
            AudiobookProject.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        raise NotFoundError("AudiobookProject")

    from datetime import UTC, datetime

    project.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


# ---------------------------------------------------------------------------
# Voice CRUD
# ---------------------------------------------------------------------------

async def list_voices(
    db: AsyncSession,
    org_id: _uuid.UUID,
) -> list[AudiobookVoiceResponse]:
    """List available voices: system voices + org's custom voices."""
    result = await db.execute(
        select(AudiobookVoice).where(
            AudiobookVoice.deleted_at.is_(None),
            (AudiobookVoice.voice_type == VoiceType.SYSTEM)
            | (AudiobookVoice.org_id == org_id),
        ).order_by(AudiobookVoice.name)
    )
    voices = result.scalars().all()
    return [_voice_to_response(v) for v in voices]


async def create_voice_clone(
    db: AsyncSession,
    org_id: _uuid.UUID,
    request: AudiobookVoiceCreate,
) -> AudiobookVoiceResponse:
    """Create a custom voice profile for cloning.

    Actual voice cloning with the provider is deferred to a background
    task; this endpoint records the voice metadata.
    """
    voice = AudiobookVoice(
        id=_uuid.uuid4(),
        org_id=org_id,
        name=request.name,
        voice_type=VoiceType.CUSTOM,
        provider=request.provider,
        accent=request.accent,
        language=request.language,
        gender=request.gender,
        settings=request.settings,
    )
    db.add(voice)
    await db.flush()
    await db.refresh(voice)
    return _voice_to_response(voice)


async def preview_voice(
    db: AsyncSession,
    voice_id: _uuid.UUID,
    sample_text: str | None,
) -> VoicePreviewResponse:
    """Generate or return a voice preview.

    In production this would call the TTS provider; for now we return
    the stored preview_url or a placeholder.
    """
    result = await db.execute(
        select(AudiobookVoice).where(
            AudiobookVoice.id == voice_id,
            AudiobookVoice.deleted_at.is_(None),
        )
    )
    voice = result.scalar_one_or_none()
    if not voice:
        raise NotFoundError("AudiobookVoice")

    text = sample_text or "This is a sample preview of the selected voice."
    preview_url = voice.preview_url or ""

    return VoicePreviewResponse(
        voice_id=voice.id,
        preview_url=preview_url,
        sample_text=text,
    )


async def delete_voice(
    db: AsyncSession,
    voice_id: _uuid.UUID,
    org_id: _uuid.UUID,
) -> bool:
    """Soft-delete a custom voice (system voices cannot be deleted)."""
    result = await db.execute(
        select(AudiobookVoice).where(
            AudiobookVoice.id == voice_id,
            AudiobookVoice.org_id == org_id,
            AudiobookVoice.voice_type == VoiceType.CUSTOM,
            AudiobookVoice.deleted_at.is_(None),
        )
    )
    voice = result.scalar_one_or_none()
    if not voice:
        raise NotFoundError("AudiobookVoice")

    from datetime import UTC, datetime

    voice.deleted_at = datetime.now(UTC)
    await db.flush()
    return True
