"""Dashboard aggregation service.

Pulls stats and summaries from existing modules -- falls back to zeros
when data is missing or queries fail (so the frontend never renders
nulls).
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.activity.models import ActivityLog
from app.modules.dashboard.schemas import (
    ActivePipelineItem,
    AIInsight,
    DashboardResponse,
    DashboardStats,
    RecentActivityItem,
    RevenuePoint,
    UpcomingDeadline,
)

logger = logging.getLogger(__name__)


async def _safe_scalar(db: AsyncSession, stmt, default=0):
    try:
        return (await db.scalar(stmt)) or default
    except Exception as exc:  # noqa: BLE001
        logger.debug("dashboard safe_scalar failed: %s", exc)
        return default


async def _safe_execute(db: AsyncSession, stmt):
    try:
        return (await db.execute(stmt)).all()
    except Exception as exc:  # noqa: BLE001
        logger.debug("dashboard safe_execute failed: %s", exc)
        return []


async def _get_stats(db: AsyncSession, org_id: UUID) -> DashboardStats:
    from app.models.project import Project

    stats = DashboardStats()

    total = await _safe_scalar(
        db,
        select(func.count(Project.id)).where(
            Project.org_id == org_id, Project.deleted_at.is_(None)
        ),
    )
    stats.total_projects = int(total or 0)

    in_progress = await _safe_scalar(
        db,
        select(func.count(Project.id)).where(
            Project.org_id == org_id,
            Project.deleted_at.is_(None),
            Project.status.in_(["active", "in_progress"]),
        ),
    )
    stats.in_progress = int(in_progress or 0)

    published = await _safe_scalar(
        db,
        select(func.count(Project.id)).where(
            Project.org_id == org_id,
            Project.deleted_at.is_(None),
            Project.status == "completed",
        ),
    )
    stats.published = int(published or 0)

    # Monthly revenue: sum RoyaltyRecord.net_revenue over last 30 days
    try:
        from app.modules.analytics.models import RoyaltyRecord

        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
        total_rev = await _safe_scalar(
            db,
            select(func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0)).where(
                RoyaltyRecord.org_id == org_id,
                RoyaltyRecord.period_start >= thirty_days_ago,
            ),
            default=Decimal("0"),
        )
        stats.monthly_revenue = Decimal(str(total_rev or 0))
    except Exception as exc:  # noqa: BLE001
        logger.debug("monthly_revenue failed: %s", exc)

    return stats


async def _get_revenue_trend(
    db: AsyncSession, org_id: UUID
) -> list[RevenuePoint]:
    try:
        from app.modules.analytics.models import RoyaltyRecord

        start = datetime.now(UTC) - timedelta(days=30)
        stmt = (
            select(
                func.date(RoyaltyRecord.period_start).label("d"),
                func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0).label("total"),
            )
            .where(
                RoyaltyRecord.org_id == org_id,
                RoyaltyRecord.period_start >= start,
            )
            .group_by(func.date(RoyaltyRecord.period_start))
            .order_by(func.date(RoyaltyRecord.period_start))
        )
        rows = await _safe_execute(db, stmt)
        out: list[RevenuePoint] = []
        for row in rows:
            d = row[0]
            if isinstance(d, str):
                try:
                    d = date.fromisoformat(d)
                except Exception:  # noqa: BLE001
                    continue
            elif isinstance(d, datetime):
                d = d.date()
            if not isinstance(d, date):
                continue
            out.append(RevenuePoint(date=d, amount=Decimal(str(row[1] or 0))))
        return out
    except Exception as exc:  # noqa: BLE001
        logger.debug("revenue_trend failed: %s", exc)
        return []


async def _get_active_pipelines(
    db: AsyncSession, org_id: UUID
) -> list[ActivePipelineItem]:
    try:
        from app.modules.production_pipeline.models import Pipeline

        stmt = (
            select(Pipeline)
            .where(
                Pipeline.org_id == org_id,
                Pipeline.deleted_at.is_(None),
            )
            .order_by(Pipeline.deadline.asc().nullslast())
            .limit(5)
        )
        result = await db.execute(stmt)
        pipelines = result.scalars().all()
        return [
            ActivePipelineItem(
                id=p.id,
                title=p.name,
                stage=(p.status.value if hasattr(p.status, "value") else str(p.status)),
                progress_pct=int(p.progress_pct or 0),
                due_date=p.deadline,
            )
            for p in pipelines
        ]
    except Exception as exc:  # noqa: BLE001
        logger.debug("active_pipelines failed: %s", exc)
        return []


async def _get_recent_activity(
    db: AsyncSession, org_id: UUID
) -> list[RecentActivityItem]:
    try:
        stmt = (
            select(ActivityLog)
            .where(ActivityLog.org_id == org_id)
            .order_by(ActivityLog.created_at.desc())
            .limit(10)
        )
        result = await db.execute(stmt)
        rows = result.scalars().all()
        return [RecentActivityItem.model_validate(r) for r in rows]
    except Exception as exc:  # noqa: BLE001
        logger.debug("recent_activity failed: %s", exc)
        return []


async def _get_upcoming_deadlines(
    db: AsyncSession, org_id: UUID
) -> list[UpcomingDeadline]:
    out: list[UpcomingDeadline] = []
    try:
        from app.models.project import Project

        today = datetime.now(UTC).date()
        stmt = (
            select(Project)
            .where(
                Project.org_id == org_id,
                Project.deleted_at.is_(None),
                Project.target_date.is_not(None),
                Project.target_date >= today,
            )
            .order_by(Project.target_date.asc())
            .limit(5)
        )
        result = await db.execute(stmt)
        for p in result.scalars().all():
            out.append(
                UpcomingDeadline(
                    id=p.id,
                    title=p.title,
                    date=p.target_date,
                    source_type="project",
                    source_id=p.id,
                )
            )
    except Exception as exc:  # noqa: BLE001
        logger.debug("upcoming_deadlines failed: %s", exc)
    return out


def _generate_insights(stats: DashboardStats) -> list[AIInsight]:
    insights: list[AIInsight] = []
    if stats.total_projects == 0:
        insights.append(
            AIInsight(
                id="onboard",
                type="getting_started",
                message="Publish your first book to receive AI-powered insights.",
                priority="info",
            )
        )
    else:
        if stats.monthly_revenue and stats.monthly_revenue > 0:
            insights.append(
                AIInsight(
                    id="revenue",
                    type="revenue",
                    message=(
                        f"You earned ${stats.monthly_revenue:.2f} in the last 30 "
                        "days -- consider a follow-up volume."
                    ),
                    priority="positive",
                )
            )
        if stats.in_progress > 0:
            insights.append(
                AIInsight(
                    id="in_progress",
                    type="progress",
                    message=(
                        f"{stats.in_progress} project(s) in progress -- review "
                        "active pipelines to keep launches on track."
                    ),
                    priority="info",
                )
            )
    return insights


async def get_dashboard(db: AsyncSession, org_id: UUID) -> DashboardResponse:
    """Return the aggregated dashboard payload for the given org."""
    stats = await _get_stats(db, org_id)
    revenue_trend = await _get_revenue_trend(db, org_id)
    active_pipelines = await _get_active_pipelines(db, org_id)
    recent_activity = await _get_recent_activity(db, org_id)
    upcoming_deadlines = await _get_upcoming_deadlines(db, org_id)
    ai_insights = _generate_insights(stats)
    return DashboardResponse(
        stats=stats,
        revenue_trend=revenue_trend,
        active_pipelines=active_pipelines,
        recent_activity=recent_activity,
        ai_insights=ai_insights,
        upcoming_deadlines=upcoming_deadlines,
    )
