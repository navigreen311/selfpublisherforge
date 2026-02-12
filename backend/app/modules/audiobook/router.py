"""API router for the Audiobook Production Studio module.

Endpoints:
  POST   /                   -- Create audiobook project from book
  GET    /                   -- List audiobook projects (filtered by org)
  GET    /{project_id}       -- Get audiobook project details with chapters
  PATCH  /{project_id}       -- Update project settings
  DELETE /{project_id}       -- Delete audiobook project

  GET    /voices             -- List available voices (system + custom)
  POST   /voices             -- Create custom voice (upload for cloning)
  GET    /voices/{voice_id}/preview -- Generate voice preview audio
  DELETE /voices/{voice_id}  -- Delete custom voice
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.audiobook import schemas, service

router = APIRouter()


# ---------------------------------------------------------------------------
# Voices — registered BEFORE parameterised /{project_id} to avoid conflicts
# ---------------------------------------------------------------------------

@router.get(
    "/voices",
    response_model=list[schemas.AudiobookVoiceResponse],
    summary="List available voices",
    description="List all available voices including system voices and the organization's custom voices.",
)
async def list_voices(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List available voices (system + custom for the org)."""
    return await service.list_voices(db, current_user["org_id"])


@router.post(
    "/voices",
    response_model=schemas.AudiobookVoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create custom voice",
    description="Create a custom voice profile for cloning. Actual TTS cloning is processed asynchronously.",
)
async def create_voice(
    request: schemas.AudiobookVoiceCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a custom voice for audiobook narration."""
    return await service.create_voice_clone(db, current_user["org_id"], request)


@router.get(
    "/voices/{voice_id}/preview",
    response_model=schemas.VoicePreviewResponse,
    summary="Preview voice",
    description="Generate or retrieve a voice preview audio sample.",
)
async def preview_voice(
    voice_id: UUID,
    sample_text: str | None = Query(default=None, max_length=500),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a voice preview audio sample."""
    return await service.preview_voice(db, voice_id, sample_text)


@router.delete(
    "/voices/{voice_id}",
    response_model=schemas.DeleteResponse,
    summary="Delete custom voice",
    description="Delete a custom voice profile. System voices cannot be deleted.",
)
async def delete_voice(
    voice_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a custom voice."""
    await service.delete_voice(db, voice_id, current_user["org_id"])
    return schemas.DeleteResponse()


# ---------------------------------------------------------------------------
# Audiobook Project CRUD
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=schemas.AudiobookProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create audiobook project",
    description="Create a new audiobook project from an existing book. Chapters are auto-imported from the manuscript.",
)
async def create_audiobook_project(
    request: schemas.AudiobookProjectCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new audiobook project from an existing book."""
    return await service.create_project(
        db, current_user["org_id"], current_user["user_id"], request,
    )


@router.get(
    "",
    response_model=schemas.AudiobookProjectListResponse,
    summary="List audiobook projects",
    description="List audiobook projects for the current organization with pagination and optional status filter.",
)
async def list_audiobook_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List audiobook projects for the current organization."""
    return await service.list_projects(
        db, current_user["org_id"], page, page_size, status_filter,
    )


@router.get(
    "/{project_id}",
    response_model=schemas.AudiobookProjectResponse,
    summary="Get audiobook project",
    description="Get an audiobook project's details including all chapters.",
)
async def get_audiobook_project(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get audiobook project details with chapters."""
    return await service.get_project(db, project_id, current_user["org_id"])


@router.patch(
    "/{project_id}",
    response_model=schemas.AudiobookProjectResponse,
    summary="Update audiobook project",
    description="Update an audiobook project's title, status, voice, or settings.",
)
async def update_audiobook_project(
    project_id: UUID,
    request: schemas.AudiobookProjectUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an audiobook project."""
    return await service.update_project(
        db, project_id, current_user["org_id"], request,
    )


@router.delete(
    "/{project_id}",
    response_model=schemas.DeleteResponse,
    summary="Delete audiobook project",
    description="Soft-delete an audiobook project and its associated chapters.",
)
async def delete_audiobook_project(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an audiobook project."""
    await service.delete_project(db, project_id, current_user["org_id"])
    return schemas.DeleteResponse()
