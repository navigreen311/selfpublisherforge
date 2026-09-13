"""Alert rules: negative review spike, velocity drop, star rating decline,
competitor review surge.
"""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.review_intelligence.models import BookReview, ReviewAlert
from app.modules.review_intelligence.schemas import (
    AlertSeverity,
    AlertType,
    SentimentLabel,
)

logger = logging.getLogger(__name__)


# --- Alert Thresholds ---

DEFAULT_THRESHOLDS = {
    "negative_spike_pct": 50.0,  # 50% increase in negative reviews
    "velocity_drop_pct": -40.0,  # 40% decrease in review velocity
    "rating_decline_threshold": 0.3,  # star rating drop
    "competitor_surge_pct": 100.0,  # competitor reviews surge percentage
    "min_reviews_for_alert": 3,  # minimum reviews in period to trigger alert
}


def _determine_severity(alert_type: AlertType, magnitude: float) -> AlertSeverity:
    """Determine alert severity based on type and magnitude of the change."""
    if alert_type == AlertType.NEGATIVE_SPIKE:
        if magnitude > 200:
            return AlertSeverity.CRITICAL
        if magnitude > 100:
            return AlertSeverity.HIGH
        if magnitude > 50:
            return AlertSeverity.MEDIUM
        return AlertSeverity.LOW
    if alert_type == AlertType.VELOCITY_DROP:
        if magnitude < -80:
            return AlertSeverity.CRITICAL
        if magnitude < -60:
            return AlertSeverity.HIGH
        if magnitude < -40:
            return AlertSeverity.MEDIUM
        return AlertSeverity.LOW
    if alert_type == AlertType.RATING_DECLINE:
        if magnitude > 1.0:
            return AlertSeverity.CRITICAL
        if magnitude > 0.5:
            return AlertSeverity.HIGH
        if magnitude > 0.3:
            return AlertSeverity.MEDIUM
        return AlertSeverity.LOW
    if alert_type == AlertType.COMPETITOR_SURGE:
        if magnitude > 300:
            return AlertSeverity.CRITICAL
        if magnitude > 200:
            return AlertSeverity.HIGH
        if magnitude > 100:
            return AlertSeverity.MEDIUM
        return AlertSeverity.LOW

    return AlertSeverity.LOW


async def _create_alert(
    db: AsyncSession,
    org_id: UUID,
    book_id: UUID,
    alert_type: AlertType,
    magnitude: float,
    title: str,
    description: str,
    data: dict | None = None,
) -> ReviewAlert:
    """Create a new review alert."""
    severity = _determine_severity(alert_type, magnitude)

    alert = ReviewAlert(
        org_id=org_id,
        book_id=book_id,
        alert_type=alert_type.value,
        severity=severity.value,
        title=title,
        description=description,
        data=data or {},
    )
    db.add(alert)
    await db.flush()
    logger.info(f"Created {severity.value} alert [{alert_type.value}] for book {book_id}: {title}")
    return alert


async def check_negative_spike(
    db: AsyncSession,
    org_id: UUID,
    book_id: UUID,
    window_days: int = 7,
    thresholds: dict | None = None,
) -> ReviewAlert | None:
    """Check if there's a spike in negative reviews compared to the previous window."""
    thresholds = thresholds or DEFAULT_THRESHOLDS
    now = datetime.now(UTC)
    current_start = now - timedelta(days=window_days)
    previous_start = current_start - timedelta(days=window_days)

    # Count negative reviews in current window
    current_stmt = select(func.count(BookReview.id)).where(
        and_(
            BookReview.org_id == org_id,
            BookReview.book_id == book_id,
            BookReview.sentiment == SentimentLabel.NEGATIVE.value,
            BookReview.review_date >= current_start,
            BookReview.review_date < now,
            BookReview.deleted_at.is_(None),
        )
    )
    current_result = await db.execute(current_stmt)
    current_count = current_result.scalar() or 0

    # Count negative reviews in previous window
    previous_stmt = select(func.count(BookReview.id)).where(
        and_(
            BookReview.org_id == org_id,
            BookReview.book_id == book_id,
            BookReview.sentiment == SentimentLabel.NEGATIVE.value,
            BookReview.review_date >= previous_start,
            BookReview.review_date < current_start,
            BookReview.deleted_at.is_(None),
        )
    )
    previous_result = await db.execute(previous_stmt)
    previous_count = previous_result.scalar() or 0

    if current_count < thresholds["min_reviews_for_alert"]:
        return None

    if previous_count > 0:
        change_pct = ((current_count - previous_count) / previous_count) * 100
    elif current_count > 0:
        change_pct = 100.0
    else:
        return None

    if change_pct >= thresholds["negative_spike_pct"]:
        return await _create_alert(
            db=db,
            org_id=org_id,
            book_id=book_id,
            alert_type=AlertType.NEGATIVE_SPIKE,
            magnitude=change_pct,
            title=f"Negative review spike detected ({current_count} in last {window_days} days)",
            description=(
                f"Negative reviews increased by {change_pct:.0f}% compared to "
                f"the previous {window_days}-day period ({previous_count} -> {current_count})."
            ),
            data={
                "current_count": current_count,
                "previous_count": previous_count,
                "change_pct": round(change_pct, 1),
                "window_days": window_days,
            },
        )
    return None


