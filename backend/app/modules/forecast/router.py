"""FastAPI router for Revenue Forecasting (Feature 7)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.forecast import service
from app.modules.forecast.schemas import ForecastResponse

router = APIRouter()


@router.get(
    "/revenue",
    response_model=ForecastResponse,
    summary="AI-powered revenue forecast",
    description=(
        "Linear-regression revenue forecast over a 30/90/180-day horizon with "
        "seasonal adjustment. Reads the existing royalty_records table."
    ),
    responses={
        200: {"description": "Forecast summary + chart data + seasonality insights"},
        401: {"description": "Not authenticated"},
    },
)
async def get_revenue_forecast(
    horizon_days: int = Query(30, description="Forecast horizon in days (30, 90, or 180)"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ForecastResponse:
    return await service.forecast_revenue(
        db, current_user["org_id"], horizon_days=int(horizon_days)
    )
