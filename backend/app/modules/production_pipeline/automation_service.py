"""Automation rules engine for the Production Pipeline."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.production_pipeline.models import PipelineAutomation


async def create_automation(
    db: AsyncSession,
    pipeline_id: uuid.UUID,
    trigger_type: str,
    trigger_config: dict,
    action_type: str,
    action_config: dict,
    enabled: bool = True,
) -> PipelineAutomation:
    """Create an automation rule."""
    automation = PipelineAutomation(
        pipeline_id=pipeline_id,
        trigger_type=trigger_type,
        trigger_config=trigger_config,
        action_type=action_type,
        action_config=action_config,
        enabled=enabled,
    )
    db.add(automation)
    await db.flush()
    await db.refresh(automation)
    return automation


async def get_automations(
    db: AsyncSession, pipeline_id: uuid.UUID
) -> list[PipelineAutomation]:
    """List all automations for a pipeline."""
    stmt = (
        select(PipelineAutomation)
        .where(PipelineAutomation.pipeline_id == pipeline_id)
        .order_by(PipelineAutomation.created_at)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_automation(
    db: AsyncSession, automation_id: uuid.UUID, **kwargs
) -> PipelineAutomation | None:
    """Update an automation rule."""
    stmt = select(PipelineAutomation).where(PipelineAutomation.id == automation_id)
    result = await db.execute(stmt)
    automation = result.scalar_one_or_none()
    if not automation:
        return None

    for key, value in kwargs.items():
        if value is not None and hasattr(automation, key):
            setattr(automation, key, value)

    await db.flush()
    await db.refresh(automation)
    return automation


async def delete_automation(
    db: AsyncSession, automation_id: uuid.UUID
) -> bool:
    """Delete an automation rule."""
    stmt = select(PipelineAutomation).where(PipelineAutomation.id == automation_id)
    result = await db.execute(stmt)
    automation = result.scalar_one_or_none()
    if not automation:
        return False

    await db.delete(automation)
    await db.flush()
    return True


async def evaluate_trigger(
    db: AsyncSession,
    pipeline_id: uuid.UUID,
    event_type: str,
    event_data: dict | None = None,
) -> list[dict]:
    """Check if any enabled automations match the event and return actions to execute."""
    automations = await get_automations(db, pipeline_id)
    actions: list[dict] = []

    for auto in automations:
        if not auto.enabled:
            continue
        if auto.trigger_type != event_type:
            continue

        # Check trigger config matches event data
        trigger_cfg = auto.trigger_config or {}
        if event_type == "task_moved_to_stage" or event_type == "all_tasks_complete_in_stage":
            if trigger_cfg.get("stage_id") and event_data:
                if str(trigger_cfg["stage_id"]) != str(event_data.get("stage_id", "")):
                    continue

        actions.append({
            "automation_id": str(auto.id),
            "action_type": auto.action_type,
            "action_config": auto.action_config,
        })

    return actions
