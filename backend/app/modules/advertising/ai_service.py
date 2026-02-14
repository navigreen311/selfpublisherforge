"""AI-powered insights, keyword suggestions, and bid optimization for Advertising Intelligence."""

import random
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.advertising.models import Campaign, CampaignPerformance, KeywordBid


async def get_ai_insights(db: AsyncSession, org_id) -> list[dict]:
    """Analyze campaigns and generate actionable insights.

    Returns mock/calculated insights based on campaign performance data,
    including budget suggestions, ACOS warnings, and keyword opportunities.
    """
    insights = []

    # Get all active campaigns
    result = await db.execute(
        select(Campaign).where(
            and_(
                Campaign.org_id == org_id,
                Campaign.deleted_at.is_(None),
            )
        )
    )
    campaigns = result.scalars().all()

    if not campaigns:
        insights.append({
            "type": "getting_started",
            "message": "No campaigns found. Create your first campaign to start advertising your books.",
            "campaign_id": None,
            "action": "create_campaign",
            "severity": "info",
        })
        return insights

    active_campaigns = [c for c in campaigns if c.status == "active"]
    paused_campaigns = [c for c in campaigns if c.status == "paused"]

    if not active_campaigns:
        insights.append({
            "type": "no_active",
            "message": f"You have {len(campaigns)} campaign(s) but none are active. Consider activating or creating new campaigns.",
            "campaign_id": None,
            "action": "activate_campaign",
            "severity": "warning",
        })

    # Analyze each active campaign
    since = datetime.utcnow() - timedelta(days=30)
    for campaign in active_campaigns:
        perf_result = await db.execute(
            select(CampaignPerformance).where(
                and_(
                    CampaignPerformance.campaign_id == campaign.id,
                    CampaignPerformance.date >= since,
                )
            )
        )
        perf_records = perf_result.scalars().all()

        if not perf_records:
            insights.append({
                "type": "no_data",
                "message": f"Campaign '{campaign.name}' has no performance data in the last 30 days. Check if it is running correctly.",
                "campaign_id": str(campaign.id),
                "action": "check_campaign",
                "severity": "warning",
            })
            continue

        total_spend = sum(r.spend for r in perf_records)
        total_sales = sum(r.sales for r in perf_records)
        total_impressions = sum(r.impressions for r in perf_records)
        total_clicks = sum(r.clicks for r in perf_records)

        # ACOS analysis
        if total_sales > 0:
            acos = (total_spend / total_sales) * 100
            if acos > 70:
                insights.append({
                    "type": "high_acos",
                    "message": f"Campaign '{campaign.name}' has a high ACOS of {acos:.1f}%. Consider lowering bids or pausing underperforming keywords.",
                    "campaign_id": str(campaign.id),
                    "action": "optimize_bids",
                    "severity": "warning",
                })
            elif acos < 20:
                insights.append({
                    "type": "low_acos",
                    "message": f"Campaign '{campaign.name}' has an excellent ACOS of {acos:.1f}%. Consider increasing bids to capture more sales.",
                    "campaign_id": str(campaign.id),
                    "action": "increase_bids",
                    "severity": "success",
                })

        # CTR analysis
        if total_impressions > 0:
            ctr = (total_clicks / total_impressions) * 100
            if ctr < 0.2:
                insights.append({
                    "type": "low_ctr",
                    "message": f"Campaign '{campaign.name}' has a low CTR of {ctr:.2f}%. Consider improving ad copy or refining targeting.",
                    "campaign_id": str(campaign.id),
                    "action": "improve_creative",
                    "severity": "warning",
                })

        # Budget analysis
        if total_spend > 0 and campaign.daily_budget > 0:
            avg_daily_spend = total_spend / len(perf_records)
            budget_utilization = (avg_daily_spend / campaign.daily_budget) * 100
            if budget_utilization > 95:
                insights.append({
                    "type": "budget_capped",
                    "message": f"Campaign '{campaign.name}' is spending its full daily budget. Consider increasing budget to capture more traffic.",
                    "campaign_id": str(campaign.id),
                    "action": "increase_budget",
                    "severity": "info",
                })
            elif budget_utilization < 30:
                insights.append({
                    "type": "low_spend",
                    "message": f"Campaign '{campaign.name}' is only using {budget_utilization:.0f}% of its budget. Consider adding more keywords or increasing bids.",
                    "campaign_id": str(campaign.id),
                    "action": "add_keywords",
                    "severity": "info",
                })

        # Zero-sales keywords analysis
        kw_result = await db.execute(
            select(KeywordBid).where(
                and_(
                    KeywordBid.campaign_id == campaign.id,
                    KeywordBid.is_active.is_(True),
                    KeywordBid.is_negative.is_(False),
                    KeywordBid.spend > 5.0,
                    KeywordBid.sales == 0,
                )
            )
        )
        wasteful_keywords = kw_result.scalars().all()
        if wasteful_keywords:
            kw_names = ", ".join(kw.keyword for kw in wasteful_keywords[:3])
            insights.append({
                "type": "wasteful_keywords",
                "message": f"Campaign '{campaign.name}' has {len(wasteful_keywords)} keyword(s) with spend but no sales ({kw_names}). Consider negating or pausing them.",
                "campaign_id": str(campaign.id),
                "action": "negate_keywords",
                "severity": "warning",
            })

    # Paused campaign reminder
    if paused_campaigns:
        insights.append({
            "type": "paused_campaigns",
            "message": f"You have {len(paused_campaigns)} paused campaign(s). Review them to see if any should be reactivated.",
            "campaign_id": None,
            "action": "review_paused",
            "severity": "info",
        })

    return insights


