"""API router for the Audiobook module — SSML & Pronunciation endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.audiobook import service
from app.modules.audiobook import service_crud as crud_service
from app.modules.audiobook.schemas import (
    PronunciationCreate,
    PronunciationListResponse,
    PronunciationResponse,
    SSMLGenerateRequest,
    SSMLResponse,
    SSMLUpdateRequest,
)
from app.modules.audiobook.schemas_extended import AudiobookStatsResponse

router = APIRouter()


# ── SSML endpoints ─────────────────────────────────────────────────────────


@router.post(
    "/{project_id}/chapters/{chapter_id}/ssml",
    response_model=SSMLResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate SSML from chapter text",
    description=(
        "Generate SSML annotations from a chapter's plain text using "
        "dialogue detection, emotion tagging, and pronunciation dictionary."
    ),
)
async def generate_ssml(
    project_id: UUID,
    chapter_id: UUID,
    request: SSMLGenerateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await service.generate_ssml(
        db,
        project_id=project_id,
        chapter_id=chapter_id,
        org_id=current_user["org_id"],
        options=request.options,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found.",
        )
    return result


@router.patch(
    "/{project_id}/chapters/{chapter_id}/ssml",
    response_model=SSMLResponse,
    summary="Update SSML annotations",
    description="Update a chapter's SSML text with manual edits. Validates SSML syntax before saving.",
)
async def update_ssml(
    project_id: UUID,
    chapter_id: UUID,
    request: SSMLUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await service.update_ssml(
            db,
            project_id=project_id,
            chapter_id=chapter_id,
            org_id=current_user["org_id"],
            ssml_text=request.ssml_text,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found.",
        )
    return result


# ── Pronunciation endpoints ────────────────────────────────────────────────


@router.post(
    "/pronunciation",
    response_model=PronunciationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add pronunciation entry",
    description="Add a custom pronunciation entry to the organization's dictionary.",
)
async def add_pronunciation(
    request: PronunciationCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entry = await service.add_pronunciation(db, current_user["org_id"], request)
    return entry


@router.get(
    "/pronunciation",
    response_model=PronunciationListResponse,
    summary="List pronunciation dictionary",
    description="List pronunciation entries for the organization, optionally filtered by project.",
)
async def list_pronunciation(
    project_id: UUID | None = Query(None, description="Filter by audiobook project ID"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entries = await service.list_pronunciation(
        db, current_user["org_id"], project_id=project_id
    )
    return PronunciationListResponse(items=entries, total=len(entries))


@router.delete(
    "/pronunciation/{pron_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete pronunciation entry",
    description="Soft-delete a pronunciation entry from the dictionary.",
)
async def delete_pronunciation(
    pron_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await service.delete_pronunciation(db, pron_id, current_user["org_id"])
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pronunciation entry not found.",
        )




# Stats endpoint

@router.get(
    "/stats",
    response_model=AudiobookStatsResponse,
    summary="Get audiobook statistics",
    description="Get statistics for audiobook projects in the organization: total, in progress, completed, and total duration.",
)
async def get_audiobook_stats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await crud_service.get_audiobook_stats(db, current_user["org_id"])
