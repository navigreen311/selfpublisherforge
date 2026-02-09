"""Review monitoring, alert management, reputation scoring service."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.modules.review_intelligence.models import (
    BookReview,
    ReputationScore,
    ReviewAlert,
)
from app.modules.review_intelligence.schemas import (
    AcquisitionTip,
    AcquisitionTipsRequest,
    AcquisitionTipsResponse,
    AlertListParams,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    ReputationHealthMetrics,
    ReviewAlertRead,
    ReviewListParams,
    ReviewRead,
    SentimentBreakdown,
    SentimentLabel,
    VelocityPeriod,
    VelocityTrend,
)
from app.modules.review_intelligence.sentiment import (
    analyze_sentiment_batch,
    analyze_sentiment_llm,
    extract_themes_from_results,
)
from app.modules.review_intelligence.velocity import (
    compute_velocity_from_snapshots,
    detect_trend,
)

logger = logging.getLogger(__name__)
settings = get_settings()


# --- Review CRUD ---


async def list_reviews(
    db: AsyncSession,
    org_id: UUID,
    params: ReviewListParams,
) -> tuple[list[BookReview], Optional[str], int]:
    """List reviews for an org's books with filtering and pagination.

    Returns:
        Tuple of (reviews, next_cursor, total_count).
    """
    # Base query
    stmt = select(BookReview).where(
        and_(
            BookReview.org_id == org_id,
            BookReview.deleted_at.is_(None),
        )
    )

    count_stmt = select(func.count(BookReview.id)).where(
        and_(
            BookReview.org_id == org_id,
            BookReview.deleted_at.is_(None),
        )
    )

    # Apply filters
    if params.source:
        stmt = stmt.where(BookReview.source == params.source.value)
        count_stmt = count_stmt.where(BookReview.source == params.source.value)
    if params.min_rating is not None:
        stmt = stmt.where(BookReview.star_rating >= params.min_rating)
        count_stmt = count_stmt.where(BookReview.star_rating >= params.min_rating)
    if params.max_rating is not None:
        stmt = stmt.where(BookReview.star_rating <= params.max_rating)
        count_stmt = count_stmt.where(BookReview.star_rating <= params.max_rating)
    if params.sentiment:
        stmt = stmt.where(BookReview.sentiment == params.sentiment.value)
        count_stmt = count_stmt.where(BookReview.sentiment == params.sentiment.value)
    if params.is_competitor is not None:
        stmt = stmt.where(BookReview.is_competitor == params.is_competitor)
        count_stmt = count_stmt.where(BookReview.is_competitor == params.is_competitor)

    # Cursor pagination
    if params.cursor:
        stmt = stmt.where(BookReview.id > params.cursor)

    # Sorting
    sort_column = getattr(BookReview, params.sort_by, BookReview.review_date)
    if params.sort_dir == "asc":
        stmt = stmt.order_by(sort_column.asc())
    else:
        stmt = stmt.order_by(sort_column.desc())

    stmt = stmt.limit(params.limit + 1)

    result = await db.execute(stmt)
    reviews = list(result.scalars().all())

    count_result = await db.execute(count_stmt)
    total_count = count_result.scalar() or 0

    next_cursor = None
    if len(reviews) > params.limit:
        reviews = reviews[: params.limit]
        next_cursor = str(reviews[-1].id)

    return reviews, next_cursor, total_count


async def get_reviews_for_book(
    db: AsyncSession,
    org_id: UUID,
    book_id: UUID,
    params: ReviewListParams,
) -> tuple[list[BookReview], Optional[str], int]:
    """Get reviews for a specific book with sentiment data."""
    stmt = select(BookReview).where(
        and_(
            BookReview.org_id == org_id,
            BookReview.book_id == book_id,
            BookReview.deleted_at.is_(None),
        )
    )

    count_stmt = select(func.count(BookReview.id)).where(
        and_(
            BookReview.org_id == org_id,
            BookReview.book_id == book_id,
            BookReview.deleted_at.is_(None),
        )
    )

    if params.sentiment:
        stmt = stmt.where(BookReview.sentiment == params.sentiment.value)
        count_stmt = count_stmt.where(BookReview.sentiment == params.sentiment.value)
    if params.min_rating is not None:
        stmt = stmt.where(BookReview.star_rating >= params.min_rating)
        count_stmt = count_stmt.where(BookReview.star_rating >= params.min_rating)
    if params.max_rating is not None:
        stmt = stmt.where(BookReview.star_rating <= params.max_rating)
        count_stmt = count_stmt.where(BookReview.star_rating <= params.max_rating)

    if params.cursor:
        stmt = stmt.where(BookReview.id > params.cursor)

    sort_column = getattr(BookReview, params.sort_by, BookReview.review_date)
    if params.sort_dir == "asc":
        stmt = stmt.order_by(sort_column.asc())
    else:
        stmt = stmt.order_by(sort_column.desc())

    stmt = stmt.limit(params.limit + 1)

    result = await db.execute(stmt)
    reviews = list(result.scalars().all())

    count_result = await db.execute(count_stmt)
    total_count = count_result.scalar() or 0

    next_cursor = None
    if len(reviews) > params.limit:
        reviews = reviews[: params.limit]
        next_cursor = str(reviews[-1].id)

    return reviews, next_cursor, total_count


# --- Sentiment ---


async def get_sentiment_breakdown(
    db: AsyncSession, org_id: UUID, book_id: UUID
) -> SentimentBreakdown:
    """Get sentiment breakdown for a book's reviews."""
    stmt = select(
        func.count(BookReview.id).label("total"),
        func.count(
            case((BookReview.sentiment == "positive", 1))
        ).label("positive"),
        func.count(
            case((BookReview.sentiment == "neutral", 1))
        ).label("neutral"),
        func.count(
            case((BookReview.sentiment == "negative", 1))
        ).label("negative"),
        func.count(
            case((BookReview.sentiment == "mixed", 1))
        ).label("mixed"),
        func.avg(BookReview.sentiment_score).label("avg_score"),
    ).where(
        and_(
            BookReview.org_id == org_id,
            BookReview.book_id == book_id,
            BookReview.deleted_at.is_(None),
            BookReview.sentiment.isnot(None),
        )
    )

    result = await db.execute(stmt)
    row = result.one()

    total = row.total or 0
    positive = row.positive or 0
    neutral = row.neutral or 0
    negative = row.negative or 0
    mixed = row.mixed or 0

    # Extract themes from stored analysis results
    themes_stmt = select(BookReview.themes).where(
        and_(
            BookReview.org_id == org_id,
            BookReview.book_id == book_id,
            BookReview.themes.isnot(None),
            BookReview.deleted_at.is_(None),
        )
    )
    themes_result = await db.execute(themes_stmt)
    all_themes_data = themes_result.scalars().all()

    # Aggregate themes
    theme_counts: dict[str, int] = {}
    for themes_dict in all_themes_data:
        if isinstance(themes_dict, dict):
            for theme_name in themes_dict.get("themes", []):
                theme_counts[theme_name] = theme_counts.get(theme_name, 0) + 1

    from app.modules.review_intelligence.schemas import ThemeItem

    theme_items = [
        ThemeItem(
            theme=name,
            count=count,
            sentiment=SentimentLabel.NEUTRAL,
            example_quotes=[],
        )
        for name, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]
    ]

    return SentimentBreakdown(
        positive_count=positive,
        neutral_count=neutral,
        negative_count=negative,
        mixed_count=mixed,
        total_count=total,
        positive_pct=round((positive / total) * 100, 1) if total > 0 else 0.0,
        neutral_pct=round((neutral / total) * 100, 1) if total > 0 else 0.0,
        negative_pct=round((negative / total) * 100, 1) if total > 0 else 0.0,
        mixed_pct=round((mixed / total) * 100, 1) if total > 0 else 0.0,
        avg_sentiment_score=round(float(row.avg_score), 3) if row.avg_score else 0.0,
        themes=theme_items,
    )


async def analyze_reviews_batch(
    db: AsyncSession, org_id: UUID, request: BatchAnalysisRequest
) -> BatchAnalysisResponse:
    """Analyze a batch of reviews with AI sentiment analysis."""
    # Fetch reviews
    stmt = select(BookReview).where(
        and_(
            BookReview.org_id == org_id,
            BookReview.deleted_at.is_(None),
        )
    )

    if request.review_ids:
        stmt = stmt.where(BookReview.id.in_(request.review_ids))
    elif request.book_id:
        stmt = stmt.where(BookReview.book_id == request.book_id)

    stmt = stmt.limit(request.limit)

    result = await db.execute(stmt)
    reviews = list(result.scalars().all())

    if not reviews:
        return BatchAnalysisResponse(
            total_analyzed=0,
            sentiment_breakdown=SentimentBreakdown(
                positive_count=0,
                neutral_count=0,
                negative_count=0,
                mixed_count=0,
                total_count=0,
                positive_pct=0.0,
                neutral_pct=0.0,
                negative_pct=0.0,
                mixed_pct=0.0,
                avg_sentiment_score=0.0,
            ),
        )

    # Run sentiment analysis
    review_dicts = [
        {"text": r.body or "", "star_rating": r.star_rating} for r in reviews
    ]
    analysis_results = await analyze_sentiment_batch(review_dicts)

    # Update reviews with analysis results
    now = datetime.now(timezone.utc)
    for review, result_item in zip(reviews, analysis_results):
        review.sentiment = result_item.sentiment.value
        review.sentiment_score = result_item.score
        review.themes = {
            "themes": result_item.themes,
            "key_phrases": result_item.key_phrases,
            "complaints": result_item.complaints,
            "praise": result_item.praise,
        }
        review.analyzed_at = now
        db.add(review)

    await db.flush()

    # Build response
    positive = sum(1 for r in analysis_results if r.sentiment == SentimentLabel.POSITIVE)
    negative = sum(1 for r in analysis_results if r.sentiment == SentimentLabel.NEGATIVE)
    neutral = sum(1 for r in analysis_results if r.sentiment == SentimentLabel.NEUTRAL)
    mixed = sum(1 for r in analysis_results if r.sentiment == SentimentLabel.MIXED)
    total = len(analysis_results)

    all_complaints: list[str] = []
    all_praise: list[str] = []
    for r in analysis_results:
        all_complaints.extend(r.complaints)
        all_praise.extend(r.praise)

    themes = extract_themes_from_results(analysis_results)

    # Deduplicate
    top_complaints = list(dict.fromkeys(all_complaints))[:10]
    top_praise = list(dict.fromkeys(all_praise))[:10]

    avg_score = (
        sum(r.score for r in analysis_results) / total if total > 0 else 0.0
    )

    # Generate actionable insights
    insights = _generate_insights(positive, negative, neutral, total, themes)

    return BatchAnalysisResponse(
        total_analyzed=total,
        sentiment_breakdown=SentimentBreakdown(
            positive_count=positive,
            neutral_count=neutral,
            negative_count=negative,
            mixed_count=mixed,
            total_count=total,
            positive_pct=round((positive / total) * 100, 1) if total > 0 else 0.0,
            neutral_pct=round((neutral / total) * 100, 1) if total > 0 else 0.0,
            negative_pct=round((negative / total) * 100, 1) if total > 0 else 0.0,
            mixed_pct=round((mixed / total) * 100, 1) if total > 0 else 0.0,
            avg_sentiment_score=round(avg_score, 3),
            themes=themes,
        ),
        top_themes=themes[:5],
        top_complaints=top_complaints,
        top_praise=top_praise,
        actionable_insights=insights,
    )


