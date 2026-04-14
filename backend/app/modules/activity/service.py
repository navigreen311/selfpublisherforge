"""Activity log service -- helper to record activity events."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.activity.models import ActivityLog

logger = logging.getLogger(__name__)


async def log_activity(
    db: AsyncSession,
    *,
    org_id: UUID,
    user_id: UUID | None,
    action: str,
    description: str | None = None,
    resource_type: str | None = None,
    resource_id: UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> ActivityLog:
    """Create a new activity log entry.

    Best-effort: logs but does not raise on failures -- activity logging
    should never break the caller's flow.
    """
    entry = ActivityLog(
        org_id=org_id,
        user_id=user_id,
        action=action,
        description=description,
        resource_type=resource_type,
        resource_id=resource_id,
        activity_metadata=metadata or {},
    )
    db.add(entry)
    try:
        await db.flush()
    except Exception as exc:  # noqa: BLE001
        logger.warning("activity_log flush failed: %s", exc)
    return entry
