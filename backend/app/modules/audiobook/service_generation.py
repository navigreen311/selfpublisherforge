"""Business logic for audiobook chapter audio generation, regeneration, and approval."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException, ForbiddenError, NotFoundError
from app.modules.audiobook.schemas_generation import (
    ChapterApproveRequest,
    ChapterAudioFileResponse,
    ChapterAudioResponse,
    GenerateAllRequest,
    GenerateAllResponse,
    GenerateChapterRequest,
    GenerationJobResponse,
    RegenerateSegmentRequest,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lazy model access (avoids circular imports & N806 lint violations)
# ---------------------------------------------------------------------------


def _project_model():
    from app.models.audiobook import AudiobookProject

    return AudiobookProject


def _chapter_model():
    from app.models.audiobook import AudiobookChapter

    return AudiobookChapter


def _job_model():
    from app.models.audiobook import AudiobookGenerationJob

    return AudiobookGenerationJob


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_project_or_404(
    db: AsyncSession,
    project_id: UUID,
    org_id: UUID,
):
    """Fetch an audiobook project, verifying it belongs to the org."""
    model = _project_model()
    query = select(model).where(
        model.id == project_id,
        model.deleted_at.is_(None),
    )
    result = await db.execute(query)
    project = result.scalar_one_or_none()

    if not project:
        raise NotFoundError("Audiobook project")

    if project.org_id != org_id:
        raise ForbiddenError("Access denied to this audiobook project.")

    return project


async def _get_chapter_or_404(
    db: AsyncSession,
    project_id: UUID,
    chapter_id: UUID,
):
    """Fetch an audiobook chapter, verifying it belongs to the project."""
    model = _chapter_model()
    query = select(model).where(
        model.id == chapter_id,
        model.audiobook_project_id == project_id,
        model.deleted_at.is_(None),
    )
    result = await db.execute(query)
    chapter = result.scalar_one_or_none()

    if not chapter:
        raise NotFoundError("Audiobook chapter")

    return chapter


# ---------------------------------------------------------------------------
# Generate single chapter
# ---------------------------------------------------------------------------


async def generate_chapter_audio(
    db: AsyncSession,
    project_id: UUID,
    chapter_id: UUID,
    org_id: UUID,
    request: GenerateChapterRequest,
) -> GenerationJobResponse:
    """Queue chapter audio generation as a Celery task.

    Steps:
        1. Validate project and chapter exist, belong to org
        2. Update chapter status to 'preprocessing'
        3. Create AudiobookGenerationJob record
        4. Dispatch Celery task
        5. Return job info with celery_task_id
    """
    await _get_project_or_404(db, project_id, org_id)
    chapter = await _get_chapter_or_404(db, project_id, chapter_id)

    if chapter.status == "approved":
        raise AppException(
            status_code=409,
            code="CHAPTER_ALREADY_APPROVED",
            message="Chapter audio has already been approved. Use regenerate to replace.",
        )

    chapter.status = "preprocessing"
    chapter.generation_attempts = (chapter.generation_attempts or 0) + 1
    chapter.updated_at = datetime.now(UTC)

    input_params: dict = {}
    if request.voice_id:
        input_params["voice_id"] = str(request.voice_id)
    if request.generation_params:
        input_params.update(request.generation_params)

    job = _job_model()(
        audiobook_project_id=project_id,
        chapter_id=chapter_id,
        job_type="chapter_generate",
        status="queued",
        priority=5,
        input_params=input_params,
    )
    db.add(job)
    await db.flush()

    # Dispatch Celery task (lazy import to avoid circular deps)
    from app.tasks.audiobook_tasks import generate_chapter_audio

    task = generate_chapter_audio.delay(str(job.id), str(chapter_id))
    job.celery_task_id = task.id
    await db.flush()

    logger.info(
        "Queued chapter audio generation: project=%s chapter=%s job=%s celery_task=%s",
        project_id,
        chapter_id,
        job.id,
        task.id,
    )

    return GenerationJobResponse.model_validate(job)


# ---------------------------------------------------------------------------
# Generate all chapters
# ---------------------------------------------------------------------------


async def generate_all_chapters(
    db: AsyncSession,
    project_id: UUID,
    org_id: UUID,
    request: GenerateAllRequest,
) -> GenerateAllResponse:
    """Queue all pending chapters for audio generation.

    Finds all chapters with status 'pending' and creates a generation job for each.
    """
    chapter_cls = _chapter_model()

    project = await _get_project_or_404(db, project_id, org_id)

    query = (
        select(chapter_cls)
        .where(
            chapter_cls.audiobook_project_id == project_id,
            chapter_cls.status == "pending",
            chapter_cls.deleted_at.is_(None),
        )
        .order_by(chapter_cls.chapter_number)
    )
    result = await db.execute(query)
    chapters = result.scalars().all()

    if not chapters:
        raise AppException(
            status_code=422,
            code="NO_PENDING_CHAPTERS",
            message="No chapters with 'pending' status found for generation.",
        )

    from app.tasks.audiobook_tasks import generate_chapter_audio

    job_cls = _job_model()
    jobs: list[GenerationJobResponse] = []

    for chapter in chapters:
        chapter.status = "preprocessing"
        chapter.generation_attempts = (chapter.generation_attempts or 0) + 1
        chapter.updated_at = datetime.now(UTC)

        input_params: dict = {}
        if request.voice_overrides and chapter.chapter_number in request.voice_overrides:
            input_params["voice_id"] = str(request.voice_overrides[chapter.chapter_number])
        input_params["parallel"] = request.parallel

        job = job_cls(
            audiobook_project_id=project_id,
            chapter_id=chapter.id,
            job_type="chapter_generate",
            status="queued",
            priority=5,
            input_params=input_params,
        )
        db.add(job)
        await db.flush()

        task = generate_chapter_audio.delay(str(job.id), str(chapter.id))
        job.celery_task_id = task.id
        await db.flush()

        jobs.append(GenerationJobResponse.model_validate(job))

    project.status = "generating"
    project.updated_at = datetime.now(UTC)

    logger.info(
        "Queued %d chapter(s) for generation: project=%s",
        len(jobs),
        project_id,
    )

    return GenerateAllResponse(
        jobs=jobs,
        total_chapters=project.total_chapters or len(chapters),
        queued_count=len(jobs),
    )


# ---------------------------------------------------------------------------
# Get chapter audio
# ---------------------------------------------------------------------------


async def get_chapter_audio(
    db: AsyncSession,
    project_id: UUID,
    chapter_id: UUID,
    org_id: UUID,
) -> ChapterAudioFileResponse:
    """Get chapter audio URL and metadata.

    Returns a pre-signed S3 URL for the chapter's audio file.
    """
    project = await _get_project_or_404(db, project_id, org_id)
    chapter = await _get_chapter_or_404(db, project_id, chapter_id)

    if not chapter.audio_url:
        raise AppException(
            status_code=404,
            code="AUDIO_NOT_FOUND",
            message="Audio has not been generated for this chapter yet.",
        )

    # ASSUMPTION: audio_url is already a pre-signed S3 URL or storage URL.
    # A storage service would generate fresh pre-signed URLs here.
    return ChapterAudioFileResponse(
        chapter_id=chapter.id,
        chapter_number=chapter.chapter_number,
        chapter_title=chapter.chapter_title,
        audio_url=chapter.audio_url,
        duration_seconds=chapter.duration_seconds or 0,
        file_size_bytes=chapter.file_size_bytes or 0,
        format=project.output_format if project else "mp3",
        sample_rate=project.sample_rate if project else 44100,
        bit_rate=project.bit_rate if project else 192,
    )


# ---------------------------------------------------------------------------
# Regenerate chapter
# ---------------------------------------------------------------------------


async def regenerate_chapter_audio(
    db: AsyncSession,
    project_id: UUID,
    chapter_id: UUID,
    org_id: UUID,
    request: GenerateChapterRequest,
) -> GenerationJobResponse:
    """Regenerate audio for a chapter (re-queues the generation task).

    Similar to generate_chapter_audio but uses the 'chapter_regenerate' job type
    and resets the chapter status.
    """
    await _get_project_or_404(db, project_id, org_id)
    chapter = await _get_chapter_or_404(db, project_id, chapter_id)

    chapter.status = "preprocessing"
    chapter.generation_attempts = (chapter.generation_attempts or 0) + 1
    chapter.updated_at = datetime.now(UTC)

    input_params: dict = {}
    if request.voice_id:
        input_params["voice_id"] = str(request.voice_id)
    if request.generation_params:
        input_params.update(request.generation_params)

    job = _job_model()(
        audiobook_project_id=project_id,
        chapter_id=chapter_id,
        job_type="chapter_regenerate",
        status="queued",
        priority=5,
        input_params=input_params,
    )
    db.add(job)
    await db.flush()

    from app.tasks.audiobook_tasks import generate_chapter_audio

    task = generate_chapter_audio.delay(str(job.id), str(chapter_id))
    job.celery_task_id = task.id
    await db.flush()

    logger.info(
        "Queued chapter audio regeneration: project=%s chapter=%s job=%s",
        project_id,
        chapter_id,
        job.id,
    )

    return GenerationJobResponse.model_validate(job)


# ---------------------------------------------------------------------------
# Approve chapter
# ---------------------------------------------------------------------------


async def approve_chapter(
    db: AsyncSession,
    project_id: UUID,
    chapter_id: UUID,
    org_id: UUID,
    request: ChapterApproveRequest,
) -> ChapterAudioResponse:
    """Approve or request changes for a chapter's audio.

    If approved, updates chapter status to 'approved' and increments the
    project's completed_chapters counter. If not approved, sets status
    back to 'review'.
    """
    project = await _get_project_or_404(db, project_id, org_id)
    chapter = await _get_chapter_or_404(db, project_id, chapter_id)

    if not chapter.audio_url and request.approved:
        raise AppException(
            status_code=422,
            code="NO_AUDIO_TO_APPROVE",
            message="Cannot approve a chapter that has no generated audio.",
        )

    if request.approved:
        chapter.status = "approved"
        project.completed_chapters = (project.completed_chapters or 0) + 1
        project.updated_at = datetime.now(UTC)

        if project.completed_chapters >= (project.total_chapters or 0):
            project.status = "reviewing"
    else:
        chapter.status = "review"

    if request.review_notes is not None:
        chapter.review_notes = request.review_notes

    chapter.updated_at = datetime.now(UTC)

    logger.info(
        "Chapter %s %s: project=%s",
        chapter_id,
        "approved" if request.approved else "sent back for review",
        project_id,
    )

    return ChapterAudioResponse.model_validate(chapter)


# ---------------------------------------------------------------------------
# Regenerate segment
# ---------------------------------------------------------------------------


async def regenerate_segment(
    db: AsyncSession,
    project_id: UUID,
    chapter_id: UUID,
    segment_index: int,
    org_id: UUID,
    request: RegenerateSegmentRequest,
) -> GenerationJobResponse:
    """Regenerate a specific segment (sentence/paragraph) of a chapter.

    Steps:
        1. Get chapter and validate it has audio
        2. Create a segment_regenerate job
        3. Dispatch Celery task
        4. The task will splice new audio into the existing chapter audio
    """
    await _get_project_or_404(db, project_id, org_id)
    chapter = await _get_chapter_or_404(db, project_id, chapter_id)

    if not chapter.audio_url:
        raise AppException(
            status_code=422,
            code="NO_AUDIO_FOR_SEGMENT_REGEN",
            message="Cannot regenerate segment — chapter audio has not been generated yet.",
        )

    input_params: dict = {
        "segment_index": segment_index,
    }
    if request.replacement_text:
        input_params["replacement_text"] = request.replacement_text
    if request.voice_id:
        input_params["voice_id"] = str(request.voice_id)

    job = _job_model()(
        audiobook_project_id=project_id,
        chapter_id=chapter_id,
        job_type="segment_regenerate",
        status="queued",
        priority=3,
        input_params=input_params,
    )
    db.add(job)
    await db.flush()

    from app.tasks.audiobook_tasks import regenerate_segment_task

    task = regenerate_segment_task.delay(str(job.id), str(chapter_id), segment_index)
    job.celery_task_id = task.id
    await db.flush()

    # Track the edit in the chapter's audio_edits JSONB
    edits = chapter.audio_edits or []
    edits.append(
        {
            "segment_index": segment_index,
            "job_id": str(job.id),
            "timestamp": datetime.now(UTC).isoformat(),
            "replacement_text": request.replacement_text,
        }
    )
    chapter.audio_edits = edits
    chapter.updated_at = datetime.now(UTC)

    logger.info(
        "Queued segment regeneration: project=%s chapter=%s segment=%d job=%s",
        project_id,
        chapter_id,
        segment_index,
        job.id,
    )

    return GenerationJobResponse.model_validate(job)
