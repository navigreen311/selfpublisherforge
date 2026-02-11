"""Service layer for the Production Pipeline module.

Handles Pipeline CRUD, task management, status transitions, and deadline calculations.
"""

from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.production_pipeline.models import (
    Pipeline,
    PipelineStatus,
    PipelineTask,
    PipelineTemplate,
    TaskStatus,
    TaskType,
)
from app.modules.production_pipeline.schemas import (
    CreatePipeline,
    CreateTask,
    CreateTemplate,
    PaginatedPipelines,
    PipelineSummaryResponse,
    TimelineTask,
    TimelineView,
    UpdatePipeline,
    UpdateTask,
)
from app.modules.production_pipeline.workflow import (
    WorkflowError,
    compute_blocked_tasks,
    compute_critical_path,
    compute_task_progress,
    detect_cycle,
    get_overdue_tasks,
    get_ready_tasks,
    validate_pipeline_transition,
    validate_task_transition,
)

# ── Pipeline CRUD ─────────────────────────────────────────────────────────


async def create_pipeline(
    db: AsyncSession,
    org_id: uuid.UUID,
    payload: CreatePipeline,
) -> Pipeline:
    """Create a new pipeline, optionally from a template."""
    pipeline = Pipeline(
        org_id=org_id,
        book_id=payload.book_id,
        name=payload.name,
        description=payload.description,
        status=PipelineStatus.DRAFT,
        settings=payload.settings or {},
        deadline=payload.deadline,
    )
    db.add(pipeline)
    await db.flush()

    # If a template_id is provided, seed tasks from the template
    if payload.template_id:
        template = await db.get(PipelineTemplate, payload.template_id)
        if template and template.task_definitions:
            for idx, td in enumerate(template.task_definitions):
                task = PipelineTask(
                    org_id=org_id,
                    pipeline_id=pipeline.id,
                    title=td.get("title", f"Task {idx + 1}"),
                    description=td.get("description"),
                    type=TaskType(td.get("type", "writing")),
                    status=TaskStatus.PENDING,
                    depends_on=td.get("depends_on", []),
                    position=td.get("position", idx),
                )
                # Calculate due dates from estimated_days if pipeline has deadline
                if payload.deadline and td.get("estimated_days"):
                    task.due_date = payload.deadline - timedelta(
                        days=max(0, len(template.task_definitions) - idx)
                    )
                db.add(task)

    await db.flush()
    await db.refresh(pipeline)
    return pipeline


