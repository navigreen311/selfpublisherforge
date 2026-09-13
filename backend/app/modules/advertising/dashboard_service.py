"""Enhanced dashboard service for Advertising Intelligence."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.advertising.models import Campaign, CampaignPerformance


async def get_enhanced_dashboard(db: AsyncSession, org_id, period: str = "30d"):
    """Return dashboard with stats, trend data, and top campaigns."""
    days = int(period.replace("d", "")) if period.endswith("d") else 30
    start_date = datetime.utcnow() - timedelta(days=days)

    # Get active campaigns count
    campaigns_q = await db.execute(
        select(Campaign).where(
            Campaign.org_id == org_id,
            Campaign.status == "active",
            Campaign.deleted_at.is_(None),
        )
    )
    campaigns = campaigns_q.scalars().all()

    # Get performance data
    perf_q = await db.execute(
        select(CampaignPerformance)
        .join(Campaign, CampaignPerformance.campaign_id == Campaign.id)
        .where(Campaign.org_id == org_id, CampaignPerformance.date >= start_date)
        .order_by(CampaignPerformance.date)
    )
    perf_records = perf_q.scalars().all()

    # Aggregate stats
    total_spend = sum(r.spend for r in perf_records)
    total_sales = sum(r.sales for r in perf_records)
    total_impressions = sum(r.impressions for r in perf_records)
    total_clicks = sum(r.clicks for r in perf_records)

    stats = {
        "active_campaigns": len(campaigns),
        "total_spend_today": 0.0,
        "total_spend_period": round(total_spend, 2),
        "total_sales_period": round(total_sales, 2),
        "overall_acos": round((total_spend / total_sales * 100) if total_sales > 0 else 0, 1),
        "overall_roas": round(total_sales / total_spend if total_spend > 0 else 0, 1),
        "total_impressions": total_impressions,
        "total_clicks": total_clicks,
    }

    # Trend data (aggregate by date)
    # Values mix a date string with numeric counters, so this needs an
    # explicit annotation or they infer as `object` and every += fails.
    trend_map: dict[str, dict[str, Any]] = {}
    for r in perf_records:
        date_key = r.date.strftime("%Y-%m-%d") if hasattr(r.date, "strftime") else str(r.date)
        if date_key not in trend_map:
            trend_map[date_key] = {
                "date": date_key,
                "spend": 0,
                "sales": 0,
                "impressions": 0,
                "clicks": 0,
                "orders": 0,
            }
        trend_map[date_key]["spend"] += r.spend
        trend_map[date_key]["sales"] += r.sales
        trend_map[date_key]["impressions"] += r.impressions
        trend_map[date_key]["clicks"] += r.clicks
        trend_map[date_key]["orders"] += r.orders
    trend_data = sorted(trend_map.values(), key=lambda x: x["date"])

    # Top campaigns by spend
    campaign_stats: dict[Any, dict[str, Any]] = {}
    for r in perf_records:
        cid = str(r.campaign_id)
        if cid not in campaign_stats:
            campaign_stats[cid] = {
                "campaign_id": cid,
                "spend": 0,
                "sales": 0,
                "impressions": 0,
                "clicks": 0,
                "orders": 0,
            }
        campaign_stats[cid]["spend"] += r.spend
        campaign_stats[cid]["sales"] += r.sales
        campaign_stats[cid]["impressions"] += r.impressions
        campaign_stats[cid]["clicks"] += r.clicks
        campaign_stats[cid]["orders"] += r.orders

    top_campaigns = []
    for cid, cs in sorted(campaign_stats.items(), key=lambda x: x[1]["spend"], reverse=True)[:10]:
        campaign = next((c for c in campaigns if str(c.id) == cid), None)
        acos = round((cs["spend"] / cs["sales"] * 100) if cs["sales"] > 0 else 0, 1)
        ctr = round((cs["clicks"] / cs["impressions"] * 100) if cs["impressions"] > 0 else 0, 2)
        top_campaigns.append(
            {
                "campaign_id": cid,
                "name": campaign.name if campaign else "Unknown",
                "spend": round(cs["spend"], 2),
                "sales": round(cs["sales"], 2),
                "acos": acos,
                "impressions": cs["impressions"],
                "clicks": cs["clicks"],
                "ctr": ctr,
            }
        )

    return {"stats": stats, "trend_data": trend_data, "top_campaigns": top_campaigns}