async def check_velocity_drop(
    db: AsyncSession,
    org_id: UUID,
    book_id: UUID,
    window_days: int = 14,
    thresholds: dict | None = None,
) -> ReviewAlert | None:
    """Check if review velocity has dropped significantly."""
    thresholds = thresholds or DEFAULT_THRESHOLDS
    now = datetime.now(UTC)
    current_start = now - timedelta(days=window_days)
    previous_start = current_start - timedelta(days=window_days)

    # Count reviews in current window
    current_stmt = select(func.count(BookReview.id)).where(
        and_(
            BookReview.org_id == org_id,
            BookReview.book_id == book_id,
            BookReview.review_date >= current_start,
            BookReview.review_date < now,
            BookReview.deleted_at.is_(None),
        )
    )
    current_result = await db.execute(current_stmt)
    current_count = current_result.scalar() or 0

    # Count reviews in previous window
    previous_stmt = select(func.count(BookReview.id)).where(
        and_(
            BookReview.org_id == org_id,
            BookReview.book_id == book_id,
            BookReview.review_date >= previous_start,
            BookReview.review_date < current_start,
            BookReview.deleted_at.is_(None),
        )
    )
    previous_result = await db.execute(previous_stmt)
    previous_count = previous_result.scalar() or 0

    if previous_count < thresholds["min_reviews_for_alert"]:
        return None

    change_pct = ((current_count - previous_count) / previous_count) * 100

    if change_pct <= thresholds["velocity_drop_pct"]:
        return await _create_alert(
            db=db,
            org_id=org_id,
            book_id=book_id,
            alert_type=AlertType.VELOCITY_DROP,
            magnitude=change_pct,
            title="Review velocity drop detected",
            description=(
                f"Review velocity dropped by {abs(change_pct):.0f}% over the "
                f"last {window_days} days ({previous_count} -> {current_count})."
            ),
            data={
                "current_count": current_count,
                "previous_count": previous_count,
                "change_pct": round(change_pct, 1),
                "window_days": window_days,
            },
        )
    return None