async def get_pipeline(
    db: AsyncSession, pipeline_id: uuid.UUID, org_id: uuid.UUID
) -> Pipeline | None:
    """Get a single pipeline with its tasks."""
    stmt = select(Pipeline).where(
        Pipeline.id == pipeline_id,
        Pipeline.org_id == org_id,
        Pipeline.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_pipelines(
    db: AsyncSession,
    org_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    status: PipelineStatus | None = None,
    book_id: uuid.UUID | None = None,
) -> PaginatedPipelines:
    """List pipelines with pagination and optional filters."""
    base = select(Pipeline).where(
        Pipeline.org_id == org_id,
        Pipeline.deleted_at.is_(None),
    )
    if status:
        base = base.where(Pipeline.status == status)
    if book_id:
        base = base.where(Pipeline.book_id == book_id)

    # Total count
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Fetch page
    stmt = base.order_by(Pipeline.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size)
    result = await db.execute(stmt)
    pipelines = list(result.scalars().all())

    now = datetime.now(UTC)
    items: list[PipelineSummaryResponse] = []
    for p in pipelines:
        tasks = p.tasks or []
        completed_count = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        overdue_count = len(get_overdue_tasks(tasks, now))
        items.append(
            PipelineSummaryResponse(
                id=p.id,
                org_id=p.org_id,
                book_id=p.book_id,
                name=p.name,
                status=p.status,
                deadline=p.deadline,
                task_count=len(tasks),
                completed_task_count=completed_count,
                overdue_task_count=overdue_count,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )

    return PaginatedPipelines(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


async def update_pipeline(
    db: AsyncSession,
    pipeline_id: uuid.UUID,
    org_id: uuid.UUID,
    payload: UpdatePipeline,
) -> Pipeline | None:
    """Update pipeline settings / status."""
    pipeline = await get_pipeline(db, pipeline_id, org_id)
    if not pipeline:
        return None

    update_data = payload.model_dump(exclude_unset=True)

    # Validate status transition if changing status
    if "status" in update_data and update_data["status"] is not None:
        validate_pipeline_transition(pipeline.status, update_data["status"])

    for field, value in update_data.items():
        setattr(pipeline, field, value)

    await db.flush()
    await db.refresh(pipeline)
    return pipeline


async def delete_pipeline(
    db: AsyncSession, pipeline_id: uuid.UUID, org_id: uuid.UUID
) -> bool:
    """Soft-delete a pipeline."""
    pipeline = await get_pipeline(db, pipeline_id, org_id)
    if not pipeline:
        return False
    pipeline.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


# ── Task Management ───────────────────────────────────────────────────────


async def add_task(
    db: AsyncSession,
    pipeline_id: uuid.UUID,
    org_id: uuid.UUID,
    payload: CreateTask,
) -> PipelineTask | None:
    """Add a task to a pipeline."""
    pipeline = await get_pipeline(db, pipeline_id, org_id)
    if not pipeline:
        return None

    task = PipelineTask(
        org_id=org_id,
        pipeline_id=pipeline_id,
        title=payload.title,
        description=payload.description,
        type=payload.type,
        status=TaskStatus.PENDING,
        assignee_id=payload.assignee_id,
        due_date=payload.due_date,
        depends_on=payload.depends_on or [],
        position=payload.position,
    )
    db.add(task)
    await db.flush()

    # Validate no cycle introduced
    await db.refresh(pipeline)
    if detect_cycle(pipeline.tasks):
        await db.rollback()
        raise WorkflowError("Adding this task would create a dependency cycle.")

    # Update blocked statuses
    await _refresh_blocked_statuses(db, pipeline)

    await db.refresh(task)
    return task


async def update_task(
    db: AsyncSession,
    pipeline_id: uuid.UUID,
    task_id: uuid.UUID,
    org_id: uuid.UUID,
    payload: UpdateTask,
) -> PipelineTask | None:
    """Update a task's status, assignee, etc."""
    pipeline = await get_pipeline(db, pipeline_id, org_id)
    if not pipeline:
        return None

    task = await _get_task(db, task_id, pipeline_id)
    if not task:
        return None

    update_data = payload.model_dump(exclude_unset=True)

    # Validate status transition
    if "status" in update_data and update_data["status"] is not None:
        validate_task_transition(task.status, update_data["status"])
        if update_data["status"] == TaskStatus.COMPLETED:
            update_data["completed_at"] = datetime.now(UTC)

    for field, value in update_data.items():
        setattr(task, field, value)

    await db.flush()

    # Re-check for cycles if dependencies changed
    if "depends_on" in update_data:
        await db.refresh(pipeline)
        if detect_cycle(pipeline.tasks):
            await db.rollback()
            raise WorkflowError(
                "Updating dependencies would create a cycle."
            )

    # Refresh blocked statuses across the pipeline
    await db.refresh(pipeline)
    await _refresh_blocked_statuses(db, pipeline)

    await db.refresh(task)
    return task


async def _get_task(
    db: AsyncSession, task_id: uuid.UUID, pipeline_id: uuid.UUID
) -> PipelineTask | None:
    stmt = select(PipelineTask).where(
        PipelineTask.id == task_id,
        PipelineTask.pipeline_id == pipeline_id,
        PipelineTask.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _refresh_blocked_statuses(
    db: AsyncSession, pipeline: Pipeline
) -> None:
    """Mark tasks blocked/unblocked based on current dependency state."""
    tasks = pipeline.tasks or []
    blocked = compute_blocked_tasks(tasks)
    blocked_ids = {str(t.id) for t in blocked}
    ready = get_ready_tasks(tasks)
    ready_ids = {str(t.id) for t in ready}

    for t in tasks:
        tid = str(t.id)
        if tid in blocked_ids and t.status == TaskStatus.PENDING:
            t.status = TaskStatus.BLOCKED
        elif tid in ready_ids and t.status == TaskStatus.BLOCKED:
            t.status = TaskStatus.PENDING


# ── Timeline ──────────────────────────────────────────────────────────────


async def get_timeline(
    db: AsyncSession, pipeline_id: uuid.UUID, org_id: uuid.UUID
) -> TimelineView | None:
    """Generate a Gantt-style timeline view for a pipeline."""
    pipeline = await get_pipeline(db, pipeline_id, org_id)
    if not pipeline:
        return None

    tasks = pipeline.tasks or []
    critical = compute_critical_path(tasks) if tasks else []

    timeline_tasks: list[TimelineTask] = []
    for t in tasks:
        timeline_tasks.append(
            TimelineTask(
                id=t.id,
                title=t.title,
                type=t.type,
                status=t.status,
                assignee_id=t.assignee_id,
                start_date=t.created_at,
                due_date=t.due_date,
                completed_at=t.completed_at,
                depends_on=t.depends_on or [],
                progress=compute_task_progress(t),
            )
        )

    return TimelineView(
        pipeline_id=pipeline.id,
        pipeline_name=pipeline.name,
        deadline=pipeline.deadline,
        tasks=timeline_tasks,
        critical_path=critical,
    )


# ── Templates ─────────────────────────────────────────────────────────────


async def create_template(
    db: AsyncSession, org_id: uuid.UUID, payload: CreateTemplate
) -> PipelineTemplate:
    """Save a pipeline template."""
    template = PipelineTemplate(
        org_id=org_id,
        name=payload.name,
        description=payload.description,
        task_definitions=[td.model_dump() for td in payload.task_definitions],
        settings=payload.settings or {},
        is_public=payload.is_public,
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)
    return template


async def list_templates(
    db: AsyncSession, org_id: uuid.UUID
) -> list[PipelineTemplate]:
    """List templates visible to the org (own + public)."""
    stmt = select(PipelineTemplate).where(
        (PipelineTemplate.org_id == org_id) | (PipelineTemplate.is_public.is_(True)),
        PipelineTemplate.deleted_at.is_(None),
    ).order_by(PipelineTemplate.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_template_from_pipeline(
    db: AsyncSession,
    pipeline_id: uuid.UUID,
    org_id: uuid.UUID,
    name: str,
    description: str | None = None,
) -> PipelineTemplate | None:
    """Save an existing pipeline as a reusable template."""
    pipeline = await get_pipeline(db, pipeline_id, org_id)
    if not pipeline:
        return None

    task_defs = []
    for t in (pipeline.tasks or []):
        task_defs.append(
            {
                "title": t.title,
                "type": t.type.value,
                "description": t.description,
                "depends_on": t.depends_on or [],
                "position": t.position,
                "estimated_days": 1,
            }
        )

    template = PipelineTemplate(
        org_id=org_id,
        name=name,
        description=description,
        task_definitions=task_defs,
        settings=pipeline.settings or {},
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)
    return template
