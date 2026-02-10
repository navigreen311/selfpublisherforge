"""FastAPI router for the Market Intelligence Engine.

Prefix: /api/v1/market
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

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


@router.get("/categories", response_model=list[CategoryNode])
async def browse_categories(
    root_id: Optional[str] = Query(None, description="Parent category ID"),
    marketplace: str = Query("US"),
):
    """Browse Amazon category taxonomy (tree structure)."""
    svc = _service()
    return await svc.get_categories(root_id=root_id, marketplace=marketplace)


@router.get("/categories/{category_id}/analysis", response_model=CategoryAnalysis)
async def category_analysis(
    category_id: str,
    marketplace: str = Query("US"),
):
    """Category analysis with BSR distribution and competition score."""
    svc = _service()
    return await svc.get_category_analysis(category_id, marketplace=marketplace)


# ------------------------------------------------------------------
# Keywords
# ------------------------------------------------------------------


@router.post("/keywords/research", response_model=KeywordResearchResponse)
async def keyword_research(request: KeywordResearchRequest):
    """Keyword research: search volume, competition, CPC, trends."""
    svc = _service()
    return await svc.research_keywords(request)


@router.get("/keywords/suggestions", response_model=list[KeywordData])
async def keyword_suggestions(
    genre: str = Query(..., min_length=1),
    niche: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """AI-suggested keywords for a genre / niche."""
    from app.modules.market_intelligence.schemas import KeywordSuggestionsParams

    svc = _service()
    params = KeywordSuggestionsParams(genre=genre, niche=niche, limit=limit)
    return await svc.suggest_keywords(params)


# ------------------------------------------------------------------
# Niche Analysis
# ------------------------------------------------------------------


@router.post("/analyze-niche", response_model=NicheAnalysisResponse)
async def analyze_niche(request: NicheAnalysisRequest):
    """Comprehensive niche analysis with scoring and gap analysis."""
    svc = _service()
    return await svc.analyze_niche(request)


# ------------------------------------------------------------------
# Competitors
# ------------------------------------------------------------------


@router.get("/competitors", response_model=list[CompetitorListItem])
async def list_competitors(
    marketplace: str = Query("US"),
):
    """List tracked competitor books."""
    svc = _service()
    return await svc.list_competitors(marketplace=marketplace)


@router.post("/competitors/track", response_model=CompetitorDetail, status_code=201)
async def track_competitor(request: CompetitorTrackRequest):
    """Start tracking a competitor by ASIN."""
    svc = _service()
    try:
        return await svc.track_competitor(request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/competitors/{competitor_id}", response_model=CompetitorDetail)
async def get_competitor(competitor_id: UUID):
    """Competitor detail with BSR history."""
    svc = _service()
    detail = await svc.get_competitor(competitor_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return detail


# ------------------------------------------------------------------
# Trends & Snapshots
# ------------------------------------------------------------------


@router.get("/trends", response_model=MarketTrendsResponse)
async def market_trends(
    category_id: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
):
    """Market trend data for categories and keywords."""
    svc = _service()
    return await svc.get_trends(
        category_id=category_id, keyword=keyword, days=days
    )


@router.get("/snapshots", response_model=list[MarketSnapshot])
async def market_snapshots(
    category_id: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=90),
):
    """Daily category snapshots."""
    svc = _service()
    return await svc.get_snapshots(category_id=category_id, limit=limit)
