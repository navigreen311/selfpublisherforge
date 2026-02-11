"""API router for the Production Pipeline module."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.production_pipeline import service
from app.modules.production_pipeline.models import PipelineStatus
from app.modules.production_pipeline.schemas import (
    CreatePipeline,
    CreateTask,
    CreateTemplate,
    PaginatedPipelines,
    PipelineResponse,
    TaskResponse,
    TemplateResponse,
    TimelineView,
    UpdatePipeline,
    UpdateTask,
)
from app.modules.production_pipeline.workflow import WorkflowError

router = APIRouter()


# ── Template endpoints (MUST be before /{pipeline_id} routes) ─────────────


@router.post(
    "/templates",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a pipeline template",
    description="Save a reusable pipeline template with predefined stages and tasks.",
)
async def create_template(
    payload: CreateTemplate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    template = await service.create_template(db, current_user["org_id"], payload)
    return template


@router.get(
    "/templates",
    response_model=list[TemplateResponse],
    summary="List pipeline templates",
    description="List all available pipeline templates for the organization.",
)
async def list_templates(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_templates(db, current_user["org_id"])


# ── Pipeline endpoints ────────────────────────────────────────────────────


@router.post(
    "",
    response_model=PipelineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new production pipeline",
    description="Create a new production pipeline for a book, optionally from a template.",
)
async def create_pipeline(
    payload: CreatePipeline,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pipeline = await service.create_pipeline(db, current_user["org_id"], payload)
    return pipeline


@router.get(
    "",
    response_model=PaginatedPipelines,
    summary="List pipelines (paginated, filterable)",
    description="List production pipelines with optional status and book filters.",
)
async def list_pipelines(
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    pipeline_status: PipelineStatus | None = Query(None, alias="status"),
    book_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await service.list_pipelines(
        db, current_user["org_id"], page=page, page_size=page_size, status=pipeline_status, book_id=book_id
    )


@router.get(
    "/{pipeline_id}",
    response_model=PipelineResponse,
    summary="Get pipeline detail with tasks",
    description="Get full pipeline detail including all tasks and their statuses.",
)
async def get_pipeline(
    pipeline_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pipeline = await service.get_pipeline(db, pipeline_id, current_user["org_id"])
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found.")
    return pipeline


@router.patch(
    "/{pipeline_id}",
    response_model=PipelineResponse,
    summary="Update pipeline settings",
    description="Update pipeline status, due date, or other settings.",
)
async def update_pipeline(
    pipeline_id: uuid.UUID,
    payload: UpdatePipeline,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        pipeline = await service.update_pipeline(db, pipeline_id, current_user["org_id"], payload)
    except WorkflowError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found.")
    return pipeline


# ── Task endpoints ────────────────────────────────────────────────────────


@router.post(
    "/{pipeline_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a task to a pipeline",
    description="Add a new task to an existing pipeline with stage and dependency info.",
)
async def add_task(
    pipeline_id: uuid.UUID,
    payload: CreateTask,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        task = await service.add_task(db, pipeline_id, current_user["org_id"], payload)
    except WorkflowError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not task:
        raise HTTPException(status_code=404, detail="Pipeline not found.")
    return task


@router.patch(
    "/{pipeline_id}/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Update task status/assignee",
    description="Update a task's status, assignee, or completion state.",
)
async def update_task(
    pipeline_id: uuid.UUID,
    task_id: uuid.UUID,
    payload: UpdateTask,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        task = await service.update_task(db, pipeline_id, task_id, current_user["org_id"], payload)
    except WorkflowError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not task:
        raise HTTPException(status_code=404, detail="Pipeline or task not found.")
    return task


# ── Timeline endpoint ─────────────────────────────────────────────────────


@router.get(
    "/{pipeline_id}/timeline",
    response_model=TimelineView,
    summary="Get Gantt-style timeline for a pipeline",
    description="Get a Gantt-style timeline view with task dependencies and dates.",
)
async def get_timeline(
    pipeline_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    timeline = await service.get_timeline(db, pipeline_id, current_user["org_id"])
    if not timeline:
        raise HTTPException(status_code=404, detail="Pipeline not found.")
    return timeline
