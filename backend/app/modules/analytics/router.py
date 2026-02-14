"""FastAPI router for the Analytics & BI module.

Endpoints:
  GET  /api/v1/analytics/dashboard        Main dashboard
  GET  /api/v1/analytics/revenue           Revenue data
  GET  /api/v1/analytics/royalties         Royalty records
  POST /api/v1/analytics/royalties/import  Import royalty CSV
  GET  /api/v1/analytics/portfolio         Portfolio metrics
  POST /api/v1/analytics/reports/generate  Generate report
  GET  /api/v1/analytics/reports           List reports
  GET  /api/v1/analytics/reports/{id}/download  Download report
  POST /api/v1/analytics/events            Record event
  GET  /api/v1/analytics/trends            Trend data
"""

from __future__ import annotations

import os
from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.pagination import PaginatedResponse
from app.database import get_db
from app.modules.analytics import service
from app.modules.analytics.schemas import (
    AggregationPeriod,
    AnalyticsEventCreate,
    AnalyticsEventResponse,
    DashboardData,
    Platform,
    PortfolioMetrics,
    ReportGenerateRequest,
    ReportRequest,
    ReportResponse,
    RevenueQueryParams,
    RevenueResponse,
    RoyaltyImportRequest,
    RoyaltyImportResponse,
    RoyaltyRecordResponse,
    TrendData,
)

router = APIRouter()


# ---------- Dashboard ----------

