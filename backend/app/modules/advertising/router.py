"""FastAPI router for Advertising Intelligence endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

logger = logging.getLogger(__name__)

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
    FacebookCampaignCreate,
    FacebookCampaignUpdate,
    FacebookCampaignResponse,
    FacebookCampaignListResponse,
    FacebookCampaignMetrics,
)
from app.modules.advertising.facebook_ads import FacebookAdsError

try:
    from app.modules.advertising.facebook_ads import FacebookAdsClient
    _facebook_client = FacebookAdsClient()
except (ImportError, ModuleNotFoundError) as e:
    logger.warning("Facebook Ads client not available: %s", e)
    _facebook_client = None

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


# ─── Facebook Ads Endpoints ─────────────────────────────────────────────────

@router.post(
    "/facebook/campaigns",
    response_model=FacebookCampaignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Facebook ad campaign",
    description="Create a new advertising campaign on Facebook via the Marketing API.",
)
async def create_facebook_campaign(
    data: FacebookCampaignCreate,
    current_user: dict = Depends(get_current_user),
    service: AdvertisingService = Depends(_get_service),
):
    """Create a Facebook Ads campaign."""
    try:
        return await service.facebook_create_campaign(
            org_id=current_user["org_id"],
            data=data,
        )
    except FacebookAdsError as exc:
        raise HTTPException(
            status_code=exc.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )


@router.get(
    "/facebook/campaigns",
    response_model=FacebookCampaignListResponse,
    summary="List Facebook campaigns",
    description="List Facebook Ads campaigns for the configured ad account.",
)
async def list_facebook_campaigns(
    limit: int = Query(50, ge=1, le=200),
    status_filter: str | None = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user),
    service: AdvertisingService = Depends(_get_service),
):
    """List Facebook Ads campaigns."""
    try:
        return await service.facebook_list_campaigns(
            org_id=current_user["org_id"],
            limit=limit,
            status_filter=status_filter,
        )
    except FacebookAdsError as exc:
        raise HTTPException(
            status_code=exc.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )


@router.get(
    "/facebook/campaigns/{campaign_id}",
    response_model=FacebookCampaignResponse,
    summary="Get Facebook campaign details",
    description="Get details for a single Facebook Ads campaign by its external ID.",
)
async def get_facebook_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    service: AdvertisingService = Depends(_get_service),
):
    """Get a single Facebook Ads campaign."""
    try:
        return await service.facebook_get_campaign(
            org_id=current_user["org_id"],
            external_campaign_id=campaign_id,
        )
    except FacebookAdsError as exc:
        status_code = exc.status_code or status.HTTP_502_BAD_GATEWAY
        if status_code == 404 or (exc.fb_error and exc.fb_error.get("code") == 100):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facebook campaign not found",
            )
        raise HTTPException(status_code=status_code, detail=str(exc))


@router.patch(
    "/facebook/campaigns/{campaign_id}",
    response_model=FacebookCampaignResponse,
    summary="Update Facebook campaign",
    description="Update an existing Facebook Ads campaign's name, status, or budget.",
)
async def update_facebook_campaign(
    campaign_id: str,
    data: FacebookCampaignUpdate,
    current_user: dict = Depends(get_current_user),
    service: AdvertisingService = Depends(_get_service),
):
    """Update a Facebook Ads campaign."""
    try:
        return await service.facebook_update_campaign(
            org_id=current_user["org_id"],
            external_campaign_id=campaign_id,
            data=data,
        )
    except FacebookAdsError as exc:
        status_code = exc.status_code or status.HTTP_502_BAD_GATEWAY
        if status_code == 404 or (exc.fb_error and exc.fb_error.get("code") == 100):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facebook campaign not found",
            )
        raise HTTPException(status_code=status_code, detail=str(exc))


@router.post(
    "/facebook/campaigns/{campaign_id}/pause",
    response_model=FacebookCampaignResponse,
    summary="Pause Facebook campaign",
    description="Pause an active Facebook Ads campaign.",
)
async def pause_facebook_campaign(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
    service: AdvertisingService = Depends(_get_service),
):
    """Pause a Facebook Ads campaign."""
    try:
        return await service.facebook_pause_campaign(
            org_id=current_user["org_id"],
            external_campaign_id=campaign_id,
        )
    except FacebookAdsError as exc:
        status_code = exc.status_code or status.HTTP_502_BAD_GATEWAY
        if status_code == 404 or (exc.fb_error and exc.fb_error.get("code") == 100):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facebook campaign not found",
            )
        raise HTTPException(status_code=status_code, detail=str(exc))


@router.get(
    "/facebook/campaigns/{campaign_id}/metrics",
    response_model=FacebookCampaignMetrics,
    summary="Get Facebook campaign metrics",
    description="Get performance metrics (impressions, clicks, spend, CTR, CPC, etc.) for a Facebook campaign.",
)
async def get_facebook_campaign_metrics(
    campaign_id: str,
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    current_user: dict = Depends(get_current_user),
    service: AdvertisingService = Depends(_get_service),
):
    """Get performance metrics for a Facebook Ads campaign."""
    # Validate date format
    from datetime import datetime as dt
    for label, value in [("start_date", start_date), ("end_date", end_date)]:
        try:
            dt.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {label} format. Use YYYY-MM-DD.",
            )

    try:
        return await service.facebook_get_campaign_metrics(
            org_id=current_user["org_id"],
            external_campaign_id=campaign_id,
            start_date=start_date,
            end_date=end_date,
        )
    except FacebookAdsError as exc:
        status_code = exc.status_code or status.HTTP_502_BAD_GATEWAY
        if status_code == 404 or (exc.fb_error and exc.fb_error.get("code") == 100):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facebook campaign not found",
            )
        raise HTTPException(status_code=status_code, detail=str(exc))


@router.put(
    "/facebook/campaigns/{campaign_id}",
    response_model=FacebookCampaignResponse,
    summary="Update Facebook campaign (PUT)",
    description="Update an existing Facebook Ads campaign's name, status, or budget using PUT.",
)
async def put_facebook_campaign(
    campaign_id: str,
    data: FacebookCampaignUpdate,
    current_user: dict = Depends(get_current_user),
    service: AdvertisingService = Depends(_get_service),
):
    """Update a Facebook Ads campaign via PUT."""
    try:
        return await service.facebook_update_campaign(
            org_id=current_user["org_id"],
            external_campaign_id=campaign_id,
            data=data,
        )
    except FacebookAdsError as exc:
        status_code = exc.status_code or status.HTTP_502_BAD_GATEWAY
        if status_code == 404 or (exc.fb_error and exc.fb_error.get("code") == 100):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facebook campaign not found",
            )
        raise HTTPException(status_code=status_code, detail=str(exc))


@router.get(
    "/facebook/campaigns/{campaign_id}/insights",
    response_model=FacebookCampaignMetrics,
    summary="Get Facebook campaign insights",
    description="Get performance insights (impressions, clicks, spend, CTR, CPC, etc.) for a Facebook campaign.",
)
async def get_facebook_campaign_insights(
    campaign_id: str,
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    current_user: dict = Depends(get_current_user),
    service: AdvertisingService = Depends(_get_service),
):
    """Get performance insights for a Facebook Ads campaign."""
    from datetime import datetime as dt

    for label, value in [("start_date", start_date), ("end_date", end_date)]:
        try:
            dt.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {label} format. Use YYYY-MM-DD.",
            )

    try:
        return await service.facebook_get_campaign_metrics(
            org_id=current_user["org_id"],
            external_campaign_id=campaign_id,
            start_date=start_date,
            end_date=end_date,
        )
    except FacebookAdsError as exc:
        status_code = exc.status_code or status.HTTP_502_BAD_GATEWAY
        if status_code == 404 or (exc.fb_error and exc.fb_error.get("code") == 100):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facebook campaign not found",
            )
        raise HTTPException(status_code=status_code, detail=str(exc))


class FacebookAudienceCreate(BaseModel):
    """Request body for creating a Facebook custom audience."""

    name: str = Field(..., min_length=1, max_length=255, description="Audience name")
    description: str = Field("", max_length=1000, description="Audience description")
    source_type: str = Field(
        "CUSTOM",
        description="Audience source type (CUSTOM, WEBSITE, APP, OFFLINE, ENGAGEMENT)",
    )


class FacebookAudienceResponse(BaseModel):
    """Response body for a created Facebook custom audience."""

    audience_id: str
    name: str
    source_type: str
    created: bool = True


@router.post(
    "/facebook/audiences",
    response_model=FacebookAudienceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Facebook custom audience",
    description="Create a custom audience on Facebook for ad targeting.",
)
async def create_facebook_audience(
    data: FacebookAudienceCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a Facebook custom audience."""
    if _facebook_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Facebook Ads client is not available. Check credentials configuration.",
        )

    try:
        result = await _facebook_client.create_custom_audience(
            name=data.name,
            description=data.description,
            source_type=data.source_type,
        )
        return result
    except FacebookAdsError as exc:
        raise HTTPException(
            status_code=exc.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )
