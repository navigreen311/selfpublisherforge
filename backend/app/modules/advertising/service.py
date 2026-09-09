"""Advertising Intelligence service layer.

Handles campaign CRUD, performance aggregation, optimization orchestration,
and coordination between platform clients (Amazon/Facebook), optimizer, and creative generator.
"""

import logging
import os
from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.modules.advertising.amazon_ads import AmazonAdsClient, AmazonAdsError
from app.modules.advertising.creative_generator import AdCreativeGenerator
from app.modules.advertising.facebook_ads import FacebookAdsClient, FacebookAdsError
from app.modules.advertising.models import (
    AdCreative,
    Campaign,
    CampaignPerformance,
    KeywordBid,
)
from app.modules.advertising.optimizer import (
    AdOptimizer,
    CampaignPerformanceData,
    KeywordPerformanceData,
)
from app.modules.advertising.schemas import (
    AdCreativeResponse,
    AdDashboard,
    AdPerformance,
    AdPlatform,
    CampaignCreate,
    CampaignFilter,
    CampaignResponse,
    CampaignStatus,
    CampaignUpdate,
    CampaignWithPerformance,
    CreativeGenerateRequest,
    CreativeGenerateResponse,
    FacebookCampaignCreate,
    FacebookCampaignListResponse,
    FacebookCampaignMetrics,
    FacebookCampaignResponse,
    FacebookCampaignUpdate,
    KeywordBidBulkUpdate,
    KeywordBidResponse,
    OptimizationRequest,
    OptimizationSuggestion,
    PerformanceQuery,
    PerformanceSummary,
)

logger = logging.getLogger(__name__)

DEFAULT_BID_AMOUNT = float(os.environ.get("DEFAULT_BID_AMOUNT", "0.75"))


