"""Stage management service for the Production Pipeline."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.production_pipeline.models import PipelineStage, Pipeline


async def create_stage(
    db: AsyncSession,
    pipeline_id: uuid.UUID,
    org_id: uuid.UUID,
    name: str,
    color: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> PipelineStage:
    """Create a new stage at the end of the pipeline."""
    # Get max order_index
    stmt = select(func.coalesce(func.max(PipelineStage.order_index), -1)).where(
        PipelineStage.pipeline_id == pipeline_id,
        PipelineStage.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    max_idx = result.scalar() or -1

    stage = PipelineStage(
        org_id=org_id,
        pipeline_id=pipeline_id,
        name=name,
        order_index=max_idx + 1,
        color=color,
        start_date=start_date,
        end_date=end_date,
    )
    db.add(stage)
    await db.flush()
    await db.refresh(stage)
    return stage


async def get_stages(
    db: AsyncSession, pipeline_id: uuid.UUID
) -> list[PipelineStage]:
    """Get all stages for a pipeline, ordered."""
    stmt = (
        select(PipelineStage)
        .where(
            PipelineStage.pipeline_id == pipeline_id,
            PipelineStage.deleted_at.is_(None),
        )
        .order_by(PipelineStage.order_index)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_stage(
    db: AsyncSession,
    stage_id: uuid.UUID,
    **kwargs,
) -> PipelineStage | None:
    """Update stage properties."""
    stmt = select(PipelineStage).where(
        PipelineStage.id == stage_id,
        PipelineStage.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    stage = result.scalar_one_or_none()
    if not stage:
        return None

    for key, value in kwargs.items():
        if value is not None and hasattr(stage, key):
            setattr(stage, key, value)

    await db.flush()
    await db.refresh(stage)
    return stage


async def delete_stage(
    db: AsyncSession, stage_id: uuid.UUID
) -> bool:
    """Soft delete a stage. Tasks in this stage get stage_id set to NULL."""
    from datetime import UTC, datetime
    from app.modules.production_pipeline.models import PipelineTask

    stmt = select(PipelineStage).where(
        PipelineStage.id == stage_id,
        PipelineStage.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    stage = result.scalar_one_or_none()
    if not stage:
        return False

    # Unassign tasks from this stage
    task_stmt = select(PipelineTask).where(PipelineTask.stage_id == stage_id)
    task_result = await db.execute(task_stmt)
    for task in task_result.scalars().all():
        task.stage_id = None

    stage.deleted_at = datetime.now(UTC)
    await db.flush()
    return True


async def reorder_stages(
    db: AsyncSession,
    pipeline_id: uuid.UUID,
    stage_order: list[dict],
) -> list[PipelineStage]:
    """Bulk reorder stages. stage_order is [{stage_id, order_index}, ...]."""
    for item in stage_order:
        stmt = select(PipelineStage).where(
            PipelineStage.id == uuid.UUID(str(item["stage_id"])),
            PipelineStage.pipeline_id == pipeline_id,
        )
        result = await db.execute(stmt)
        stage = result.scalar_one_or_none()
        if stage:
            stage.order_index = item["order_index"]

    await db.flush()
    return await get_stages(db, pipeline_id)