async def suggest_keywords(db: AsyncSession, org_id, book_id=None) -> list[dict]:
    """Generate keyword suggestions with mock search volumes and suggested bids.

    Uses existing campaign keywords and book data to generate related suggestions.
    """
    # Get existing keywords from the org's campaigns
    campaign_ids_q = select(Campaign.id).where(
        and_(
            Campaign.org_id == org_id,
            Campaign.deleted_at.is_(None),
        )
    )
    if book_id:
        campaign_ids_q = campaign_ids_q.where(Campaign.book_id == book_id)

    kw_result = await db.execute(
        select(KeywordBid.keyword).where(
            KeywordBid.campaign_id.in_(campaign_ids_q),
            KeywordBid.is_negative.is_(False),
        ).distinct()
    )
    existing_keywords = [r for r in kw_result.scalars().all()]

    # Generate mock keyword suggestions based on existing keywords
    suggestion_templates = [
        "best {genre} books",
        "{genre} kindle books",
        "{genre} ebook",
        "new {genre} releases",
        "{genre} paperback",
        "{genre} audiobook",
        "top rated {genre}",
        "{genre} book series",
        "best selling {genre}",
        "{genre} must read",
        "books like {keyword}",
        "{keyword} similar books",
        "{keyword} series",
        "best {keyword}",
        "{keyword} kindle",
    ]

    genres = [
        "romance", "thriller", "mystery", "fantasy", "sci-fi",
        "self-help", "business", "horror", "historical fiction", "literary fiction",
    ]

    suggestions = []
    seen = set()

    # Generate suggestions from existing keywords
    for kw in existing_keywords[:5]:
        for template in random.sample(suggestion_templates, min(3, len(suggestion_templates))):
            suggestion = template.format(keyword=kw, genre=kw)
            if suggestion not in seen and suggestion != kw:
                seen.add(suggestion)
                suggestions.append({
                    "keyword": suggestion,
                    "search_volume": random.randint(100, 50000),
                    "suggested_bid": round(random.uniform(0.25, 3.50), 2),
                    "competition": random.choice(["low", "medium", "high"]),
                })

    # If few suggestions from existing keywords, add genre-based ones
    if len(suggestions) < 10:
        for genre in random.sample(genres, min(5, len(genres))):
            for template in random.sample(suggestion_templates[:10], min(2, len(suggestion_templates))):
                suggestion = template.format(genre=genre, keyword=genre)
                if suggestion not in seen:
                    seen.add(suggestion)
                    suggestions.append({
                        "keyword": suggestion,
                        "search_volume": random.randint(500, 100000),
                        "suggested_bid": round(random.uniform(0.20, 2.50), 2),
                        "competition": random.choice(["low", "medium", "high"]),
                    })

    # Sort by search volume descending and limit
    suggestions.sort(key=lambda x: x["search_volume"], reverse=True)
    return suggestions[:20]


async def optimize_bids(
    db: AsyncSession,
    org_id,
    campaign_id,
    target_acos: float = 30.0,
    strategy: str = "maximize_sales",
) -> dict:
    """Analyze keyword performance and recommend bid adjustments.

    Strategies:
    - maximize_sales: Increase bids on converting keywords, decrease on non-converters
    - minimize_acos: Aggressively lower bids on high-ACOS keywords
    - maximize_impressions: Increase bids broadly to gain visibility
    """
    # Verify campaign belongs to org
    campaign_result = await db.execute(
        select(Campaign).where(
            and_(
                Campaign.id == campaign_id,
                Campaign.org_id == org_id,
                Campaign.deleted_at.is_(None),
            )
        )
    )
    campaign = campaign_result.scalar_one_or_none()
    if not campaign:
        return {"recommendations": [], "estimated_impact": {"message": "Campaign not found"}}

    # Get active keyword bids
    kw_result = await db.execute(
        select(KeywordBid).where(
            and_(
                KeywordBid.campaign_id == campaign_id,
                KeywordBid.is_active.is_(True),
                KeywordBid.is_negative.is_(False),
            )
        )
    )
    keywords = kw_result.scalars().all()

    if not keywords:
        return {
            "recommendations": [],
            "estimated_impact": {"message": "No active keywords found for this campaign"},
        }

    recommendations = []
    total_current_spend = 0.0
    total_estimated_spend = 0.0

    for kw in keywords:
        current_bid = kw.bid_amount
        kw_acos = kw.acos if kw.acos else 0.0
        suggested_bid = current_bid
        reason = ""

        if strategy == "maximize_sales":
            if kw.sales > 0 and kw_acos < target_acos:
                # High performer - increase bid to capture more
                increase_pct = min(0.25, (target_acos - kw_acos) / 100)
                suggested_bid = round(current_bid * (1 + increase_pct), 2)
                reason = f"Strong performer with ACOS {kw_acos:.1f}% below target. Increasing bid to capture more conversions."
            elif kw.clicks > 10 and kw.sales == 0:
                # Clicks but no sales - decrease
                suggested_bid = round(current_bid * 0.7, 2)
                reason = "Receiving clicks but no sales. Lowering bid to reduce waste."
            elif kw_acos > target_acos * 1.5:
                # Way over target ACOS
                decrease_pct = min(0.30, (kw_acos - target_acos) / 200)
                suggested_bid = round(current_bid * (1 - decrease_pct), 2)
                reason = f"ACOS of {kw_acos:.1f}% is well above target of {target_acos:.1f}%. Reducing bid."
            else:
                continue  # No change needed

        elif strategy == "minimize_acos":
            if kw_acos > target_acos:
                decrease_pct = min(0.35, (kw_acos - target_acos) / 100)
                suggested_bid = round(current_bid * (1 - decrease_pct), 2)
                reason = f"ACOS of {kw_acos:.1f}% exceeds target. Aggressively lowering bid."
            elif kw.clicks > 5 and kw.sales == 0:
                suggested_bid = round(current_bid * 0.5, 2)
                reason = "No conversions despite clicks. Significantly reducing bid."
            else:
                continue

        elif strategy == "maximize_impressions":
            if kw.impressions < 100:
                suggested_bid = round(current_bid * 1.3, 2)
                reason = "Low impressions. Increasing bid for visibility."
            elif kw.sales > 0:
                suggested_bid = round(current_bid * 1.15, 2)
                reason = "Converting keyword. Increasing bid to gain more impressions."
            else:
                suggested_bid = round(current_bid * 1.1, 2)
                reason = "Increasing bid moderately for broader reach."

        # Ensure minimum bid
        suggested_bid = max(0.02, suggested_bid)

        if abs(suggested_bid - current_bid) > 0.01:
            expected_acos_impact = round(
                (suggested_bid - current_bid) / current_bid * -10 if current_bid > 0 else 0, 1
            )
            recommendations.append({
                "keyword": kw.keyword,
                "current_bid": current_bid,
                "suggested_bid": suggested_bid,
                "reason": reason,
                "expected_acos_impact": expected_acos_impact,
            })
            total_current_spend += kw.spend
            total_estimated_spend += kw.spend * (suggested_bid / current_bid) if current_bid > 0 else 0

    estimated_impact = {
        "total_keywords_analyzed": len(keywords),
        "keywords_with_changes": len(recommendations),
        "estimated_spend_change_pct": round(
            ((total_estimated_spend - total_current_spend) / total_current_spend * 100)
            if total_current_spend > 0 else 0,
            1,
        ),
        "strategy": strategy,
        "target_acos": target_acos,
    }

    return {"recommendations": recommendations, "estimated_impact": estimated_impact}
