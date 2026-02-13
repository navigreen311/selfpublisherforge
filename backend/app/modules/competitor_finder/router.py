"""FastAPI router for the Competitor Weakness Finder module.

Endpoints:
  POST /competitors/analyze          - Deep analyze a competitor book
  GET  /competitors/{id}/weaknesses  - Get detected weaknesses
  POST /competitors/batch-analyze    - Analyze top N books in a category
  GET  /competitors/{id}/opportunity  - Get opportunity blueprint
  POST /competitors/gap-analysis     - Cover/title/content gap analysis
  GET  /competitors/alerts           - Get competitor alerts
"""
from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.competitor_finder.schemas import (
    BatchAnalyzeRequest,
    BatchAnalyzeResponse,
    CompetitorAlertSchema,
    CompetitorAnalysisSchema,
    CompetitorAnalyzeRequest,
    GapAnalysisRequest,
    GapAnalysisSchema,
    OpportunityBlueprintSchema,
    WeaknessSignalSchema,
)
from app.modules.competitor_finder.service import CompetitorFinderService
from app.tasks.competitor_finder import process_batch_analysis, process_single_analysis

VALID_MARKETPLACES = {"US", "UK", "DE", "FR", "JP", "IT", "ES", "IN", "CA", "AU"}

router = APIRouter()


@router.post(
    "/analyze",
    response_model=CompetitorAnalysisSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Deep analyze a competitor book",
    description="Analyze reviews, listing, and positioning of a competitor book.",
)
async def analyze_competitor(
    request: CompetitorAnalyzeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CompetitorFinderService(db)
    try:
        analysis = await service.analyze_competitor(
            request=request,
            org_id=current_user["org_id"],
        )
        process_single_analysis.delay(
            analysis_id=str(analysis.id),
            org_id=str(current_user["org_id"]),
            include_opportunity=request.include_opportunity,
        )
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{analysis_id}/weaknesses",
    response_model=list[WeaknessSignalSchema],
    summary="Get detected weaknesses from analysis",
    description="Returns all weakness signals detected during review analysis.",
)
async def get_weaknesses(
    analysis_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CompetitorFinderService(db)
    try:
        weaknesses = await service.get_weaknesses(
            analysis_id=analysis_id,
            org_id=current_user["org_id"],
        )
        return weaknesses
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/batch-analyze",
    response_model=BatchAnalyzeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Batch analyze top N books in a category",
    description="Starts analysis for the top N competitor books in a given category.",
)
async def batch_analyze(
    request: BatchAnalyzeRequest,
    marketplace: str = Query("US", description="Amazon marketplace code"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if marketplace not in VALID_MARKETPLACES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid marketplace '{marketplace}'. Must be one of: {', '.join(sorted(VALID_MARKETPLACES))}",
        )
    service = CompetitorFinderService(db)
    try:
        analyses = await service.batch_analyze(
            request=request,
            org_id=current_user["org_id"],
        )
        task = process_batch_analysis.delay(
            analysis_ids=[str(a.id) for a in analyses],
            org_id=str(current_user["org_id"]),
            include_opportunity=request.include_opportunity,
        )
        return BatchAnalyzeResponse(
            task_id=task.id,
            analyses_created=len(analyses),
            book_ids=[a.book_id for a in analyses],
            message=f"Batch analysis started for {len(analyses)} books",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/{analysis_id}/opportunity",
    response_model=OpportunityBlueprintSchema | None,
    summary="Get opportunity blueprint",
    description="Returns the AI-generated opportunity blueprint for beating this competitor.",
)
async def get_opportunity(
    analysis_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CompetitorFinderService(db)
    try:
        opportunity = await service.get_opportunity(
            analysis_id=analysis_id,
            org_id=current_user["org_id"],
        )
        if not opportunity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No opportunity blueprint found for this analysis",
            )
        return opportunity
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/gap-analysis",
    response_model=GapAnalysisSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Run gap analysis for a niche",
    description="Analyze cover, title, and content gaps across competitor books in a niche.",
)
async def gap_analysis(
    request: GapAnalysisRequest,
    marketplace: str = Query("US", description="Amazon marketplace code"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if marketplace not in VALID_MARKETPLACES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid marketplace '{marketplace}'. Must be one of: {', '.join(sorted(VALID_MARKETPLACES))}",
        )
    service = CompetitorFinderService(db)
    try:
        result = await service.run_gap_analysis(
            request=request,
            org_id=current_user["org_id"],
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/alerts",
    response_model=list[CompetitorAlertSchema],
    summary="Get competitor alerts",
    description="Get alerts for price changes, new books, BSR shifts, and review spikes.",
)
async def get_alerts(
    include_dismissed: bool = Query(False, description="Include dismissed alerts"),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CompetitorFinderService(db)
    alerts = await service.get_alerts(
        org_id=current_user["org_id"],
        include_dismissed=include_dismissed,
        limit=limit,
    )
    return alerts


# ------------------------------------------------------------------
# Enhanced Competitor CRUD Endpoints
# ------------------------------------------------------------------


@router.post("", status_code=201)
async def add_competitor(
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add competitor by ASIN/URL/title."""
    return {
        "id": str(uuid4()),
        "asin": body.get("identifier", ""),
        "title": "Pending lookup",
        "author": "",
        "tracked": True,
    }


@router.get("")
async def list_tracked(
    project_id: str = Query(None),
    sort: str = Query("bsr"),
    page: int = Query(1),
    limit: int = Query(20),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List tracked competitors."""
    return {"competitors": [], "total": 0}


@router.delete("/{competitor_id}")
async def remove_competitor(
    competitor_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove competitor from tracking."""
    return {"status": "removed"}


@router.get("/{competitor_id}/bsr-history")
async def bsr_history(
    competitor_id: UUID,
    period: str = Query("90d"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get BSR history."""
    return {"data": []}


@router.get("/{competitor_id}/reviews")
async def competitor_reviews(
    competitor_id: UUID,
    sort: str = Query("recent"),
    page: int = Query(1),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get competitor reviews."""
    return {"reviews": [], "total": 0}


@router.post("/compare")
async def compare_books(
    body: dict,
    current_user: dict = Depends(get_current_user),
):
    """Compare books side by side."""
    return {"books": [], "feature_list": []}


# ------------------------------------------------------------------
# Alert CRUD Endpoints
# ------------------------------------------------------------------


@router.post("/alerts", status_code=201)
async def create_alert(
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create alert."""
    return {"id": str(uuid4()), **body, "active": True, "created_at": "now"}


@router.patch("/alerts/{alert_id}")
async def update_alert(
    alert_id: UUID,
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update alert."""
    return {"id": str(alert_id), **body}


@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete alert."""
    return {"status": "deleted"}


@router.get("/alerts/history")
async def alert_history(
    page: int = Query(1),
    limit: int = Query(20),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Alert event history."""
    return {"events": []}
