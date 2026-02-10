"""Celery tasks for Advertising Intelligence.

Handles:
- Periodic performance sync from ad platforms
- Auto-optimize bids based on ACOS targets
- Budget alerts when thresholds are exceeded
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID

from app.tasks import celery_app
from app.database import async_session
from app.modules.advertising.models import Campaign, CampaignPerformance, KeywordBid
from app.modules.advertising.schemas import CampaignStatus, OptimizationRequest
from app.modules.advertising.service import AdvertisingService
from app.modules.advertising.amazon_ads import AmazonAdsClient
from app.modules.advertising.facebook_ads import FacebookAdsClient
from app.modules.advertising.optimizer import AdOptimizer

from sqlalchemy import select, and_

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Helper to run async code in Celery sync tasks."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="advertising.sync_performance", bind=True, max_retries=3)
def sync_campaign_performance(self, campaign_id: str | None = None):
    """Sync performance data from ad platforms for campaigns.

    If campaign_id is provided, syncs only that campaign.
    Otherwise, syncs all active campaigns.
    """
    logger.info(f"Starting performance sync (campaign_id={campaign_id})")
    _run_async(_sync_performance_async(campaign_id))
    logger.info("Performance sync completed")


async def _sync_performance_async(campaign_id: str | None = None):
    """Async implementation of performance sync."""
    amazon_client = AmazonAdsClient()
    facebook_client = FacebookAdsClient()

    async with async_session() as db:
        try:
            if campaign_id:
                query = select(Campaign).where(Campaign.id == campaign_id)
            else:
                query = select(Campaign).where(
                    and_(
                        Campaign.status == CampaignStatus.ACTIVE.value,
                        Campaign.deleted_at.is_(None),
                        Campaign.external_campaign_id.isnot(None),
                    )
                )

            result = await db.execute(query)
            campaigns = result.scalars().all()

            now = datetime.now(timezone.utc)
            yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
            today = now.strftime("%Y-%m-%d")

            for campaign in campaigns:
                try:
                    if campaign.platform == "amazon" and campaign.external_campaign_id:
                        report = await amazon_client.get_campaign_report(
                            external_campaign_id=campaign.external_campaign_id,
                            start_date=yesterday,
                            end_date=today,
                        )
                        metrics = report.get("metrics", {})
                    elif campaign.platform == "facebook" and campaign.external_campaign_id:
                        report = await facebook_client.get_campaign_insights(
                            external_campaign_id=campaign.external_campaign_id,
                            start_date=yesterday,
                            end_date=today,
                        )
                        metrics = report.get("metrics", {})
                    else:
                        continue

                    # Upsert performance record
                    perf = CampaignPerformance(
                        campaign_id=campaign.id,
                        date=now,
                        impressions=int(metrics.get("impressions", 0)),
                        clicks=int(metrics.get("clicks", 0)),
                        spend=float(metrics.get("cost", metrics.get("spend", 0))),
                        sales=float(metrics.get("sales", 0)),
                        orders=int(metrics.get("orders", 0)),
                        acos=float(metrics.get("acos", 0)),
                        roas=float(metrics.get("roas", 0)),
                        ctr=float(metrics.get("ctr", 0)),
                        cpc=float(metrics.get("cpc", 0)),
                    )
                    db.add(perf)
                    logger.info(f"Synced performance for campaign {campaign.id}")

                except Exception as e:
                    logger.error(
                        f"Failed to sync performance for campaign {campaign.id}: {e}"
                    )

            await db.commit()

        except Exception as e:
            await db.rollback()
            logger.error(f"Performance sync failed: {e}")
            raise


@celery_app.task(name="advertising.auto_optimize", bind=True, max_retries=3)
def auto_optimize_bids(self):
    """Automatically optimize bids for campaigns with ACOS targets.

    Runs periodically to adjust keyword bids based on performance data.
    Only processes campaigns that have:
    - Active status
    - A target ACOS set
    - Sufficient performance data (7+ days)
    """
    logger.info("Starting auto bid optimization")
    _run_async(_auto_optimize_async())
    logger.info("Auto bid optimization completed")


async def _auto_optimize_async():
    """Async implementation of auto bid optimization."""
    optimizer = AdOptimizer()

    async with async_session() as db:
        try:
            # Find campaigns eligible for optimization
            result = await db.execute(
                select(Campaign).where(
                    and_(
                        Campaign.status == CampaignStatus.ACTIVE.value,
                        Campaign.deleted_at.is_(None),
                        Campaign.target_acos.isnot(None),
                        Campaign.bid_strategy != "manual",
                    )
                )
            )
            campaigns = result.scalars().all()

            for campaign in campaigns:
                try:
                    service = AdvertisingService(db)
                    request = OptimizationRequest(
                        target_acos=campaign.target_acos,
                        min_data_points=7,
                    )
                    suggestion = await service.optimize_campaign(
                        org_id=campaign.org_id,
                        campaign_id=campaign.id,
                        request=request,
                    )

                    if suggestion and suggestion.bid_adjustments:
                        # Apply bid adjustments automatically
                        for adj in suggestion.bid_adjustments:
                            kw_result = await db.execute(
                                select(KeywordBid).where(
                                    KeywordBid.id == adj.keyword_bid_id
                                )
                            )
                            kw = kw_result.scalar_one_or_none()
                            if kw:
                                kw.bid_amount = adj.suggested_bid
                                logger.info(
                                    f"Auto-adjusted bid for '{kw.keyword}': "
                                    f"${adj.current_bid:.2f} -> ${adj.suggested_bid:.2f}"
                                )

                        # Apply negative keywords
                        for neg_kw in suggestion.keywords_to_negate:
                            neg_bid = KeywordBid(
                                campaign_id=campaign.id,
                                keyword=neg_kw,
                                match_type="exact",
                                bid_amount=0.0,
                                is_negative=True,
                            )
                            db.add(neg_bid)

                        logger.info(
                            f"Campaign {campaign.id}: {len(suggestion.bid_adjustments)} adjustments, "
                            f"{len(suggestion.keywords_to_negate)} negations"
                        )

                except Exception as e:
                    logger.error(
                        f"Failed to optimize campaign {campaign.id}: {e}"
                    )

            await db.commit()

        except Exception as e:
            await db.rollback()
            logger.error(f"Auto optimization failed: {e}")
            raise


@celery_app.task(name="advertising.budget_alerts", bind=True, max_retries=3)
def check_budget_alerts(self):
    """Check for campaigns approaching budget limits and send alerts.

    Sends alerts when:
    - Daily spend exceeds 80% of daily budget
    - Total spend exceeds 80% of total budget
    - ACOS exceeds target by more than 50%
    """
    logger.info("Checking budget alerts")
    _run_async(_check_budget_alerts_async())
    logger.info("Budget alert check completed")


async def _check_budget_alerts_async():
    """Async implementation of budget alert checking."""
    async with async_session() as db:
        try:
            result = await db.execute(
                select(Campaign).where(
                    and_(
                        Campaign.status == CampaignStatus.ACTIVE.value,
                        Campaign.deleted_at.is_(None),
                    )
                )
            )
            campaigns = result.scalars().all()
            alerts = []

            for campaign in campaigns:
                service = AdvertisingService(db)
                summary = await service._get_performance_summary(campaign.id, days=1)

                # Check daily budget
                if summary.total_spend > campaign.daily_budget * 0.8:
                    pct = round(summary.total_spend / campaign.daily_budget * 100, 1) if campaign.daily_budget > 0 else 0
                    alerts.append({
                        "campaign_id": str(campaign.id),
                        "campaign_name": campaign.name,
                        "alert_type": "daily_budget",
                        "message": (
                            f"Campaign '{campaign.name}' has spent {pct}% "
                            f"of its daily budget (${summary.total_spend:.2f} / "
                            f"${campaign.daily_budget:.2f})"
                        ),
                    })

                # Check total budget
                if campaign.total_budget:
                    total_summary = await service._get_performance_summary(
                        campaign.id, days=365
                    )
                    if total_summary.total_spend > campaign.total_budget * 0.8:
                        pct = round(total_summary.total_spend / campaign.total_budget * 100, 1)
                        alerts.append({
                            "campaign_id": str(campaign.id),
                            "campaign_name": campaign.name,
                            "alert_type": "total_budget",
                            "message": (
                                f"Campaign '{campaign.name}' has spent {pct}% "
                                f"of its total budget"
                            ),
                        })

                # Check ACOS target
                if campaign.target_acos and summary.avg_acos > campaign.target_acos * 1.5:
                    alerts.append({
                        "campaign_id": str(campaign.id),
                        "campaign_name": campaign.name,
                        "alert_type": "acos_exceeded",
                        "message": (
                            f"Campaign '{campaign.name}' ACOS ({summary.avg_acos:.1f}%) "
                            f"significantly exceeds target ({campaign.target_acos:.1f}%)"
                        ),
                    })

            if alerts:
                logger.warning(f"Generated {len(alerts)} budget alerts: {alerts}")
                # In production, publish these as events via EventPublisher
                # or send notifications via the notifications module

        except Exception as e:
            logger.error(f"Budget alert check failed: {e}")
            raise


# ─── Periodic Task Schedule ──────────────────────────────────────────────────

celery_app.conf.beat_schedule = celery_app.conf.get("beat_schedule", {})
celery_app.conf.beat_schedule.update({
    "sync-ad-performance-hourly": {
        "task": "advertising.sync_performance",
        "schedule": 3600.0,  # Every hour
    },
    "auto-optimize-bids-daily": {
        "task": "advertising.auto_optimize",
        "schedule": 86400.0,  # Every 24 hours
    },
    "check-budget-alerts-every-4h": {
        "task": "advertising.budget_alerts",
        "schedule": 14400.0,  # Every 4 hours
    },
})
