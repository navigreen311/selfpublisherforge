"""FastAPI router for Advertising Intelligence endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.core.dependencies import get_current_user
from app.core.pagination import PaginatedResponse
from app.modules.advertising.schemas import (
    AdDashboard,
    AdPerformance,
    AdCreativeResponse,
    CampaignCreate,
    CampaignFilter,
    CampaignResponse,
    CampaignUpdate,
    CampaignWithPerformance,
    CreativeGenerateRequest,
    CreativeGenerateResponse,
    KeywordBidBulkUpdate,
    KeywordBidResponse,
    OptimizationRequest,
    OptimizationSuggestion,
    PerformanceQuery,
    AdPlatform,
    CampaignStatus,
    CampaignType,
)
from app.modules.advertising.service import AdvertisingService

router = APIRouter()


def _get_service(db: AsyncSession = Depends(get_db)) -> AdvertisingService:
    return AdvertisingService(db)


# ─── Campaign Endpoints ──────────────────────────────────────────────────────

@router.get(
    "/campaigns",
    response_model=PaginatedResponse[CampaignWithPerformance],
    summary="List ad campaigns",
    description="List ad campaigns across platforms with optional filters and performance summaries.",
)
async def list_campaigns(
    platform: AdPlatform | None = None,
    campaign_status: CampaignStatus | None = Query(None, alias="status"),
    campaign_type: CampaignType | None = None,
    book_id: UUID | None = None,
    cursor: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    service: AdvertisingService = Depends(_get_service),
):
    """List ad campaigns across platforms with performance summaries."""
    filters = CampaignFilter(
        platform=platform,
        status=campaign_status,
        campaign_type=campaign_type,
        book_id=book_id,
    )
    campaigns, next_cursor, total_count = await service.list_campaigns(
        org_id=current_user["org_id"],
        filters=filters,
        cursor=cursor,
        limit=limit,
    )
    return PaginatedResponse(
        items=campaigns,
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
        total_count=total_count,
    )


@router.post(
    "/campaigns",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create ad campaign",
    description="Create a new advertising campaign on a supported platform.",
)
async def create_campaign(
    data: CampaignCreate,
    current_user: dict = Depends(get_current_user),
    service: AdvertisingService = Depends(_get_service),
):
    """Create a new ad campaign."""
    return await service.create_campaign(
        org_id=current_user["org_id"],
        data=data,
    )


@router.get(
    "/campaigns/{campaign_id}",
    response_model=CampaignWithPerformance,
    summary="Get campaign detail",
    description="Get campaign detail with aggregated performance metrics.",
)
async def get_campaign(
    campaign_id: UUID,
    current_user: dict = Depends(get_current_user),
    service: AdvertisingService = Depends(_get_service),
):
    """Get campaign detail with performance metrics."""
    campaign = await service.get_campaign(
        org_id=current_user["org_id"],
        campaign_id=campaign_id,
    )
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    return campaign


@router.patch(
    "/campaigns/{campaign_id}",
    response_model=CampaignResponse,
    summary="Update campaign",
    description="Update an existing campaign's settings, budget, or targeting.",
)
async def update_campaign(
    campaign_id: UUID,
    data: CampaignUpdate,
    current_user: dict = Depends(get_current_user),
    service: AdvertisingService = Depends(_get_service),
):
    """Update an existing campaign."""
    campaign = await service.update_campaign(
        org_id=current_user["org_id"],
        campaign_id=campaign_id,
        data=data,
    )
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    return campaign


# ─── Performance Endpoints ────────────────────────────────────────────────────

@router.get(
    "/campaigns/{campaign_id}/performance",
    response_model=list[AdPerformance],
    summary="Get campaign performance",
    description="Get detailed performance data including impressions, clicks, spend, sales, and ACOS.",
)
async def get_campaign_performance(
    campaign_id: UUID,
    date_from: str | None = None,
    date_to: str | None = None,
    granularity: str = "daily",
    current_user: dict = Depends(get_current_user),
    service: AdvertisingService = Depends(_get_service),
):
    """Get detailed performance data (impressions, clicks, spend, sales, ACOS)."""
    from datetime import datetime

    query = PerformanceQuery(granularity=granularity)
    if date_from:
        try:
            query.date_from = datetime.fromisoformat(date_from)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format")
    if date_to:
        try:
            query.date_to = datetime.fromisoformat(date_to)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format")

    return await service.get_campaign_performance(
        org_id=current_user["org_id"],
        campaign_id=campaign_id,
        query=query,
    )


# ─── Optimization Endpoint ───────────────────────────────────────────────────

@router.post(
    "/campaigns/{campaign_id}/optimize",
    response_model=OptimizationSuggestion,
    summary="AI-optimize campaign",
    description="Generate AI-powered bid and targeting optimization suggestions for a campaign.",
)
async def optimize_campaign(
    campaign_id: UUID,
    request: OptimizationRequest | None = None,
    current_user: dict = Depends(get_current_user),
    service: AdvertisingService = Depends(_get_service),
):
    """AI optimize bids and targeting for a campaign."""
    if request is None:
        request = OptimizationRequest()

    suggestion = await service.optimize_campaign(
        org_id=current_user["org_id"],
        campaign_id=campaign_id,
        request=request,
    )
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    return suggestion


# ─── Keyword Bid Endpoints ───────────────────────────────────────────────────

@router.get(
    "/keyword-bids",
    response_model=list[KeywordBidResponse],
    summary="List keyword bids",
    description="Get current keyword bids, optionally filtered by campaign.",
)
async def list_keyword_bids(
    campaign_id: UUID | None = None,
    current_user: dict = Depends(get_current_user),
    service: AdvertisingService = Depends(_get_service),
):
    """Get current keyword bids, optionally filtered by campaign."""
    return await service.list_keyword_bids(
        org_id=current_user["org_id"],
        campaign_id=campaign_id,
    )


@router.patch(
    "/keyword-bids",
    response_model=list[KeywordBidResponse],
    summary="Bulk update keyword bids",
    description="Bulk update keyword bid amounts across campaigns.",
)
async def update_keyword_bids(
    data: KeywordBidBulkUpdate,
    current_user: dict = Depends(get_current_user),
    service: AdvertisingService = Depends(_get_service),
):
    """Bulk update keyword bids."""
    return await service.update_keyword_bids(
        org_id=current_user["org_id"],
        bulk_update=data,
    )


# ─── Creative Endpoints ──────────────────────────────────────────────────────

@router.post(
    "/creatives/generate",
    response_model=CreativeGenerateResponse,
    summary="Generate ad creatives",
    description="AI-generate ad copy and headlines from book data.",
)
async def generate_creatives(
    request: CreativeGenerateRequest,
    current_user: dict = Depends(get_current_user),
    service: AdvertisingService = Depends(_get_service),
):
    """AI generate ad copy and headlines from book data."""
    return await service.generate_creatives(
        org_id=current_user["org_id"],
        request=request,
    )


@router.get(
    "/creatives",
    response_model=list[AdCreativeResponse],
    summary="List ad creatives",
    description="List ad creatives with performance data, optionally filtered by campaign.",
)
async def list_creatives(
    campaign_id: UUID | None = None,
    current_user: dict = Depends(get_current_user),
    service: AdvertisingService = Depends(_get_service),
):
    """List ad creatives with performance data."""
    return await service.list_creatives(
        org_id=current_user["org_id"],
        campaign_id=campaign_id,
    )


# ─── Dashboard Endpoint ──────────────────────────────────────────────────────

@router.get(
    "/dashboard",
    response_model=AdDashboard,
    summary="Get ad dashboard",
    description="Get aggregate advertising performance dashboard across all campaigns.",
    responses={
        200: {"description": "Dashboard data including spend, revenue, ACOS, and trends"},
        401: {"description": "Not authenticated"},
    },
)
async def get_dashboard(
    current_user: dict = Depends(get_current_user),
    service: AdvertisingService = Depends(_get_service),
):
    """Get aggregate ad performance dashboard."""
    return await service.get_dashboard(org_id=current_user["org_id"])
