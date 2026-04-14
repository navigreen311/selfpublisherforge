"""Dashboard aggregator endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.dashboard import service
from app.modules.dashboard.schemas import DashboardResponse

router = APIRouter()


@router.get(
    "",
    response_model=DashboardResponse,
    summary="Get dashboard aggregate",
    description=(
        "Aggregates stats, revenue trend, active pipelines, recent activity, "
        "AI insights, and upcoming deadlines for the current organization."
    ),
)
async def get_dashboard(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    return await service.get_dashboard(db, current_user["org_id"])