def _generate_insights(
    positive: int, negative: int, neutral: int, total: int, themes: list
) -> list[str]:
    """Generate basic actionable insights from analysis."""
    insights = []

    if total == 0:
        return ["No reviews available for analysis."]

    neg_pct = (negative / total) * 100 if total > 0 else 0
    pos_pct = (positive / total) * 100 if total > 0 else 0

    if neg_pct > 30:
        insights.append(
            f"High negative sentiment ({neg_pct:.0f}%). Consider addressing common complaints."
        )
    if pos_pct > 70:
        insights.append(
            f"Strong positive sentiment ({pos_pct:.0f}%). Leverage this in marketing materials."
        )
    if neutral > positive and neutral > negative:
        insights.append(
            "Most reviews are neutral. Consider what could make the book more memorable."
        )

    # Theme-based insights
    for theme in themes[:3]:
        if theme.sentiment == SentimentLabel.NEGATIVE:
            insights.append(
                f'The theme "{theme.theme}" appears frequently with negative sentiment. '
                "This is an area to investigate."
            )
        elif theme.sentiment == SentimentLabel.POSITIVE:
            insights.append(
                f'Readers frequently praise "{theme.theme}". Highlight this in your marketing.'
            )

    if not insights:
        insights.append("Review sentiment is balanced. Monitor for changes over time.")

    return insights


# --- Alerts ---


async def list_alerts(
    db: AsyncSession, org_id: UUID, params: AlertListParams
) -> tuple[list[ReviewAlert], Optional[str], int]:
    """List review alerts with filtering."""
    stmt = select(ReviewAlert).where(
        and_(
            ReviewAlert.org_id == org_id,
            ReviewAlert.deleted_at.is_(None),
        )
    )

    count_stmt = select(func.count(ReviewAlert.id)).where(
        and_(
            ReviewAlert.org_id == org_id,
            ReviewAlert.deleted_at.is_(None),
        )
    )

    if params.alert_type:
        stmt = stmt.where(ReviewAlert.alert_type == params.alert_type.value)
        count_stmt = count_stmt.where(ReviewAlert.alert_type == params.alert_type.value)
    if params.severity:
        stmt = stmt.where(ReviewAlert.severity == params.severity.value)
        count_stmt = count_stmt.where(ReviewAlert.severity == params.severity.value)
    if params.is_acknowledged is not None:
        stmt = stmt.where(ReviewAlert.is_acknowledged == params.is_acknowledged)
        count_stmt = count_stmt.where(
            ReviewAlert.is_acknowledged == params.is_acknowledged
        )
    if params.book_id:
        stmt = stmt.where(ReviewAlert.book_id == params.book_id)
        count_stmt = count_stmt.where(ReviewAlert.book_id == params.book_id)

    if params.cursor:
        stmt = stmt.where(ReviewAlert.id > params.cursor)

    stmt = stmt.order_by(ReviewAlert.created_at.desc()).limit(params.limit + 1)

    result = await db.execute(stmt)
    alerts = list(result.scalars().all())

    count_result = await db.execute(count_stmt)
    total_count = count_result.scalar() or 0

    next_cursor = None
    if len(alerts) > params.limit:
        alerts = alerts[: params.limit]
        next_cursor = str(alerts[-1].id)

    return alerts, next_cursor, total_count


