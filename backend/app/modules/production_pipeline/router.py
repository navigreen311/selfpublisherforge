"""API router for the Production Pipeline module."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.production_pipeline import (
    activity_service,
    automation_service,
    service,
    stage_service,
    task_service,
)
from app.modules.production_pipeline.models import PipelineStatus
from app.modules.production_pipeline.schemas import (
    ActivityResponse,
    AutomationCreate,
    AutomationResponse,
    AutomationUpdate,
    ChecklistItemCreate,
    CreatePipeline,
    CreateTask,
    CreateTemplate,
    PaginatedPipelines,
    PipelineResponse,
    StageCreate,
    StageReorderRequest,
    StageResponse,
    StageUpdate,
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


# ── Stage endpoints ──────────────────────────────────────────────────────


@router.post(
    "/{pipeline_id}/stages",
    response_model=StageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a pipeline stage",
    description="Add a new stage to a pipeline. The stage is appended at the end.",
)
async def create_stage(
    pipeline_id: uuid.UUID,
    payload: StageCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify the pipeline exists and belongs to the org
    pipeline = await service.get_pipeline(db, pipeline_id, current_user["org_id"])
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found.")

    stage = await stage_service.create_stage(
        db,
        pipeline_id=pipeline_id,
        org_id=current_user["org_id"],
        name=payload.name,
        color=payload.color,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    await activity_service.log_activity(
        db,
        pipeline_id=pipeline_id,
        action="stage_created",
        user_id=current_user["user_id"],
        details={"stage_id": str(stage.id), "name": payload.name},
    )
    return stage


@router.get(
    "/{pipeline_id}/stages",
    response_model=list[StageResponse],
    summary="List pipeline stages",
    description="Get all stages for a pipeline in order.",
)
async def list_stages(
    pipeline_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pipeline = await service.get_pipeline(db, pipeline_id, current_user["org_id"])
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found.")
    return await stage_service.get_stages(db, pipeline_id)


@router.patch(
    "/{pipeline_id}/stages/{stage_id}",
    response_model=StageResponse,
    summary="Update a pipeline stage",
    description="Update stage name, color, or dates.",
)
async def update_stage(
    pipeline_id: uuid.UUID,
    stage_id: uuid.UUID,
    payload: StageUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pipeline = await service.get_pipeline(db, pipeline_id, current_user["org_id"])
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found.")

    update_data = payload.model_dump(exclude_unset=True)
    stage = await stage_service.update_stage(db, stage_id, **update_data)
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found.")

    await activity_service.log_activity(
        db,
        pipeline_id=pipeline_id,
        action="stage_updated",
        user_id=current_user["user_id"],
        details={"stage_id": str(stage_id), "changes": list(update_data.keys())},
    )
    return stage


@router.delete(
    "/{pipeline_id}/stages/{stage_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a pipeline stage",
    description="Soft-delete a stage. Tasks in the stage are unassigned.",
)
async def delete_stage(
    pipeline_id: uuid.UUID,
    stage_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pipeline = await service.get_pipeline(db, pipeline_id, current_user["org_id"])
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found.")

    deleted = await stage_service.delete_stage(db, stage_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Stage not found.")

    await activity_service.log_activity(
        db,
        pipeline_id=pipeline_id,
        action="stage_deleted",
        user_id=current_user["user_id"],
        details={"stage_id": str(stage_id)},
    )
    return


@router.post(
    "/{pipeline_id}/stages/reorder",
    response_model=list[StageResponse],
    summary="Reorder pipeline stages",
    description="Bulk reorder stages by providing an ordered list of stage IDs.",
)
async def reorder_stages(
    pipeline_id: uuid.UUID,
    payload: StageReorderRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pipeline = await service.get_pipeline(db, pipeline_id, current_user["org_id"])
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found.")

    stage_order = [{"stage_id": str(sid), "order_index": idx} for idx, sid in enumerate(payload.stage_ids)]
    stages = await stage_service.reorder_stages(db, pipeline_id, stage_order)

    await activity_service.log_activity(
        db,
        pipeline_id=pipeline_id,
        action="stages_reordered",
        user_id=current_user["user_id"],
        details={"new_order": [str(sid) for sid in payload.stage_ids]},
    )
    return stages


# ── Enhanced Task endpoints (checklist) ──────────────────────────────────


@router.post(
    "/{pipeline_id}/tasks/{task_id}/checklist",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a checklist item to a task",
    description="Append a new checklist item to the task's checklist.",
)
async def add_checklist_item(
    pipeline_id: uuid.UUID,
    task_id: uuid.UUID,
    payload: ChecklistItemCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pipeline = await service.get_pipeline(db, pipeline_id, current_user["org_id"])
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found.")

    task = await task_service.add_checklist_item(db, task_id, payload.label)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    await activity_service.log_activity(
        db,
        pipeline_id=pipeline_id,
        task_id=task_id,
        action="checklist_item_added",
        user_id=current_user["user_id"],
        details={"label": payload.label},
    )
    return task


@router.patch(
    "/{pipeline_id}/tasks/{task_id}/checklist/{checklist_item_id}",
    response_model=TaskResponse,
    summary="Update a checklist item",
    description="Toggle the done state of a checklist item.",
)
async def update_checklist_item(
    pipeline_id: uuid.UUID,
    task_id: uuid.UUID,
    checklist_item_id: str,
    payload: ChecklistItemCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pipeline = await service.get_pipeline(db, pipeline_id, current_user["org_id"])
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found.")

    task = await task_service.update_checklist_item(db, task_id, checklist_item_id, payload.done)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    await activity_service.log_activity(
        db,
        pipeline_id=pipeline_id,
        task_id=task_id,
        action="checklist_item_updated",
        user_id=current_user["user_id"],
        details={"item_id": checklist_item_id, "done": payload.done},
    )
    return task


@router.delete(
    "/{pipeline_id}/tasks/{task_id}/checklist/{checklist_item_id}",
    response_model=TaskResponse,
    summary="Delete a checklist item",
    description="Remove a checklist item from a task.",
)
async def delete_checklist_item(
    pipeline_id: uuid.UUID,
    task_id: uuid.UUID,
    checklist_item_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pipeline = await service.get_pipeline(db, pipeline_id, current_user["org_id"])
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found.")

    task = await task_service.delete_checklist_item(db, task_id, checklist_item_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    await activity_service.log_activity(
        db,
        pipeline_id=pipeline_id,
        task_id=task_id,
        action="checklist_item_deleted",
        user_id=current_user["user_id"],
        details={"item_id": checklist_item_id},
    )
    return task


# ── Activity endpoint ────────────────────────────────────────────────────


@router.get(
    "/{pipeline_id}/activity",
    response_model=list[ActivityResponse],
    summary="Get pipeline activity log",
    description="Get the activity log for a pipeline, optionally filtered by task.",
)
async def get_activity(
    pipeline_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    task_id: uuid.UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    pipeline = await service.get_pipeline(db, pipeline_id, current_user["org_id"])
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found.")

    return await activity_service.get_activity(db, pipeline_id, task_id=task_id, limit=limit)


# ── Automation endpoints ─────────────────────────────────────────────────


@router.post(
    "/{pipeline_id}/automations",
    response_model=AutomationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a pipeline automation",
    description="Create an automation rule that triggers actions based on pipeline events.",
)
async def create_automation(
    pipeline_id: uuid.UUID,
    payload: AutomationCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pipeline = await service.get_pipeline(db, pipeline_id, current_user["org_id"])
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found.")

    automation = await automation_service.create_automation(
        db,
        pipeline_id=pipeline_id,
        trigger_type=payload.trigger_type,
        trigger_config=payload.trigger_config,
        action_type=payload.action_type,
        action_config=payload.action_config,
        enabled=payload.enabled,
    )

    await activity_service.log_activity(
        db,
        pipeline_id=pipeline_id,
        action="automation_created",
        user_id=current_user["user_id"],
        details={
            "automation_id": str(automation.id),
            "trigger_type": payload.trigger_type,
            "action_type": payload.action_type,
        },
    )
    return automation


@router.get(
    "/{pipeline_id}/automations",
    response_model=list[AutomationResponse],
    summary="List pipeline automations",
    description="Get all automation rules for a pipeline.",
)
async def list_automations(
    pipeline_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pipeline = await service.get_pipeline(db, pipeline_id, current_user["org_id"])
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found.")

    return await automation_service.get_automations(db, pipeline_id)


@router.patch(
    "/{pipeline_id}/automations/{automation_id}",
    response_model=AutomationResponse,
    summary="Update a pipeline automation",
    description="Update an automation rule's trigger, action, or enabled state.",
)
async def update_automation(
    pipeline_id: uuid.UUID,
    automation_id: uuid.UUID,
    payload: AutomationUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pipeline = await service.get_pipeline(db, pipeline_id, current_user["org_id"])
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found.")

    update_data = payload.model_dump(exclude_unset=True)
    automation = await automation_service.update_automation(db, automation_id, **update_data)
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found.")

    await activity_service.log_activity(
        db,
        pipeline_id=pipeline_id,
        action="automation_updated",
        user_id=current_user["user_id"],
        details={
            "automation_id": str(automation_id),
            "changes": list(update_data.keys()),
        },
    )
    return automation


@router.delete(
    "/{pipeline_id}/automations/{automation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a pipeline automation",
    description="Permanently remove an automation rule.",
)
async def delete_automation(
    pipeline_id: uuid.UUID,
    automation_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pipeline = await service.get_pipeline(db, pipeline_id, current_user["org_id"])
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found.")

    deleted = await automation_service.delete_automation(db, automation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Automation not found.")

    await activity_service.log_activity(
        db,
        pipeline_id=pipeline_id,
        action="automation_deleted",
        user_id=current_user["user_id"],
        details={"automation_id": str(automation_id)},
    )
    return