@router.get(
    "/dashboard",
    response_model=DashboardData,
    summary="Get analytics dashboard",
    description="Main analytics dashboard with KPIs, charts, and trends.",
    responses={
        200: {"description": "Dashboard data including KPIs, charts, and recent activity"},
        401: {"description": "Not authenticated"},
    },
)
async def get_dashboard(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> DashboardData:
    """Main analytics dashboard with KPIs, charts, and trends."""
    period_start = (
        datetime.combine(start_date, datetime.min.time()).replace(tzinfo=UTC)
        if start_date else None
    )
    period_end = (
        datetime.combine(end_date, datetime.max.time()).replace(tzinfo=UTC)
        if end_date else None
    )
    return await service.get_dashboard(
        db, current_user["org_id"], period_start, period_end
    )


# ---------- Revenue ----------

@router.get(
    "/revenue",
    response_model=RevenueResponse,
    summary="Get revenue data",
    description="Revenue data filtered by book, date range, platform, and aggregation period.",
)
async def get_revenue(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    platform: Platform | None = Query(default=None),
    book_id: UUID | None = Query(default=None),
    aggregation: AggregationPeriod = Query(default=AggregationPeriod.MONTHLY),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> RevenueResponse:
    """Revenue data filtered by book, period, and platform."""
    params = RevenueQueryParams(
        start_date=start_date,
        end_date=end_date,
        platform=platform,
        book_id=book_id,
        aggregation=aggregation,
    )
    return await service.get_revenue(db, current_user["org_id"], params)


# ---------- Royalties ----------

@router.get(
    "/royalties",
    response_model=PaginatedResponse[RoyaltyRecordResponse],
    summary="List royalty records",
    description="List royalty records with pagination and optional platform filter.",
)
async def get_royalties(
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    platform: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse[RoyaltyRecordResponse]:
    """List royalty records with pagination."""
    return await service.get_royalties(
        db, current_user["org_id"], cursor=cursor, limit=limit, platform=platform
    )


@router.post(
    "/royalties/import",
    response_model=RoyaltyImportResponse,
    summary="Import royalty data",
    description="Import royalty data from a base64-encoded CSV file.",
)
async def import_royalties(
    request: RoyaltyImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> RoyaltyImportResponse:
    """Import royalty data from a CSV file (base64-encoded)."""
    return await service.import_royalty_data(
        db, current_user["org_id"], request
    )


# ---------- Portfolio ----------

@router.get(
    "/portfolio",
    response_model=PortfolioMetrics,
    summary="Get portfolio metrics",
    description="Portfolio-level metrics including total books, revenue, and ROI.",
)
async def get_portfolio(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> PortfolioMetrics:
    """Portfolio-level metrics: total books, revenue, ROI."""
    return await service.get_portfolio_metrics(db, current_user["org_id"])


# ---------- Reports ----------

@router.post(
    "/reports/generate",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate report",
    description="Generate a custom analytics report in PDF or XLSX format.",
)
async def generate_report(
    request: ReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ReportResponse:
    """Generate a custom report (PDF or XLSX)."""
    return await service.create_report(
        db, current_user["org_id"], current_user["user_id"], request
    )


@router.get(
    "/reports",
    response_model=PaginatedResponse[ReportResponse],
    summary="List reports",
    description="List previously generated reports with pagination.",
)
async def list_reports(
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse[ReportResponse]:
    """List generated reports."""
    return await service.list_reports(
        db, current_user["org_id"], cursor=cursor, limit=limit
    )


@router.get(
    "/reports/{report_id}/download",
    summary="Download report",
    description="Download a completed report file (PDF or XLSX).",
)
async def download_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> FileResponse:
    """Download a generated report file."""
    report = await service.get_report_by_id(
        db, current_user["org_id"], report_id
    )
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    if report.status != "completed" or not report.file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report is not ready for download",
        )
    if not os.path.exists(report.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found on disk",
        )

    media_type = (
        "application/pdf"
        if report.output_format == "pdf"
        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    filename = f"{report.title}.{report.output_format}"

    return FileResponse(
        path=report.file_path,
        media_type=media_type,
        filename=filename,
    )


# ---------- Events ----------

@router.post(
    "/events",
    response_model=AnalyticsEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record analytics event",
    description="Record a custom analytics event for tracking.",
)
async def record_event(
    event: AnalyticsEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> AnalyticsEventResponse:
    """Record an analytics event."""
    return await service.record_event(db, current_user["org_id"], event)


# ---------- Trends ----------

@router.get(
    "/trends",
    response_model=TrendData,
    summary="Get trend data",
    description="Trend data for key metrics over a configurable time period.",
)
async def get_trends(
    metric: str = Query(default="revenue"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    aggregation: AggregationPeriod = Query(default=AggregationPeriod.MONTHLY),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> TrendData:
    """Trend data for key metrics."""
    period_start = (
        datetime.combine(start_date, datetime.min.time()).replace(tzinfo=UTC)
        if start_date else None
    )
    period_end = (
        datetime.combine(end_date, datetime.max.time()).replace(tzinfo=UTC)
        if end_date else None
    )
    return await service.get_trends(
        db, current_user["org_id"], metric=metric,
        period_start=period_start, period_end=period_end,
        aggregation=aggregation,
    )


# ---------- Enhanced Dashboard ----------

@router.get(
    "/dashboard/enhanced",
    summary="Get enhanced analytics dashboard",
    description="Enhanced dashboard with KPI comparisons, trend data, revenue breakdowns, and AI insights.",
    responses={
        200: {"description": "Enhanced dashboard data"},
        401: {"description": "Not authenticated"},
    },
)
async def get_enhanced_dashboard(
    period: str = Query(default="30d", description="Period length, e.g. 30d, 60d, 90d"),
    compare: str = Query(default="previous", description="Comparison period: 'previous'"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Enhanced analytics dashboard with comparisons and AI insights."""
    from app.modules.analytics.enhanced_dashboard_service import (
        get_enhanced_dashboard as _get_enhanced,
    )
    from app.core.contracts import SuccessResponse

    data = await _get_enhanced(db, current_user["org_id"], period=period, compare=compare)
    return SuccessResponse(data=data)


# ---------- Sales Data ----------

@router.get(
    "/sales",
    summary="Get sales data",
    description="Daily sales data with totals and marketplace breakdown.",
    responses={
        200: {"description": "Sales data with daily breakdown, totals, and marketplace split"},
        401: {"description": "Not authenticated"},
    },
)
async def get_sales(
    period: str = Query(default="30d", description="Period length, e.g. 30d, 60d"),
    book_id: UUID | None = Query(default=None, description="Filter by book ID"),
    marketplace: str | None = Query(default=None, description="Filter by marketplace, e.g. US, UK"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Sales data with daily breakdown, totals, and marketplace split."""
    from app.modules.analytics.sales_service import get_sales_data
    from app.core.contracts import SuccessResponse

    data = await get_sales_data(
        db, current_user["org_id"], period=period, book_id=book_id, marketplace=marketplace,
    )
    return SuccessResponse(data=data)


# ---------- Book Performance ----------

@router.get(
    "/books/{book_id}/performance",
    summary="Get book performance",
    description="Detailed book performance including BSR history, revenue breakdown, and review trends.",
    responses={
        200: {"description": "Book performance data"},
        401: {"description": "Not authenticated"},
    },
)
async def get_book_performance(
    book_id: UUID,
    period: str = Query(default="90d", description="Period length, e.g. 30d, 90d"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Detailed book performance with BSR history and revenue breakdown."""
    from app.modules.analytics.book_performance_service import (
        get_book_performance as _get_perf,
    )
    from app.core.contracts import SuccessResponse

    data = await _get_perf(db, current_user["org_id"], book_id, period=period)
    return SuccessResponse(data=data)


# ---------- Enhanced Report Generation ----------

@router.post(
    "/reports/generate/enhanced",
    status_code=status.HTTP_201_CREATED,
    summary="Generate enhanced report",
    description="Generate an analytics report with custom sections, date ranges, and format options.",
    responses={
        201: {"description": "Report created successfully"},
        401: {"description": "Not authenticated"},
    },
)
async def generate_enhanced_report(
    request: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate a report with enhanced options (sections, book filtering, etc.)."""
    from app.modules.analytics.models import Report
    from app.modules.analytics.schemas import ReportStatus
    from app.core.contracts import SuccessResponse

    report = Report(
        org_id=current_user["org_id"],
        title=request.title,
        report_type=request.type,
        output_format=request.format,
        parameters={
            "period_start": request.period_start,
            "period_end": request.period_end,
            "book_ids": request.book_ids,
            "sections": request.sections,
        },
        status=ReportStatus.PENDING.value,
        generated_by=current_user["user_id"],
    )
    db.add(report)
    await db.flush()

    return SuccessResponse(data={
        "id": str(report.id),
        "title": report.title,
        "type": report.report_type,
        "format": report.output_format,
        "status": report.status,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    })