async def acknowledge_alert(
    db: AsyncSession,
    org_id: UUID,
    alert_id: UUID,
    user_id: UUID,
) -> Optional[ReviewAlert]:
    """Acknowledge a review alert."""
    stmt = select(ReviewAlert).where(
        and_(
            ReviewAlert.id == alert_id,
            ReviewAlert.org_id == org_id,
            ReviewAlert.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()

    if not alert:
        return None

    alert.is_acknowledged = True
    alert.acknowledged_at = datetime.now(timezone.utc)
    alert.acknowledged_by = user_id
    db.add(alert)
    await db.flush()
    return alert


# --- Reputation ---


async def compute_reputation_score(
    db: AsyncSession, org_id: UUID, book_id: UUID
) -> ReputationHealthMetrics:
    """Compute comprehensive reputation score and health metrics for a book."""
    # Aggregate review stats
    stats_stmt = select(
        func.count(BookReview.id).label("total"),
        func.avg(BookReview.star_rating).label("avg_rating"),
        func.count(
            case((BookReview.sentiment == "positive", 1))
        ).label("positive"),
        func.count(
            case((BookReview.sentiment == "negative", 1))
        ).label("negative"),
    ).where(
        and_(
            BookReview.org_id == org_id,
            BookReview.book_id == book_id,
            BookReview.is_competitor == False,
            BookReview.deleted_at.is_(None),
        )
    )

    stats_result = await db.execute(stats_stmt)
    stats = stats_result.one()

    total = stats.total or 0
    avg_rating = float(stats.avg_rating) if stats.avg_rating else 0.0
    positive = stats.positive or 0
    negative = stats.negative or 0
    sentiment_ratio = positive / total if total > 0 else 0.0

    # Rating distribution
    dist_stmt = select(
        BookReview.star_rating,
        func.count(BookReview.id),
    ).where(
        and_(
            BookReview.org_id == org_id,
            BookReview.book_id == book_id,
            BookReview.is_competitor == False,
            BookReview.deleted_at.is_(None),
        )
    ).group_by(BookReview.star_rating)

    dist_result = await db.execute(dist_stmt)
    rating_distribution = {
        str(int(row[0])): row[1] for row in dist_result.all() if row[0] is not None
    }

    # Compute velocity trend (using recent data)
    try:
        velocity = await compute_velocity_from_snapshots(
            db, org_id, book_id, VelocityPeriod.WEEKLY, lookback=4
        )
        velocity_trend = velocity.trend
    except Exception:
        velocity_trend = VelocityTrend.STABLE

    # Calculate overall score (0-100)
    overall_score = _calculate_overall_score(
        avg_rating, total, sentiment_ratio, velocity_trend
    )

    # Health grade
    health_grade = _score_to_grade(overall_score)

    # Recommendations
    recommendations = _generate_reputation_recommendations(
        avg_rating, total, sentiment_ratio, velocity_trend, negative, total
    )

    # Recent trend description
    recent_trend = (
        f"{'Rising' if velocity_trend == VelocityTrend.RISING else 'Stable' if velocity_trend == VelocityTrend.STABLE else 'Declining'} "
        f"review velocity with {total} total reviews and {avg_rating:.1f} avg rating"
    )

    # Upsert reputation score
    existing_stmt = select(ReputationScore).where(
        and_(
            ReputationScore.book_id == book_id,
            ReputationScore.org_id == org_id,
        )
    )
    existing_result = await db.execute(existing_stmt)
    rep_score = existing_result.scalar_one_or_none()

    if rep_score:
        rep_score.overall_score = overall_score
        rep_score.avg_rating = avg_rating
        rep_score.total_reviews = total
        rep_score.sentiment_ratio = sentiment_ratio
        rep_score.velocity_trend = velocity_trend.value
        rep_score.health_grade = health_grade
        rep_score.details = {
            "rating_distribution": rating_distribution,
            "recommendations": recommendations,
        }
        rep_score.last_calculated_at = datetime.now(timezone.utc)
    else:
        rep_score = ReputationScore(
            org_id=org_id,
            book_id=book_id,
            overall_score=overall_score,
            avg_rating=avg_rating,
            total_reviews=total,
            sentiment_ratio=sentiment_ratio,
            velocity_trend=velocity_trend.value,
            health_grade=health_grade,
            details={
                "rating_distribution": rating_distribution,
                "recommendations": recommendations,
            },
            last_calculated_at=datetime.now(timezone.utc),
        )
        db.add(rep_score)

    await db.flush()

    return ReputationHealthMetrics(
        book_id=book_id,
        overall_score=overall_score,
        avg_rating=round(avg_rating, 2),
        total_reviews=total,
        sentiment_ratio=round(sentiment_ratio, 3),
        velocity_trend=velocity_trend,
        health_grade=health_grade,
        rating_distribution=rating_distribution,
        recent_trend=recent_trend,
        recommendations=recommendations,
    )


def _calculate_overall_score(
    avg_rating: float,
    total_reviews: int,
    sentiment_ratio: float,
    velocity_trend: VelocityTrend,
) -> float:
    """Calculate an overall reputation score from 0-100.

    Components:
    - Rating score (40%): avg_rating / 5 * 100
    - Volume score (20%): log-scaled review count
    - Sentiment score (25%): positive sentiment ratio
    - Velocity score (15%): bonus/penalty for trend
    """
    import math

    # Rating component (0-40)
    rating_score = (avg_rating / 5.0) * 40 if avg_rating > 0 else 0

    # Volume component (0-20), log-scaled
    if total_reviews > 0:
        volume_score = min(20, (math.log10(total_reviews + 1) / math.log10(1001)) * 20)
    else:
        volume_score = 0

    # Sentiment component (0-25)
    sentiment_score = sentiment_ratio * 25

    # Velocity component (0-15)
    if velocity_trend == VelocityTrend.RISING:
        velocity_score = 15
    elif velocity_trend == VelocityTrend.STABLE:
        velocity_score = 10
    else:
        velocity_score = 5

    total = rating_score + volume_score + sentiment_score + velocity_score
    return round(min(100, max(0, total)), 1)


def _score_to_grade(score: float) -> str:
    """Convert numerical score to letter grade."""
    if score >= 95:
        return "A+"
    elif score >= 90:
        return "A"
    elif score >= 85:
        return "B+"
    elif score >= 80:
        return "B"
    elif score >= 75:
        return "C+"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def _generate_reputation_recommendations(
    avg_rating: float,
    total_reviews: int,
    sentiment_ratio: float,
    velocity_trend: VelocityTrend,
    negative_count: int,
    total_count: int,
) -> list[str]:
    """Generate reputation improvement recommendations."""
    recommendations = []

    if total_reviews < 10:
        recommendations.append(
            "Your book has very few reviews. Focus on building an ARC team and requesting reviews from readers."
        )
    elif total_reviews < 50:
        recommendations.append(
            "Building review count. Consider email follow-ups and social media outreach to drive more reviews."
        )

    if avg_rating < 3.5 and total_reviews > 5:
        recommendations.append(
            "Average rating is below 3.5. Review negative feedback for patterns and consider content revisions."
        )
    elif avg_rating < 4.0 and total_reviews > 10:
        recommendations.append(
            "Consider addressing common complaints to push your average rating above 4.0."
        )

    if sentiment_ratio < 0.5 and total_count > 5:
        recommendations.append(
            "Less than half your reviews have positive sentiment. Analyze negative themes and address them."
        )

    if velocity_trend == VelocityTrend.DECLINING:
        recommendations.append(
            "Review velocity is declining. Consider promotional activities to boost visibility and reviews."
        )

    neg_pct = (negative_count / total_count * 100) if total_count > 0 else 0
    if neg_pct > 25:
        recommendations.append(
            f"{neg_pct:.0f}% of reviews are negative. Prioritize addressing the most common complaints."
        )

    if not recommendations:
        recommendations.append(
            "Your book's reputation is healthy! Continue monitoring and engaging with readers."
        )

    return recommendations


# --- Review Acquisition Tips (AI-powered) ---


async def generate_acquisition_tips(
    request: AcquisitionTipsRequest,
) -> AcquisitionTipsResponse:
    """Generate AI-powered tips for improving review acquisition."""
    # Try LLM-based tips
    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        prompt = f"""You are a book marketing expert. Generate actionable tips for getting more book reviews.

Context:
- Current review count: {request.current_review_count or 'unknown'}
- Genre: {request.genre or 'unknown'}
- Target audience: {request.target_audience or 'general'}
- Budget: {request.budget or 'medium'}

Return a JSON object with:
- "tips": list of objects with "category", "tip", "effort_level" (low/medium/high), "expected_impact" (low/medium/high), "details"
- "estimated_review_potential": integer estimate of reviews achievable in 3 months
- "summary": brief overall recommendation

Return ONLY valid JSON."""

        message = await client.messages.create(
            model=settings.DEFAULT_LLM_MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text.strip()
        result_data = json.loads(response_text)

        tips = [
            AcquisitionTip(**tip_data)
            for tip_data in result_data.get("tips", [])
        ]

        return AcquisitionTipsResponse(
            book_id=request.book_id,
            tips=tips,
            estimated_review_potential=result_data.get(
                "estimated_review_potential", 0
            ),
            summary=result_data.get("summary", ""),
        )
    except ImportError:
        logger.info("Anthropic SDK not available, using default tips")
    except Exception as e:
        logger.warning(f"LLM acquisition tips failed, using defaults: {e}")

    # Fallback tips
    return _default_acquisition_tips(request)


def _default_acquisition_tips(
    request: AcquisitionTipsRequest,
) -> AcquisitionTipsResponse:
    """Generate default (non-AI) acquisition tips."""
    tips = [
        AcquisitionTip(
            category="ARC Team",
            tip="Build an Advance Reader Copy (ARC) team",
            effort_level="medium",
            expected_impact="high",
            details=(
                "Create a list of beta readers and ARC reviewers. "
                "Offer free copies in exchange for honest reviews on launch day."
            ),
        ),
        AcquisitionTip(
            category="Email Follow-up",
            tip="Add a review request to your back matter and email sequence",
            effort_level="low",
            expected_impact="medium",
            details=(
                "Include a direct link to your book's review page at the end of your book. "
                "Send a follow-up email to purchasers 7-10 days after purchase."
            ),
        ),
        AcquisitionTip(
            category="Social Media",
            tip="Engage with book communities on social media",
            effort_level="medium",
            expected_impact="medium",
            details=(
                "Join BookTok, Bookstagram, and genre-specific Facebook groups. "
                "Build genuine relationships, not just self-promotion."
            ),
        ),
        AcquisitionTip(
            category="BookSprout / NetGalley",
            tip="Use review platforms like BookSprout or NetGalley",
            effort_level="low",
            expected_impact="medium",
            details=(
                "These platforms connect authors with reviewers. "
                "Great for building initial review counts on new releases."
            ),
        ),
        AcquisitionTip(
            category="Newsletter Swap",
            tip="Partner with other authors for newsletter swaps",
            effort_level="medium",
            expected_impact="medium",
            details=(
                "Cross-promote with authors in your genre. "
                "Their readers may review your book and vice versa."
            ),
        ),
    ]

    count = request.current_review_count or 0
    if count < 10:
        potential = 20
    elif count < 50:
        potential = 30
    else:
        potential = 15

    return AcquisitionTipsResponse(
        book_id=request.book_id,
        tips=tips,
        estimated_review_potential=potential,
        summary=(
            "Focus on building an ARC team and leveraging email follow-ups. "
            "These are the highest-ROI activities for most self-published authors."
        ),
    )