async def check_rating_decline(
    db: AsyncSession,
    org_id: UUID,
    book_id: UUID,
    window_days: int = 30,
    thresholds: dict | None = None,
) -> ReviewAlert | None:
    """Check if average star rating has declined significantly."""
    thresholds = thresholds or DEFAULT_THRESHOLDS
    now = datetime.now(UTC)
    current_start = now - timedelta(days=window_days)
    previous_start = current_start - timedelta(days=window_days)

    # Avg rating in current window
    current_stmt = select(func.avg(BookReview.star_rating)).where(
        and_(
            BookReview.org_id == org_id,
            BookReview.book_id == book_id,
            BookReview.review_date >= current_start,
            BookReview.review_date < now,
            BookReview.deleted_at.is_(None),
        )
    )
    current_result = await db.execute(current_stmt)
    current_avg = current_result.scalar()

    # Avg rating in previous window
    previous_stmt = select(func.avg(BookReview.star_rating)).where(
        and_(
            BookReview.org_id == org_id,
            BookReview.book_id == book_id,
            BookReview.review_date >= previous_start,
            BookReview.review_date < current_start,
            BookReview.deleted_at.is_(None),
        )
    )
    previous_result = await db.execute(previous_stmt)
    previous_avg = previous_result.scalar()

    if current_avg is None or previous_avg is None:
        return None

    decline = float(previous_avg) - float(current_avg)

    if decline >= thresholds["rating_decline_threshold"]:
        return await _create_alert(
            db=db,
            org_id=org_id,
            book_id=book_id,
            alert_type=AlertType.RATING_DECLINE,
            magnitude=decline,
            title=f"Star rating decline detected ({float(previous_avg):.1f} -> {float(current_avg):.1f})",
            description=(
                f"Average star rating dropped by {decline:.2f} stars over the "
                f"last {window_days} days (from {float(previous_avg):.2f} to {float(current_avg):.2f})."
            ),
            data={
                "current_avg": round(float(current_avg), 2),
                "previous_avg": round(float(previous_avg), 2),
                "decline": round(decline, 2),
                "window_days": window_days,
            },
        )
    return None


async def check_competitor_surge(
    db: AsyncSession,
    org_id: UUID,
    book_id: UUID,
    window_days: int = 14,
    thresholds: dict | None = None,
) -> ReviewAlert | None:
    """Check if competitor books are seeing a review surge relative to this book."""
    thresholds = thresholds or DEFAULT_THRESHOLDS
    now = datetime.now(UTC)
    current_start = now - timedelta(days=window_days)

    # Count own-book reviews in window
    own_stmt = select(func.count(BookReview.id)).where(
        and_(
            BookReview.org_id == org_id,
            BookReview.book_id == book_id,
            BookReview.is_competitor.is_(False),
            BookReview.review_date >= current_start,
            BookReview.review_date < now,
            BookReview.deleted_at.is_(None),
        )
    )
    own_result = await db.execute(own_stmt)
    own_count = own_result.scalar() or 0

    # Count competitor reviews in window (same org, is_competitor=True)
    comp_stmt = select(func.count(BookReview.id)).where(
        and_(
            BookReview.org_id == org_id,
            BookReview.is_competitor.is_(True),
            BookReview.review_date >= current_start,
            BookReview.review_date < now,
            BookReview.deleted_at.is_(None),
        )
    )
    comp_result = await db.execute(comp_stmt)
    comp_count = comp_result.scalar() or 0

    if own_count == 0 and comp_count == 0:
        return None

    if own_count > 0:
        surge_pct = ((comp_count - own_count) / own_count) * 100
    elif comp_count > 0:
        surge_pct = 100.0
    else:
        return None

    if surge_pct >= thresholds["competitor_surge_pct"]:
        return await _create_alert(
            db=db,
            org_id=org_id,
            book_id=book_id,
            alert_type=AlertType.COMPETITOR_SURGE,
            magnitude=surge_pct,
            title="Competitor review surge detected",
            description=(
                f"Competitor books received {comp_count} reviews while your book "
                f"received {own_count} in the last {window_days} days "
                f"({surge_pct:.0f}% more for competitors)."
            ),
            data={
                "own_count": own_count,
                "competitor_count": comp_count,
                "surge_pct": round(surge_pct, 1),
                "window_days": window_days,
            },
        )
    return None


async def run_all_checks(
    db: AsyncSession,
    org_id: UUID,
    book_id: UUID,
    thresholds: dict | None = None,
) -> list[ReviewAlert]:
    """Run all alert checks for a book. Returns list of newly created alerts."""
    alerts = []

    for check_fn in [
        check_negative_spike,
        check_velocity_drop,
        check_rating_decline,
        check_competitor_surge,
    ]:
        try:
            alert = await check_fn(db, org_id, book_id, thresholds=thresholds)
            if alert:
                alerts.append(alert)
        except (SQLAlchemyError, ValueError, TypeError) as e:
            logger.error(
                "Alert check %s failed for book %s: %s",
                check_fn.__name__,
                book_id,
                e,
                exc_info=True,
            )

    return alerts
