"""Activity logging service for the Production Pipeline."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.production_pipeline.models import PipelineActivity


async def log_activity(
    db: AsyncSession,
    pipeline_id: uuid.UUID,
    action: str,
    task_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    details: dict | None = None,
) -> PipelineActivity:
    """Record a pipeline activity event."""
    activity = PipelineActivity(
        pipeline_id=pipeline_id,
        task_id=task_id,
        action=action,
        details=details or {},
        user_id=user_id,
    )
    db.add(activity)
    await db.flush()
    return activity


async def get_activity(
    db: AsyncSession,
    pipeline_id: uuid.UUID,
    task_id: uuid.UUID | None = None,
    limit: int = 50,
) -> list[PipelineActivity]:
    """Get activity log for a pipeline or task."""
    stmt = select(PipelineActivity).where(
        PipelineActivity.pipeline_id == pipeline_id,
    )
    if task_id:
        stmt = stmt.where(PipelineActivity.task_id == task_id)

    stmt = stmt.order_by(PipelineActivity.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
