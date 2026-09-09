"""Celery tasks for Advertising Intelligence.

Handles:
- Periodic performance sync from ad platforms
- Auto-optimize bids based on ACOS targets
- Budget alerts when thresholds are exceeded

Time limit strategy
-------------------
Each task declares explicit ``soft_time_limit`` and ``time_limit`` values
(in seconds) based on expected workload:
  - Quick   (notifications, status updates):   soft=60,   hard=120
  - Medium  (API calls, data sync):            soft=300,  hard=600
  - Long    (bulk imports, report generation):  soft=1800, hard=3600
  - V. Long (full analytics aggregation):       soft=3300, hard=3600
Global defaults in config.py are 3300/3600 but per-task limits take precedence.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError

from app.database import async_session
from app.models.user import User, UserRole
from app.modules.advertising.amazon_ads import AmazonAdsClient
from app.modules.advertising.facebook_ads import FacebookAdsClient
from app.modules.advertising.models import Campaign, CampaignPerformance, KeywordBid
from app.modules.advertising.optimizer import AdOptimizer
from app.modules.advertising.schemas import CampaignStatus, OptimizationRequest
from app.modules.advertising.service import AdvertisingService
from app.modules.notifications.models import NotificationType
from app.modules.notifications.schemas import CreateNotification
from app.modules.notifications.service import create_notification
from app.tasks import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Helper to run async code in Celery sync tasks."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="app.tasks.advertising.sync_performance", bind=True, max_retries=3, soft_time_limit=300, time_limit=600
)
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

            now = datetime.now(UTC)
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
                    await db.flush()
                    logger.info(f"Synced performance for campaign {campaign.id}")

                except (ValueError, KeyError, TypeError) as e:
                    logger.error(f"Failed to parse performance data for campaign {campaign.id}: {e}")
                except SQLAlchemyError as e:
                    logger.error(f"Database error syncing campaign {campaign.id}: {e}")

            await db.commit()

        except SoftTimeLimitExceeded:
            await db.rollback()
            logger.warning("sync_campaign_performance hit soft time limit, cleaning up")
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Performance sync failed: {e}")
            raise


@celery_app.task(
    name="app.tasks.advertising.auto_optimize", bind=True, max_retries=3, soft_time_limit=300, time_limit=600
)
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
                            kw_result = await db.execute(select(KeywordBid).where(KeywordBid.id == adj.keyword_bid_id))
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

                except (ValueError, KeyError, TypeError) as e:
                    logger.error(f"Failed to optimize campaign {campaign.id} (data error): {e}")
                except SQLAlchemyError as e:
                    logger.error(f"Failed to optimize campaign {campaign.id} (db error): {e}")

            await db.commit()

        except SoftTimeLimitExceeded:
            await db.rollback()
            logger.warning("auto_optimize_bids hit soft time limit, cleaning up")
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Auto optimization failed: {e}")
            raise


@celery_app.task(
    name="app.tasks.advertising.budget_alerts", bind=True, max_retries=3, soft_time_limit=300, time_limit=600
)
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
                    pct = (
                        round(summary.total_spend / campaign.daily_budget * 100, 1) if campaign.daily_budget > 0 else 0
                    )
                    alerts.append(
                        {
                            "campaign_id": str(campaign.id),
                            "campaign_name": campaign.name,
                            "alert_type": "daily_budget",
                            "message": (
                                f"Campaign '{campaign.name}' has spent {pct}% "
                                f"of its daily budget (${summary.total_spend:.2f} / "
                                f"${campaign.daily_budget:.2f})"
                            ),
                        }
                    )

                # Check total budget
                if campaign.total_budget:
                    total_summary = await service._get_performance_summary(campaign.id, days=365)
                    if total_summary.total_spend > campaign.total_budget * 0.8:
                        pct = round(total_summary.total_spend / campaign.total_budget * 100, 1)
                        alerts.append(
                            {
                                "campaign_id": str(campaign.id),
                                "campaign_name": campaign.name,
                                "alert_type": "total_budget",
                                "message": (f"Campaign '{campaign.name}' has spent {pct}% " f"of its total budget"),
                            }
                        )

                # Check ACOS target
                if campaign.target_acos and summary.avg_acos > campaign.target_acos * 1.5:
                    alerts.append(
                        {
                            "campaign_id": str(campaign.id),
                            "campaign_name": campaign.name,
                            "alert_type": "acos_exceeded",
                            "message": (
                                f"Campaign '{campaign.name}' ACOS ({summary.avg_acos:.1f}%) "
                                f"significantly exceeds target ({campaign.target_acos:.1f}%)"
                            ),
                        }
                    )

            if alerts:
                logger.warning(f"Generated {len(alerts)} budget alerts")

                # Deliver in-app notifications to org owners/admins
                for alert in alerts:
                    campaign_id_val = alert["campaign_id"]
                    # Find the campaign to get org_id
                    campaign_result = await db.execute(select(Campaign).where(Campaign.id == campaign_id_val))
                    alert_campaign = campaign_result.scalar_one_or_none()
                    if not alert_campaign:
                        continue

                    # Find org owners and admins to notify
                    user_result = await db.execute(
                        select(User).where(
                            and_(
                                User.org_id == alert_campaign.org_id,
                                User.role.in_([UserRole.OWNER, UserRole.ADMIN]),
                                User.is_active.is_(True),
                                User.deleted_at.is_(None),
                            )
                        )
                    )
                    recipients = user_result.scalars().all()

                    for user in recipients:
                        try:
                            await create_notification(
                                db,
                                CreateNotification(
                                    user_id=user.id,
                                    org_id=alert_campaign.org_id,
                                    type=NotificationType.WARNING,
                                    title=f"Budget Alert: {alert['campaign_name']}",
                                    message=alert["message"],
                                    data={
                                        "campaign_id": alert["campaign_id"],
                                        "alert_type": alert["alert_type"],
                                    },
                                ),
                            )
                        except SQLAlchemyError as e:
                            logger.error(
                                f"Failed to create notification for user {user.id}, "
                                f"alert {alert['alert_type']}: {e}"
                            )

                await db.commit()

        except SoftTimeLimitExceeded:
            await db.rollback()
            logger.warning("check_budget_alerts hit soft time limit, cleaning up")
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Budget alert check failed: {e}")
            raise


# ─── Periodic Task Schedule ──────────────────────────────────────────────────
# Beat schedules are registered centrally in app.tasks.scheduler.CELERY_BEAT_SCHEDULE

ADVERTISING_BEAT_SCHEDULE = {
    "sync-campaign-performance-hourly": {
        "task": "app.tasks.advertising.sync_performance",
        "schedule": 3600.0,  # Every hour
    },
    "auto-optimize-bids-daily": {
        "task": "app.tasks.advertising.auto_optimize",
        "schedule": 86400.0,  # Every 24 hours
    },
    "check-budget-alerts-30min": {
        "task": "app.tasks.advertising.budget_alerts",
        "schedule": 1800.0,  # Every 30 minutes
    },
}
