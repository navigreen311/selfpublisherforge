"""FastAPI router for audiobook project CRUD endpoints (/api/v1/audiobooks/...)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.audiobook import service_crud
from app.modules.audiobook.schemas_extended import (
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)

router = APIRouter()


# ── Project CRUD endpoints ────────────────────────────────────────────────


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create audiobook project",
    description="Create a new audiobook project from a book.",
)
async def create_project(
    body: ProjectCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service_crud.create_project(db, current_user["org_id"], body)


@router.get(
    "/",
    response_model=ProjectListResponse,
    summary="List audiobook projects",
    description="List audiobook projects for the organization with pagination and optional status filter.",
)
async def list_projects(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service_crud.list_projects(
        db, current_user["org_id"], page, per_page, status_filter
    )


@router.get(
    "/{project_id}",
    response_model=ProjectDetailResponse,
    summary="Get audiobook project",
    description="Get an audiobook project with its chapters.",
)
async def get_project(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await service_crud.get_project(db, project_id, current_user["org_id"])
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    return result


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update audiobook project",
    description="Update settings for an audiobook project.",
)
async def update_project(
    project_id: UUID,
    body: ProjectUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await service_crud.update_project(
        db, project_id, current_user["org_id"], body
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
    return result


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete audiobook project",
    description="Soft-delete an audiobook project.",
)
async def delete_project(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await service_crud.delete_project(
        db, project_id, current_user["org_id"]
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )
