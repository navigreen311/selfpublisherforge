"""Activity log router - list/filter activity events."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.activity.models import ActivityLog

router = APIRouter()


@router.get(
    "",
    summary="List activity log entries",
    description="List activity log entries for the current organization with optional filters.",
)
async def list_activity(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: UUID | None = Query(None),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    since: datetime | None = Query(None),
    until: datetime | None = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    clauses = [ActivityLog.org_id == current_user["org_id"]]
    if user_id:
        clauses.append(ActivityLog.user_id == user_id)
    if action:
        clauses.append(ActivityLog.action == action)
    if resource_type:
        clauses.append(ActivityLog.resource_type == resource_type)
    if since:
        clauses.append(ActivityLog.created_at >= since)
    if until:
        clauses.append(ActivityLog.created_at <= until)

    stmt = select(ActivityLog).where(and_(*clauses)).order_by(ActivityLog.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    rows = result.scalars().all()

    return {
        "items": [
            {
                "id": str(r.id),
                "user_id": str(r.user_id) if r.user_id else None,
                "action": r.action,
                "description": r.description,
                "resource_type": r.resource_type,
                "resource_id": str(r.resource_id) if r.resource_id else None,
                "metadata": r.activity_metadata or {},
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "limit": limit,
        "offset": offset,
    }