class AdvertisingService:
    """Core service for advertising intelligence operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.optimizer = AdOptimizer()
        self.creative_generator = AdCreativeGenerator()
        self.amazon_client = AmazonAdsClient()
        self.facebook_client = FacebookAdsClient()

    # ─── Campaign CRUD ────────────────────────────────────────────────────

    async def list_campaigns(
        self,
        org_id: UUID,
        filters: CampaignFilter | None = None,
        cursor: str | None = None,
        limit: int = 20,
    ) -> tuple[list[CampaignWithPerformance], str | None, int]:
        """List campaigns for an org with optional filters and pagination.

        Returns (campaigns, next_cursor, total_count).
        """
        query = select(Campaign).where(
            and_(
                Campaign.org_id == org_id,
                Campaign.deleted_at.is_(None),
            )
        )

        if filters:
            if filters.platform:
                query = query.where(Campaign.platform == filters.platform.value)
            if filters.status:
                query = query.where(Campaign.status == filters.status.value)
            if filters.campaign_type:
                query = query.where(Campaign.campaign_type == filters.campaign_type.value)
            if filters.book_id:
                query = query.where(Campaign.book_id == filters.book_id)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total_count = total_result.scalar() or 0

        # Pagination
        query = query.order_by(Campaign.created_at.desc()).limit(limit + 1)
        if cursor:
            try:
                cursor_dt = datetime.fromisoformat(cursor)
                query = query.where(Campaign.created_at < cursor_dt)
            except ValueError:
                logger.warning("Invalid cursor value: %s", cursor)

        result = await self.db.execute(query)
        campaigns = list(result.scalars().all())

        next_cursor = None
        if len(campaigns) > limit:
            campaigns = campaigns[:limit]
            next_cursor = campaigns[-1].created_at.isoformat()

        # Attach performance summaries
        enriched = []
        for campaign in campaigns:
            summary = await self._get_performance_summary(campaign.id)
            resp = CampaignWithPerformance.model_validate(campaign)
            resp.performance_summary = summary
            enriched.append(resp)

        return enriched, next_cursor, total_count

    async def get_campaign(self, org_id: UUID, campaign_id: UUID) -> CampaignWithPerformance:
        """Get a single campaign with performance summary."""
        result = await self.db.execute(
            select(Campaign).where(
                and_(
                    Campaign.id == campaign_id,
                    Campaign.org_id == org_id,
                    Campaign.deleted_at.is_(None),
                )
            )
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise AppException(
                status_code=404,
                code="CAMPAIGN_NOT_FOUND",
                message="Campaign not found",
            )

        summary = await self._get_performance_summary(campaign.id)
        resp = CampaignWithPerformance.model_validate(campaign)
        resp.performance_summary = summary
        return resp

    async def create_campaign(self, org_id: UUID, data: CampaignCreate) -> CampaignResponse:
        """Create a new ad campaign."""
        campaign = Campaign(
            org_id=org_id,
            name=data.name,
            platform=data.platform.value,
            campaign_type=data.campaign_type.value,
            status=CampaignStatus.DRAFT.value,
            book_id=data.book_id,
            daily_budget=data.daily_budget,
            total_budget=data.total_budget,
            bid_strategy=data.bid_strategy.value,
            target_acos=data.target_acos,
            start_date=data.start_date,
            end_date=data.end_date,
            targeting_keywords=data.targeting_keywords,
            negative_keywords=data.negative_keywords,
        )
        self.db.add(campaign)
        await self.db.flush()
        await self.db.refresh(campaign)

        # Sync to external platform
        try:
            if data.platform == AdPlatform.AMAZON:
                ext_result = await self.amazon_client.create_campaign(
                    name=data.name,
                    campaign_type=data.campaign_type.value,
                    daily_budget=data.daily_budget,
                )
                campaign.external_campaign_id = ext_result.get("external_campaign_id")
            elif data.platform == AdPlatform.FACEBOOK:
                ext_result = await self.facebook_client.create_campaign(
                    name=data.name,
                    daily_budget=data.daily_budget,
                )
                campaign.external_campaign_id = ext_result.get("external_campaign_id")
            await self.db.flush()
        except (AmazonAdsError, FacebookAdsError, httpx.HTTPError, OSError) as e:
            logger.warning("Failed to sync campaign to external platform: %s", e)

        # Create keyword bids from targeting keywords
        for keyword in data.targeting_keywords:
            kw_bid = KeywordBid(
                campaign_id=campaign.id,
                keyword=keyword,
                match_type="broad",
                bid_amount=DEFAULT_BID_AMOUNT,
            )
            self.db.add(kw_bid)

        for keyword in data.negative_keywords:
            kw_bid = KeywordBid(
                campaign_id=campaign.id,
                keyword=keyword,
                match_type="exact",
                bid_amount=0.0,
                is_negative=True,
            )
            self.db.add(kw_bid)

        await self.db.flush()
        await self.db.refresh(campaign)
        return CampaignResponse.model_validate(campaign)

    async def update_campaign(
        self,
        org_id: UUID,
        campaign_id: UUID,
        data: CampaignUpdate,
    ) -> CampaignResponse:
        """Update an existing campaign."""
        result = await self.db.execute(
            select(Campaign).where(
                and_(
                    Campaign.id == campaign_id,
                    Campaign.org_id == org_id,
                    Campaign.deleted_at.is_(None),
                )
            )
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise AppException(
                status_code=404,
                code="CAMPAIGN_NOT_FOUND",
                message="Campaign not found",
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "status" and value is not None or field == "bid_strategy" and value is not None:
                setattr(campaign, field, value.value if hasattr(value, "value") else value)
            else:
                setattr(campaign, field, value)

        await self.db.flush()
        await self.db.refresh(campaign)
        return CampaignResponse.model_validate(campaign)

    # ─── Performance ──────────────────────────────────────────────────────

    async def get_campaign_performance(
        self,
        org_id: UUID,
        campaign_id: UUID,
        query: PerformanceQuery | None = None,
    ) -> list[AdPerformance]:
        """Get detailed performance records for a campaign."""
        # Verify ownership
        campaign = await self.db.execute(
            select(Campaign.id).where(
                and_(
                    Campaign.id == campaign_id,
                    Campaign.org_id == org_id,
                )
            )
        )
        if not campaign.scalar_one_or_none():
            raise AppException(
                status_code=404,
                code="CAMPAIGN_NOT_FOUND",
                message="Campaign not found",
            )

        perf_query = select(CampaignPerformance).where(CampaignPerformance.campaign_id == campaign_id)

        if query:
            if query.date_from:
                perf_query = perf_query.where(CampaignPerformance.date >= query.date_from)
            if query.date_to:
                perf_query = perf_query.where(CampaignPerformance.date <= query.date_to)

        perf_query = perf_query.order_by(CampaignPerformance.date.desc())
        result = await self.db.execute(perf_query)
        records = result.scalars().all()
        return [AdPerformance.model_validate(r) for r in records]

    async def _get_performance_summary(
        self,
        campaign_id: UUID,
        days: int = 30,
    ) -> PerformanceSummary:
        """Calculate performance summary for a campaign over a period."""
        since = datetime.now(UTC) - timedelta(days=days)
        result = await self.db.execute(
            select(
                func.sum(CampaignPerformance.impressions).label("total_impressions"),
                func.sum(CampaignPerformance.clicks).label("total_clicks"),
                func.sum(CampaignPerformance.spend).label("total_spend"),
                func.sum(CampaignPerformance.sales).label("total_sales"),
                func.sum(CampaignPerformance.orders).label("total_orders"),
                func.avg(CampaignPerformance.acos).label("avg_acos"),
                func.avg(CampaignPerformance.roas).label("avg_roas"),
                func.avg(CampaignPerformance.ctr).label("avg_ctr"),
                func.avg(CampaignPerformance.cpc).label("avg_cpc"),
                func.avg(CampaignPerformance.conversion_rate).label("avg_conversion_rate"),
                func.min(CampaignPerformance.date).label("period_start"),
                func.max(CampaignPerformance.date).label("period_end"),
            ).where(
                and_(
                    CampaignPerformance.campaign_id == campaign_id,
                    CampaignPerformance.date >= since,
                )
            )
        )
        row = result.one_or_none()
        if not row or row.total_impressions is None:
            return PerformanceSummary()

        return PerformanceSummary(
            total_impressions=row.total_impressions or 0,
            total_clicks=row.total_clicks or 0,
            total_spend=round(row.total_spend or 0, 2),
            total_sales=round(row.total_sales or 0, 2),
            total_orders=row.total_orders or 0,
            avg_acos=round(row.avg_acos or 0, 2),
            avg_roas=round(row.avg_roas or 0, 2),
            avg_ctr=round(row.avg_ctr or 0, 4),
            avg_cpc=round(row.avg_cpc or 0, 2),
            avg_conversion_rate=round(row.avg_conversion_rate or 0, 2),
            period_start=row.period_start,
            period_end=row.period_end,
        )

    # ─── Keyword Bids ────────────────────────────────────────────────────

    async def list_keyword_bids(
        self,
        org_id: UUID,
        campaign_id: UUID | None = None,
    ) -> list[KeywordBidResponse]:
        """List keyword bids, optionally filtered by campaign."""
        if campaign_id:
            # Verify ownership
            campaign = await self.db.execute(
                select(Campaign.id).where(
                    and_(
                        Campaign.id == campaign_id,
                        Campaign.org_id == org_id,
                    )
                )
            )
            if not campaign.scalar_one_or_none():
                raise AppException(
                    status_code=404,
                    code="CAMPAIGN_NOT_FOUND",
                    message="Campaign not found",
                )

            query = select(KeywordBid).where(KeywordBid.campaign_id == campaign_id)
        else:
            # All keywords across org campaigns
            campaign_ids_q = select(Campaign.id).where(Campaign.org_id == org_id)
            query = select(KeywordBid).where(KeywordBid.campaign_id.in_(campaign_ids_q))

        query = query.order_by(KeywordBid.created_at.desc())
        result = await self.db.execute(query)
        bids = result.scalars().all()
        return [KeywordBidResponse.model_validate(b) for b in bids]

    async def update_keyword_bids(
        self,
        org_id: UUID,
        bulk_update: KeywordBidBulkUpdate,
    ) -> list[KeywordBidResponse]:
        """Bulk update keyword bids."""
        updated_bids = []
        for item in bulk_update.updates:
            bid_id = item.get("id")
            new_amount = item.get("bid_amount")
            if not bid_id or not new_amount:
                continue

            # Ensure bid_id is a UUID object for proper SQLAlchemy binding
            if isinstance(bid_id, str):
                bid_id = UUID(bid_id)

            result = await self.db.execute(
                select(KeywordBid)
                .join(Campaign)
                .where(
                    and_(
                        KeywordBid.id == bid_id,
                        Campaign.org_id == org_id,
                    )
                )
            )
            bid = result.scalar_one_or_none()
            if bid:
                bid.bid_amount = new_amount
                await self.db.flush()
                await self.db.refresh(bid)
                updated_bids.append(KeywordBidResponse.model_validate(bid))

        return updated_bids

    # ─── Ad Creatives ────────────────────────────────────────────────────

    async def list_creatives(
        self,
        org_id: UUID,
        campaign_id: UUID | None = None,
    ) -> list[AdCreativeResponse]:
        """List ad creatives for an org, optionally filtered by campaign."""
        query = select(AdCreative).where(
            and_(
                AdCreative.org_id == org_id,
                AdCreative.deleted_at.is_(None),
            )
        )
        if campaign_id:
            query = query.where(AdCreative.campaign_id == campaign_id)

        query = query.order_by(AdCreative.created_at.desc())
        result = await self.db.execute(query)
        creatives = result.scalars().all()
        return [AdCreativeResponse.model_validate(c) for c in creatives]

    async def generate_creatives(
        self,
        org_id: UUID,
        request: CreativeGenerateRequest,
    ) -> CreativeGenerateResponse:
        """Generate ad creatives using AI and optionally save them."""
        response = await self.creative_generator.generate_creatives(request)

        # Save generated creatives to database
        for variation in response.variations:
            creative = AdCreative(
                org_id=org_id,
                book_id=request.book_id,
                headline=variation.headline,
                body_text=variation.body_text,
                call_to_action=variation.call_to_action,
                status="draft",
            )
            self.db.add(creative)

        await self.db.flush()
        return response

    # ─── Optimization ────────────────────────────────────────────────────

    async def optimize_campaign(
        self,
        org_id: UUID,
        campaign_id: UUID,
        request: OptimizationRequest,
    ) -> OptimizationSuggestion:
        """Run AI optimization on a campaign."""
        # Get campaign
        result = await self.db.execute(
            select(Campaign).where(
                and_(
                    Campaign.id == campaign_id,
                    Campaign.org_id == org_id,
                    Campaign.deleted_at.is_(None),
                )
            )
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise AppException(
                status_code=404,
                code="CAMPAIGN_NOT_FOUND",
                message="Campaign not found",
            )

        # Get keyword performance data
        kw_result = await self.db.execute(
            select(KeywordBid).where(
                and_(
                    KeywordBid.campaign_id == campaign_id,
                    KeywordBid.is_active.is_(True),
                    KeywordBid.is_negative.is_(False),
                )
            )
        )
        keywords = kw_result.scalars().all()

        # Build performance data for optimizer
        kw_perf_data = []
        for kw in keywords:
            kw_perf_data.append(
                KeywordPerformanceData(
                    keyword_bid_id=kw.id,
                    keyword=kw.keyword,
                    current_bid=kw.bid_amount,
                    impressions=kw.impressions,
                    clicks=kw.clicks,
                    spend=kw.spend,
                    sales=kw.sales,
                    acos=kw.acos,
                    days_of_data=request.min_data_points,  # Assume sufficient data for now
                )
            )

        # Get campaign-level ACOS
        summary = await self._get_performance_summary(campaign_id)

        campaign_data = CampaignPerformanceData(
            campaign_id=campaign_id,
            campaign_name=campaign.name,
            current_acos=summary.avg_acos,
            total_spend=summary.total_spend,
            total_sales=summary.total_sales,
            total_impressions=summary.total_impressions,
            total_clicks=summary.total_clicks,
            keywords=kw_perf_data,
        )

        # Use target ACOS from request or campaign setting
        if request.target_acos is None and campaign.target_acos:
            request.target_acos = campaign.target_acos

        return self.optimizer.optimize_campaign(campaign_data, request)

    # ─── Dashboard ───────────────────────────────────────────────────────

    async def get_dashboard(self, org_id: UUID) -> AdDashboard:
        """Get aggregate ad performance dashboard for an org."""
        # Active campaigns count
        active_count_result = await self.db.execute(
            select(func.count()).where(
                and_(
                    Campaign.org_id == org_id,
                    Campaign.status == CampaignStatus.ACTIVE.value,
                    Campaign.deleted_at.is_(None),
                )
            )
        )
        total_active = active_count_result.scalar() or 0

        # Today's spend
        today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        today_spend_result = await self.db.execute(
            select(func.sum(CampaignPerformance.spend))
            .join(Campaign)
            .where(
                and_(
                    Campaign.org_id == org_id,
                    CampaignPerformance.date >= today,
                )
            )
        )
        total_spend_today = today_spend_result.scalar() or 0.0

        # This month's spend and sales
        month_start = today.replace(day=1)
        month_result = await self.db.execute(
            select(
                func.sum(CampaignPerformance.spend).label("spend"),
                func.sum(CampaignPerformance.sales).label("sales"),
            )
            .join(Campaign)
            .where(
                and_(
                    Campaign.org_id == org_id,
                    CampaignPerformance.date >= month_start,
                )
            )
        )
        month_row = month_result.one_or_none()
        total_spend_month = round(month_row.spend or 0, 2) if month_row else 0.0
        total_sales_month = round(month_row.sales or 0, 2) if month_row else 0.0

        # Overall ACOS and ROAS
        overall_acos = self.optimizer.calculate_acos(total_spend_month, total_sales_month)
        overall_roas = self.optimizer.calculate_roas(total_spend_month, total_sales_month)

        # Top campaigns
        top_campaigns_result = await self.db.execute(
            select(Campaign)
            .where(
                and_(
                    Campaign.org_id == org_id,
                    Campaign.status == CampaignStatus.ACTIVE.value,
                    Campaign.deleted_at.is_(None),
                )
            )
            .order_by(Campaign.created_at.desc())
            .limit(5)
        )
        top_campaigns = []
        for campaign in top_campaigns_result.scalars().all():
            summary = await self._get_performance_summary(campaign.id)
            resp = CampaignWithPerformance.model_validate(campaign)
            resp.performance_summary = summary
            top_campaigns.append(resp)

        # Platform breakdown
        platform_breakdown = {}
        for platform in [AdPlatform.AMAZON, AdPlatform.FACEBOOK]:
            platform_campaigns = await self.db.execute(
                select(Campaign.id).where(
                    and_(
                        Campaign.org_id == org_id,
                        Campaign.platform == platform.value,
                        Campaign.deleted_at.is_(None),
                    )
                )
            )
            camp_ids = list(platform_campaigns.scalars().all())
            if camp_ids:
                platform_perf = await self.db.execute(
                    select(
                        func.sum(CampaignPerformance.impressions).label("total_impressions"),
                        func.sum(CampaignPerformance.clicks).label("total_clicks"),
                        func.sum(CampaignPerformance.spend).label("total_spend"),
                        func.sum(CampaignPerformance.sales).label("total_sales"),
                        func.sum(CampaignPerformance.orders).label("total_orders"),
                        func.avg(CampaignPerformance.acos).label("avg_acos"),
                        func.avg(CampaignPerformance.roas).label("avg_roas"),
                        func.avg(CampaignPerformance.ctr).label("avg_ctr"),
                        func.avg(CampaignPerformance.cpc).label("avg_cpc"),
                        func.avg(CampaignPerformance.conversion_rate).label("avg_conversion_rate"),
                    ).where(
                        and_(
                            CampaignPerformance.campaign_id.in_(camp_ids),
                            CampaignPerformance.date >= month_start,
                        )
                    )
                )
                row = platform_perf.one_or_none()
                if row and row.total_impressions is not None:
                    platform_breakdown[platform.value] = PerformanceSummary(
                        total_impressions=row.total_impressions or 0,
                        total_clicks=row.total_clicks or 0,
                        total_spend=round(row.total_spend or 0, 2),
                        total_sales=round(row.total_sales or 0, 2),
                        total_orders=row.total_orders or 0,
                        avg_acos=round(row.avg_acos or 0, 2),
                        avg_roas=round(row.avg_roas or 0, 2),
                        avg_ctr=round(row.avg_ctr or 0, 4),
                        avg_cpc=round(row.avg_cpc or 0, 2),
                        avg_conversion_rate=round(row.avg_conversion_rate or 0, 2),
                    )

        return AdDashboard(
            total_active_campaigns=total_active,
            total_spend_today=round(total_spend_today, 2),
            total_spend_month=total_spend_month,
            total_sales_month=total_sales_month,
            overall_acos=overall_acos,
            overall_roas=overall_roas,
            top_campaigns=top_campaigns,
            platform_breakdown=platform_breakdown,
        )

    # ─── Facebook Ads ────────────────────────────────────────────────────

    async def facebook_create_campaign(
        self,
        org_id: UUID,
        data: FacebookCampaignCreate,
    ) -> FacebookCampaignResponse:
        """Create a Facebook Ads campaign via the Graph API.

        Delegates to the FacebookAdsClient and returns the external campaign
        details.  The caller (router) is responsible for HTTP error mapping.
        """
        result = await self.facebook_client.create_campaign(
            name=data.name,
            objective=data.objective.value,
            daily_budget=data.daily_budget,
            status=data.status.value,
        )
        return FacebookCampaignResponse(
            external_campaign_id=result.get("external_campaign_id", ""),
            name=data.name,
            objective=data.objective.value,
            status=result.get("status", data.status.value),
            daily_budget=data.daily_budget,
            created=result.get("created", False),
        )

    async def facebook_list_campaigns(
        self,
        org_id: UUID,
        limit: int = 50,
        status_filter: str | None = None,
    ) -> FacebookCampaignListResponse:
        """List Facebook Ads campaigns for the configured ad account."""
        result = await self.facebook_client.list_campaigns(
            limit=limit,
            status_filter=status_filter,
        )
        campaigns = [FacebookCampaignResponse(**c) for c in result.get("campaigns", [])]
        return FacebookCampaignListResponse(
            campaigns=campaigns,
            total_count=result.get("total_count", len(campaigns)),
        )

    async def facebook_get_campaign(
        self,
        org_id: UUID,
        external_campaign_id: str,
    ) -> FacebookCampaignResponse:
        """Get details for a single Facebook Ads campaign."""
        result = await self.facebook_client.get_campaign(external_campaign_id)
        return FacebookCampaignResponse(
            external_campaign_id=result.get("external_campaign_id", ""),
            name=result.get("name"),
            objective=result.get("objective"),
            status=result.get("status"),
            daily_budget=result.get("daily_budget"),
        )

    async def facebook_update_campaign(
        self,
        org_id: UUID,
        external_campaign_id: str,
        data: FacebookCampaignUpdate,
    ) -> FacebookCampaignResponse:
        """Update an existing Facebook Ads campaign."""
        updates = data.model_dump(exclude_unset=True)
        # Convert enum values to strings for the client
        if "status" in updates and updates["status"] is not None:
            updates["status"] = updates["status"].value if hasattr(updates["status"], "value") else updates["status"]

        result = await self.facebook_client.update_campaign(
            external_campaign_id=external_campaign_id,
            updates=updates,
        )
        return FacebookCampaignResponse(
            external_campaign_id=result.get("external_campaign_id", ""),
            updated=result.get("updated", False),
            changes=result.get("changes"),
        )

    async def facebook_pause_campaign(
        self,
        org_id: UUID,
        external_campaign_id: str,
    ) -> FacebookCampaignResponse:
        """Pause a Facebook Ads campaign."""
        result = await self.facebook_client.pause_campaign(external_campaign_id)
        return FacebookCampaignResponse(
            external_campaign_id=result.get("external_campaign_id", ""),
            status="paused",
            updated=result.get("updated", False),
            changes=result.get("changes"),
        )

    async def facebook_get_campaign_metrics(
        self,
        org_id: UUID,
        external_campaign_id: str,
        start_date: str,
        end_date: str,
    ) -> FacebookCampaignMetrics:
        """Get performance metrics for a Facebook Ads campaign."""
        result = await self.facebook_client.get_campaign_insights(
            external_campaign_id=external_campaign_id,
            start_date=start_date,
            end_date=end_date,
        )
        return FacebookCampaignMetrics(
            external_campaign_id=result.get("external_campaign_id", ""),
            start_date=result.get("start_date", start_date),
            end_date=result.get("end_date", end_date),
            metrics=result.get("metrics", {}),
            report_status=result.get("report_status", "completed"),
        )
