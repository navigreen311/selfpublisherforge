"""FastAPI router for the Market Intelligence Engine.

Prefix: /api/v1/market
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.market_intelligence.schemas import (
    CategoryAnalysis,
    CategoryNode,
    CompetitorDetail,
    CompetitorListItem,
    CompetitorTrackRequest,
    KeywordData,
    KeywordResearchRequest,
    KeywordResearchResponse,
    MarketSnapshot,
    MarketTrendsResponse,
    NicheAnalysisRequest,
    NicheAnalysisResponse,
)
from app.modules.market_intelligence.service import MarketIntelligenceService

router = APIRouter()


def _service() -> MarketIntelligenceService:
    return MarketIntelligenceService()


# ------------------------------------------------------------------
# Categories
# ------------------------------------------------------------------


@router.get(
    "/categories",
    response_model=list[CategoryNode],
    summary="Browse categories",
    description="Browse Amazon category taxonomy as a tree structure.",
)
async def browse_categories(
    root_id: str | None = Query(None, description="Parent category ID"),
    marketplace: str = Query("US"),
    current_user: dict = Depends(get_current_user),
):
    """Browse Amazon category taxonomy (tree structure)."""
    svc = _service()
    return await svc.get_categories(root_id=root_id, marketplace=marketplace)


@router.get(
    "/categories/{category_id}/analysis",
    response_model=CategoryAnalysis,
    summary="Category analysis",
    description="Category analysis with BSR distribution and competition score.",
)
async def category_analysis(
    category_id: str,
    marketplace: str = Query("US"),
    current_user: dict = Depends(get_current_user),
):
    """Category analysis with BSR distribution and competition score."""
    svc = _service()
    return await svc.get_category_analysis(category_id, marketplace=marketplace)


# ------------------------------------------------------------------
# Keywords
# ------------------------------------------------------------------


@router.post(
    "/keywords/research",
    response_model=KeywordResearchResponse,
    summary="Keyword research",
    description="Research keywords for search volume, competition, CPC, and trends.",
)
async def keyword_research(
    request: KeywordResearchRequest,
    current_user: dict = Depends(get_current_user),
):
    """Keyword research: search volume, competition, CPC, trends."""
    svc = _service()
    return await svc.research_keywords(request)


@router.get(
    "/keywords/suggestions",
    response_model=list[KeywordData],
    summary="Keyword suggestions",
    description="Get AI-suggested keywords for a genre or niche.",
)
async def keyword_suggestions(
    genre: str = Query(..., min_length=1),
    niche: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """AI-suggested keywords for a genre / niche."""
    from app.modules.market_intelligence.schemas import KeywordSuggestionsParams

    svc = _service()
    params = KeywordSuggestionsParams(genre=genre, niche=niche, limit=limit)
    return await svc.suggest_keywords(params)


# ------------------------------------------------------------------
# Niche Analysis
# ------------------------------------------------------------------


@router.post(
    "/analyze-niche",
    response_model=NicheAnalysisResponse,
    summary="Analyze niche",
    description="Comprehensive niche analysis with scoring, demand signals, and gap analysis.",
)
async def analyze_niche(
    request: NicheAnalysisRequest,
    current_user: dict = Depends(get_current_user),
):
    """Comprehensive niche analysis with scoring and gap analysis."""
    svc = _service()
    return await svc.analyze_niche(request)


# ------------------------------------------------------------------
# Competitors
# ------------------------------------------------------------------


@router.get(
    "/competitors",
    response_model=list[CompetitorListItem],
    summary="List tracked competitors",
    description="List all tracked competitor books for a marketplace.",
)
async def list_competitors(
    marketplace: str = Query("US"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List tracked competitor books."""
    svc = _service()
    return await svc.list_competitors(db=db, org_id=current_user["org_id"], marketplace=marketplace)


@router.post(
    "/competitors/track",
    response_model=CompetitorDetail,
    status_code=201,
    summary="Track competitor",
    description="Start tracking a competitor book by ASIN.",
)
async def track_competitor(
    request: CompetitorTrackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Start tracking a competitor by ASIN."""
    svc = _service()
    try:
        return await svc.track_competitor(db=db, request=request, org_id=current_user["org_id"])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get(
    "/competitors/{competitor_id}",
    response_model=CompetitorDetail,
    summary="Get competitor detail",
    description="Get competitor detail including BSR history and pricing data.",
)
async def get_competitor(
    competitor_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Competitor detail with BSR history."""
    svc = _service()
    detail = await svc.get_competitor(db=db, competitor_id=competitor_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return detail


# ------------------------------------------------------------------
# Trends & Snapshots
# ------------------------------------------------------------------


@router.get(
    "/trends",
    response_model=MarketTrendsResponse,
    summary="Market trends",
    description="Market trend data for categories and keywords over a configurable period.",
)
async def market_trends(
    category_id: str | None = Query(None),
    keyword: str | None = Query(None),
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
):
    """Market trend data for categories and keywords."""
    svc = _service()
    return await svc.get_trends(
        category_id=category_id, keyword=keyword, days=days
    )


@router.get(
    "/snapshots",
    response_model=list[MarketSnapshot],
    summary="Daily market snapshots",
    description="Daily category snapshots with BSR and pricing aggregates.",
)
async def market_snapshots(
    category_id: str | None = Query(None),
    limit: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Daily category snapshots."""
    svc = _service()
    return await svc.get_snapshots(db=db, category_id=category_id, limit=limit)
