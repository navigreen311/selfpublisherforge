"""Enhanced task management service with checklist support."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.production_pipeline.models import PipelineTask, TaskStatus


async def create_task(
    db: AsyncSession,
    org_id: uuid.UUID,
    pipeline_id: uuid.UUID,
    stage_id: uuid.UUID | None,
    title: str,
    description: str | None = None,
    priority: str = "medium",
    due_date: datetime | None = None,
    assignee_id: uuid.UUID | None = None,
) -> PipelineTask:
    """Create a task in a pipeline stage."""
    task = PipelineTask(
        org_id=org_id,
        pipeline_id=pipeline_id,
        stage_id=stage_id,
        title=title,
        description=description,
        priority=priority,
        status=TaskStatus.PENDING,
        due_date=due_date,
        assignee_id=assignee_id,
        checklist=[],
        links=[],
        order_index=0,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def move_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    new_stage_id: uuid.UUID,
    new_order: int = 0,
) -> PipelineTask | None:
    """Move a task to a different stage."""
    stmt = select(PipelineTask).where(
        PipelineTask.id == task_id,
        PipelineTask.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        return None

    task.stage_id = new_stage_id
    task.order_index = new_order
    await db.flush()
    await db.refresh(task)
    return task


async def add_checklist_item(db: AsyncSession, task_id: uuid.UUID, label: str) -> PipelineTask | None:
    """Add an item to a task's checklist."""
    stmt = select(PipelineTask).where(
        PipelineTask.id == task_id,
        PipelineTask.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        return None

    checklist = list(task.checklist or [])
    checklist.append(
        {
            "id": str(uuid.uuid4()),
            "label": label,
            "done": False,
            "created_at": datetime.now(UTC).isoformat(),
        }
    )
    task.checklist = checklist
    await db.flush()
    await db.refresh(task)
    return task


async def update_checklist_item(db: AsyncSession, task_id: uuid.UUID, item_id: str, done: bool) -> PipelineTask | None:
    """Toggle a checklist item."""
    stmt = select(PipelineTask).where(
        PipelineTask.id == task_id,
        PipelineTask.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        return None

    checklist = list(task.checklist or [])
    for item in checklist:
        if item.get("id") == item_id:
            item["done"] = done
            break
    task.checklist = checklist
    await db.flush()
    await db.refresh(task)
    return task


async def delete_checklist_item(db: AsyncSession, task_id: uuid.UUID, item_id: str) -> PipelineTask | None:
    """Remove a checklist item."""
    stmt = select(PipelineTask).where(
        PipelineTask.id == task_id,
        PipelineTask.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        return None

    checklist = [i for i in (task.checklist or []) if i.get("id") != item_id]
    task.checklist = checklist
    await db.flush()
    await db.refresh(task)
    return task


async def get_tasks_filtered(
    db: AsyncSession,
    pipeline_id: uuid.UUID,
    stage_id: uuid.UUID | None = None,
    status: str | None = None,
    priority: str | None = None,
) -> list[PipelineTask]:
    """Get tasks with optional filters."""
    stmt = select(PipelineTask).where(
        PipelineTask.pipeline_id == pipeline_id,
        PipelineTask.deleted_at.is_(None),
    )
    if stage_id:
        stmt = stmt.where(PipelineTask.stage_id == stage_id)
    if status:
        stmt = stmt.where(PipelineTask.status == status)
    if priority:
        stmt = stmt.where(PipelineTask.priority == priority)

    stmt = stmt.order_by(PipelineTask.order_index)
    result = await db.execute(stmt)
    return list(result.scalars().all())
