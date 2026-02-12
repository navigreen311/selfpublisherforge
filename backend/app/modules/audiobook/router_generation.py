"""FastAPI router for audiobook generation endpoints (/api/v1/audiobooks/...)."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.audiobook import schemas_generation as schemas
from app.modules.audiobook import service_generation as service

router = APIRouter()


@router.post(
    "/{project_id}/chapters/{chapter_id}/generate",
    response_model=schemas.GenerationJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate chapter audio",
    description="Queue audio generation for a single chapter.",
)
async def generate_chapter_audio(
    project_id: UUID,
    chapter_id: UUID,
    body: schemas.GenerateChapterRequest = schemas.GenerateChapterRequest(),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Queue audio generation for a single chapter."""
    return await service.generate_chapter_audio(
        db,
        project_id=project_id,
        chapter_id=chapter_id,
        org_id=current_user["org_id"],
        request=body,
    )


@router.post(
    "/{project_id}/generate-all",
    response_model=schemas.GenerateAllResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate all chapters",
    description="Queue audio generation for all pending chapters in the project.",
)
async def generate_all_chapters(
    project_id: UUID,
    body: schemas.GenerateAllRequest = schemas.GenerateAllRequest(),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Queue audio generation for all pending chapters."""
    return await service.generate_all_chapters(
        db,
        project_id=project_id,
        org_id=current_user["org_id"],
        request=body,
    )


@router.get(
    "/{project_id}/chapters/{chapter_id}/audio",
    response_model=schemas.ChapterAudioFileResponse,
    summary="Get chapter audio",
    description="Get the audio file URL and metadata for a chapter.",
)
async def get_chapter_audio(
    project_id: UUID,
    chapter_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get chapter audio file URL and metadata."""
    return await service.get_chapter_audio(
        db,
        project_id=project_id,
        chapter_id=chapter_id,
        org_id=current_user["org_id"],
    )


@router.post(
    "/{project_id}/chapters/{chapter_id}/regenerate",
    response_model=schemas.GenerationJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Regenerate chapter audio",
    description="Queue regeneration of audio for a chapter.",
)
async def regenerate_chapter_audio(
    project_id: UUID,
    chapter_id: UUID,
    body: schemas.GenerateChapterRequest = schemas.GenerateChapterRequest(),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Queue regeneration of audio for a chapter."""
    return await service.regenerate_chapter_audio(
        db,
        project_id=project_id,
        chapter_id=chapter_id,
        org_id=current_user["org_id"],
        request=body,
    )


@router.patch(
    "/{project_id}/chapters/{chapter_id}/approve",
    response_model=schemas.ChapterAudioResponse,
    summary="Approve chapter audio",
    description="Approve or request changes for a chapter's generated audio.",
)
async def approve_chapter_audio(
    project_id: UUID,
    chapter_id: UUID,
    body: schemas.ChapterApproveRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve or request changes for a chapter's audio."""
    return await service.approve_chapter(
        db,
        project_id=project_id,
        chapter_id=chapter_id,
        org_id=current_user["org_id"],
        request=body,
    )


@router.post(
    "/{project_id}/chapters/{chapter_id}/segments/{segment_index}/regenerate",
    response_model=schemas.GenerationJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Regenerate segment",
    description="Regenerate a specific segment (sentence/paragraph) within a chapter.",
)
async def regenerate_segment(
    project_id: UUID,
    chapter_id: UUID,
    segment_index: int,
    body: schemas.RegenerateSegmentRequest = schemas.RegenerateSegmentRequest(),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Regenerate a specific segment of a chapter's audio."""
    return await service.regenerate_segment(
        db,
        project_id=project_id,
        chapter_id=chapter_id,
        segment_index=segment_index,
        org_id=current_user["org_id"],
        request=body,
    )
