"""Audit trail recording for the Agent System.

Every agent action is logged with actor, resource, and details for compliance
and debugging purposes.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_system.models import AuditAction, AuditTrail

logger = logging.getLogger(__name__)


async def record_audit(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    action: AuditAction,
    actor_id: uuid.UUID,
    actor_type: str = "user",
    resource_type: str,
    resource_id: uuid.UUID,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditTrail:
    """Create an immutable audit trail entry."""
    entry = AuditTrail(
        org_id=org_id,
        action=action,
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    await db.flush()
    return entry


async def list_audit_entries(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    action: AuditAction | None = None,
    actor_id: uuid.UUID | None = None,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    cursor: str | None = None,
    limit: int = 20,
) -> tuple[list[AuditTrail], str | None, bool, int]:
    """Return paginated audit entries with optional filters.

    Returns (items, next_cursor, has_more, total_count).
    """
    # Count query
    count_q = select(func.count()).select_from(AuditTrail).where(AuditTrail.org_id == org_id)
    if action:
        count_q = count_q.where(AuditTrail.action == action)
    if actor_id:
        count_q = count_q.where(AuditTrail.actor_id == actor_id)
    if resource_type:
        count_q = count_q.where(AuditTrail.resource_type == resource_type)
    if resource_id:
        count_q = count_q.where(AuditTrail.resource_id == resource_id)

    total_result = await db.execute(count_q)
    total_count = total_result.scalar() or 0

    # Data query
    query = select(AuditTrail).where(AuditTrail.org_id == org_id).order_by(desc(AuditTrail.created_at))
    if action:
        query = query.where(AuditTrail.action == action)
    if actor_id:
        query = query.where(AuditTrail.actor_id == actor_id)
    if resource_type:
        query = query.where(AuditTrail.resource_type == resource_type)
    if resource_id:
        query = query.where(AuditTrail.resource_id == resource_id)
    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor)
            query = query.where(AuditTrail.created_at < cursor_dt)
        except ValueError:
            logger.exception("Failed to write audit log entry")

    query = query.limit(limit + 1)
    result = await db.execute(query)
    entries = list(result.scalars().all())

    has_more = len(entries) > limit
    if has_more:
        entries = entries[:limit]

    next_cursor = None
    if has_more and entries:
        next_cursor = entries[-1].created_at.isoformat()

    return entries, next_cursor, has_more, total_count
