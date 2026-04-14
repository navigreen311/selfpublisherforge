"""Router for Series Analytics (read-through rate tracking).

Endpoints:
  GET  /api/v1/series/{series_id}/analytics
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.series_analytics import service
from app.modules.series_analytics.schemas import SeriesAnalyticsResponse

router = APIRouter()


@router.get(
    "/series/{series_id}/analytics",
    response_model=SeriesAnalyticsResponse,
    summary="Series read-through analytics",
    description=(
        "Read-through rates, sales funnel, and revenue per book for a single series. "
        "Metrics are aggregated from series_sales_data over the requested period."
    ),
    responses={
        200: {"description": "Series analytics payload"},
        401: {"description": "Not authenticated"},
    },
)
async def get_series_analytics_endpoint(
    series_id: UUID,
    period: str = Query(default="90d", pattern="^(30d|90d|1y)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> SeriesAnalyticsResponse:
    """Return read-through funnel, rates, and revenue breakdown for the series."""
    return await service.get_series_analytics(
        db, current_user["org_id"], series_id, period=period
    )
