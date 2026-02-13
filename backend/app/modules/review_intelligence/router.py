"""FastAPI router for Review Intelligence endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.pagination import PaginatedResponse
from app.database import get_db
from app.modules.review_intelligence.schemas import (
    AcquisitionTipsRequest,
    AcquisitionTipsResponse,
    AlertAcknowledgeRequest,
    AlertListParams,
    AlertSeverity,
    AlertType,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    ReputationHealthMetrics,
    ReviewAlertRead,
    ReviewListParams,
    ReviewRead,
    ReviewSource,
    SentimentBreakdown,
    SentimentLabel,
    VelocityPeriod,
    VelocityReport,
)
from app.modules.review_intelligence.service import (
    acknowledge_alert,
    analyze_reviews_batch,
    compute_reputation_score,
    generate_acquisition_tips,
    get_reviews_for_book,
    get_sentiment_breakdown,
    list_alerts,
    list_reviews,
)
from app.modules.review_intelligence.velocity import compute_velocity_from_snapshots

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[ReviewRead],
    summary="List reviews",
    description="List reviews for the organization's books with optional filters.",
)
async def list_reviews_endpoint(
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    source: ReviewSource | None = Query(None),
    min_rating: float | None = Query(None, ge=0.0, le=5.0),
    max_rating: float | None = Query(None, ge=0.0, le=5.0),
    sentiment: SentimentLabel | None = Query(None),
    is_competitor: bool | None = Query(None),
    sort_by: str = Query("review_date"),
    sort_dir: str = Query("desc"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List reviews for org's books."""
    params = ReviewListParams(
        cursor=cursor,
        limit=limit,
        source=source,
        min_rating=min_rating,
        max_rating=max_rating,
        sentiment=sentiment,
        is_competitor=is_competitor,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    reviews, next_cursor, total_count = await list_reviews(
        db, current_user["org_id"], params
    )
    return PaginatedResponse(
        items=[ReviewRead.model_validate(r) for r in reviews],
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
        total_count=total_count,
    )


@router.get(
    "/book/{book_id}",
    response_model=PaginatedResponse[ReviewRead],
    summary="Get book reviews",
    description="Get reviews for a specific book with sentiment analysis and filters.",
)
async def get_book_reviews_endpoint(
    book_id: UUID,
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    sentiment: SentimentLabel | None = Query(None),
    min_rating: float | None = Query(None, ge=0.0, le=5.0),
    max_rating: float | None = Query(None, ge=0.0, le=5.0),
    sort_by: str = Query("review_date"),
    sort_dir: str = Query("desc"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get reviews for a specific book with sentiment analysis."""
    params = ReviewListParams(
        cursor=cursor,
        limit=limit,
        sentiment=sentiment,
        min_rating=min_rating,
        max_rating=max_rating,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    reviews, next_cursor, total_count = await get_reviews_for_book(
        db, current_user["org_id"], book_id, params
    )
    return PaginatedResponse(
        items=[ReviewRead.model_validate(r) for r in reviews],
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
        total_count=total_count,
    )


@router.get(
    "/sentiment/{book_id}",
    response_model=SentimentBreakdown,
    summary="Get sentiment breakdown",
    description="Get sentiment breakdown (positive/neutral/negative) and key themes for a book.",
)
async def get_sentiment_endpoint(
    book_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get sentiment breakdown for a book (positive/neutral/negative, key themes)."""
    return await get_sentiment_breakdown(db, current_user["org_id"], book_id)


@router.get(
    "/velocity/{book_id}",
    response_model=VelocityReport,
    summary="Get review velocity",
    description="Get review velocity (rate of new reviews) over time for a book.",
)
async def get_velocity_endpoint(
    book_id: UUID,
    period: VelocityPeriod = Query(VelocityPeriod.WEEKLY),
    lookback: int | None = Query(None, ge=1, le=52),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get review velocity over time for a book."""
    return await compute_velocity_from_snapshots(
        db, current_user["org_id"], book_id, period, lookback
    )


@router.get(
    "/alerts",
    response_model=PaginatedResponse[ReviewAlertRead],
    summary="List review alerts",
    description="List active review alerts such as negative reviews, velocity drops, and competitor surges.",
)
async def list_alerts_endpoint(
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    alert_type: AlertType | None = Query(None),
    severity: AlertSeverity | None = Query(None),
    is_acknowledged: bool | None = Query(False),
    book_id: UUID | None = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List active review alerts (negative review, velocity drop, competitor surge)."""
    params = AlertListParams(
        cursor=cursor,
        limit=limit,
        alert_type=alert_type,
        severity=severity,
        is_acknowledged=is_acknowledged,
        book_id=book_id,
    )
    alerts, next_cursor, total_count = await list_alerts(
        db, current_user["org_id"], params
    )
    return PaginatedResponse(
        items=[ReviewAlertRead.model_validate(a) for a in alerts],
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
        total_count=total_count,
    )


@router.get("/alerts/history")
async def get_alert_history(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get alert notification history."""
    return []


@router.post("/alerts")
async def create_review_alert(
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new review alert."""
    return {"id": "stub", **body, "active": True, "created_at": "2026-01-01T00:00:00Z"}


@router.patch("/alerts/{alert_id}")
async def update_review_alert(
    alert_id: str,
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a review alert."""
    return {"id": alert_id, **body}


@router.delete("/alerts/{alert_id}")
async def delete_review_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a review alert."""
    return {"message": "Deleted"}


@router.patch(
    "/alerts/{alert_id}/acknowledge",
    response_model=ReviewAlertRead,
    summary="Acknowledge review alert",
    description="Acknowledge a review alert to dismiss it from the active list.",
)
async def acknowledge_alert_endpoint(
    alert_id: UUID,
    body: AlertAcknowledgeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Acknowledge an alert."""
    alert = await acknowledge_alert(
        db, current_user["org_id"], alert_id, current_user["user_id"]
    )
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )
    return ReviewAlertRead.model_validate(alert)


@router.post(
    "/analyze",
    response_model=BatchAnalysisResponse,
    summary="Batch analyze reviews",
    description="AI-analyze a batch of reviews to extract themes, complaints, and praise.",
)
async def analyze_reviews_endpoint(
    body: BatchAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI analyze a batch of reviews (themes, complaints, praise)."""
    return await analyze_reviews_batch(db, current_user["org_id"], body)


@router.get(
    "/reputation/{book_id}",
    response_model=ReputationHealthMetrics,
    summary="Get reputation score",
    description="Get reputation score and health metrics for a book based on review data.",
)
async def get_reputation_endpoint(
    book_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get reputation score and health metrics for a book."""
    return await compute_reputation_score(db, current_user["org_id"], book_id)


@router.post(
    "/acquisition/tips",
    response_model=AcquisitionTipsResponse,
    summary="Get review acquisition tips",
    description="Get AI-generated tips for improving review acquisition rate.",
)
async def get_acquisition_tips_endpoint(
    body: AcquisitionTipsRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get AI-generated tips for improving review acquisition."""
    return await generate_acquisition_tips(body)


# --- New stub endpoints for enhanced Review Intelligence ---


@router.get("/stats")
async def get_review_stats(
    book_id: str | None = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregate review statistics."""
    return {
        "total": 0, "avg_rating": 0.0, "this_month": 0,
        "this_month_change_pct": 0.0, "sentiment_score": 0.0,
        "velocity": 0.0, "genre_avg_velocity": 0.0,
        "needs_attention": 0, "book_count": 0,
        "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
    }


@router.get("/sentiment-trend")
async def get_sentiment_trend(
    book_id: str | None = Query(None),
    period: str = Query("6m"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get sentiment trend over time."""
    return {"data": []}


@router.get("/insights")
async def get_review_insights(
    book_id: str | None = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get AI review insights."""
    return {
        "positive_themes": [], "negative_themes": [],
        "keyword_cloud": [], "ai_summary": "",
        "action_items": [], "velocity_data": [],
        "computed_at": None,
    }


@router.get("/book-summaries")
async def get_book_review_summaries(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get review summaries for all published books."""
    return []


@router.post("/optimize-back-matter")
async def optimize_back_matter(
    body: dict,
    current_user: dict = Depends(get_current_user),
):
    """AI optimize back-of-book review request text."""
    return {"score": 75, "improved_text": "", "tips": []}


@router.get("/arc-campaigns")
async def list_arc_campaigns(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List ARC campaigns."""
    return []


@router.post("/arc-campaigns")
async def create_arc_campaign(
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create new ARC campaign."""
    return {"id": "stub", "name": body.get("name", ""), "status": "draft", "copies_sent": 0, "reviews_received": 0}


@router.post("/arc-campaigns/{campaign_id}/send-reminder")
async def send_arc_reminder(
    campaign_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Send reminder to ARC recipients."""
    return {"message": "Reminder sent"}


@router.post("/email-sequences/generate")
async def generate_email_sequence(
    body: dict,
    current_user: dict = Depends(get_current_user),
):
    """Generate email sequence for review acquisition."""
    return {"emails": []}


@router.patch("/{review_id}")
async def update_review(
    review_id: str,
    body: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update review (mark read, flag, etc.)."""
    return {"id": review_id, **body}
