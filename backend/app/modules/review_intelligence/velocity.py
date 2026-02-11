"""Review velocity tracking: daily/weekly/monthly rates, trend detection, anomaly detection."""

import logging
import statistics
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.review_intelligence.models import BookReview, ReviewVelocitySnapshot
from app.modules.review_intelligence.schemas import (
    VelocityDataPoint,
    VelocityPeriod,
    VelocityReport,
    VelocityTrend,
)

logger = logging.getLogger(__name__)


def _period_delta(period: VelocityPeriod) -> timedelta:
    """Return the timedelta for one period unit."""
    if period == VelocityPeriod.DAILY:
        return timedelta(days=1)
    if period == VelocityPeriod.WEEKLY:
        return timedelta(weeks=1)
    if period == VelocityPeriod.MONTHLY:
        return timedelta(days=30)
    return timedelta(days=1)


def _default_lookback(period: VelocityPeriod) -> int:
    """Number of periods to look back by default."""
    if period == VelocityPeriod.DAILY:
        return 30
    if period == VelocityPeriod.WEEKLY or period == VelocityPeriod.MONTHLY:
        return 12
    return 30


def detect_trend(data_points: list[VelocityDataPoint]) -> VelocityTrend:
    """Detect velocity trend from a list of data points.

    Uses simple linear regression on review counts. If the slope is
    significantly positive, trend is RISING; if significantly negative,
    DECLINING; otherwise STABLE.
    """
    if len(data_points) < 3:
        return VelocityTrend.STABLE

    counts = [dp.review_count for dp in data_points]
    n = len(counts)
    x_vals = list(range(n))

    x_mean = sum(x_vals) / n
    y_mean = sum(counts) / n

    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, counts, strict=False))
    denominator = sum((x - x_mean) ** 2 for x in x_vals)

    if denominator == 0:
        return VelocityTrend.STABLE

    slope = numerator / denominator

    # Normalize slope relative to mean
    if y_mean > 0:
        relative_slope = slope / y_mean
    else:
        relative_slope = slope

    if relative_slope > 0.1:
        return VelocityTrend.RISING
    if relative_slope < -0.1:
        return VelocityTrend.DECLINING
    return VelocityTrend.STABLE


def detect_anomalies(
    data_points: list[VelocityDataPoint], z_threshold: float = 2.0
) -> list[dict]:
    """Detect anomalies in review velocity using modified z-score method.

    Uses the median and MAD (Median Absolute Deviation) instead of mean/stdev
    so that multiple outliers do not inflate the spread and mask each other.

    Args:
        data_points: Time-ordered velocity data points.
        z_threshold: Number of standard deviations for anomaly detection.

    Returns:
        List of anomaly dicts with period info and z-score.
    """
    if len(data_points) < 5:
        return []

    counts = [dp.review_count for dp in data_points]
    median = statistics.median(counts)
    mad = statistics.median([abs(c - median) for c in counts])

    # Scale MAD to be comparable to standard deviation for normal distributions
    # (MAD * 1.4826 ≈ stdev for normally distributed data)
    mad_scaled = mad * 1.4826

    if mad_scaled == 0:
        # MAD is zero when the majority of values equal the median.
        # Fall back to mean absolute deviation from the median so that the
        # few differing points are still detectable as anomalies.
        mean_abs_dev = statistics.mean([abs(c - median) for c in counts])
        if mean_abs_dev == 0:
            return []
        center = median
        spread = mean_abs_dev
    else:
        center = median
        spread = mad_scaled

    anomalies = []
    for i, dp in enumerate(data_points):
        z_score = (dp.review_count - center) / spread
        if abs(z_score) > z_threshold:
            anomalies.append(
                {
                    "period_start": dp.period_start.isoformat(),
                    "period_end": dp.period_end.isoformat(),
                    "review_count": dp.review_count,
                    "z_score": round(z_score, 2),
                    "direction": "spike" if z_score > 0 else "drop",
                    "expected_range": {
                        "low": max(0, round(center - z_threshold * spread)),
                        "high": round(center + z_threshold * spread),
                    },
                }
            )

    return anomalies


async def compute_velocity_from_reviews(
    db: AsyncSession,
    org_id: UUID,
    book_id: UUID,
    period: VelocityPeriod = VelocityPeriod.WEEKLY,
    lookback: int | None = None,
) -> VelocityReport:
    """Compute review velocity directly from the book_reviews table.

    Args:
        db: Database session.
        org_id: Organization ID.
        book_id: Book ID.
        period: Granularity of velocity data.
        lookback: Number of periods to look back.

    Returns:
        VelocityReport with data points, rate, trend and anomaly info.
    """
    if lookback is None:
        lookback = _default_lookback(period)

    delta = _period_delta(period)
    now = datetime.now(UTC)
    start_date = now - (delta * lookback)

    # Query reviews grouped by period
    data_points: list[VelocityDataPoint] = []

    for i in range(lookback):
        period_start = start_date + (delta * i)
        period_end = start_date + (delta * (i + 1))

        stmt = select(
            func.count(BookReview.id).label("review_count"),
            func.avg(BookReview.star_rating).label("avg_rating"),
            func.count(
                func.nullif(BookReview.sentiment == "positive", False)
            ).label("positive_count"),
            func.count(
                func.nullif(BookReview.sentiment == "neutral", False)
            ).label("neutral_count"),
            func.count(
                func.nullif(BookReview.sentiment == "negative", False)
            ).label("negative_count"),
        ).where(
            and_(
                BookReview.org_id == org_id,
                BookReview.book_id == book_id,
                BookReview.review_date >= period_start,
                BookReview.review_date < period_end,
                BookReview.deleted_at.is_(None),
            )
        )

        result = await db.execute(stmt)
        row = result.one()

        data_points.append(
            VelocityDataPoint(
                period_start=period_start,
                period_end=period_end,
                review_count=row.review_count or 0,
                avg_rating=round(float(row.avg_rating), 2) if row.avg_rating else None,
                positive_count=row.positive_count or 0,
                neutral_count=row.neutral_count or 0,
                negative_count=row.negative_count or 0,
            )
        )

    # Calculate rates
    current_rate = data_points[-1].review_count if data_points else 0.0
    previous_rate = data_points[-2].review_count if len(data_points) >= 2 else 0.0

    if previous_rate > 0:
        change_pct = ((current_rate - previous_rate) / previous_rate) * 100
    elif current_rate > 0:
        change_pct = 100.0
    else:
        change_pct = 0.0

    trend = detect_trend(data_points)
    anomalies = detect_anomalies(data_points)

    return VelocityReport(
        book_id=book_id,
        period=period,
        data_points=data_points,
        current_rate=float(current_rate),
        previous_rate=float(previous_rate),
        change_pct=round(change_pct, 1),
        trend=trend,
        anomalies=anomalies,
    )


async def compute_velocity_from_snapshots(
    db: AsyncSession,
    org_id: UUID,
    book_id: UUID,
    period: VelocityPeriod = VelocityPeriod.WEEKLY,
    lookback: int | None = None,
) -> VelocityReport:
    """Compute velocity from pre-computed snapshots (faster for large datasets).

    Falls back to compute_velocity_from_reviews if no snapshots exist.
    """
    if lookback is None:
        lookback = _default_lookback(period)

    delta = _period_delta(period)
    now = datetime.now(UTC)
    start_date = now - (delta * lookback)

    stmt = (
        select(ReviewVelocitySnapshot)
        .where(
            and_(
                ReviewVelocitySnapshot.book_id == book_id,
                ReviewVelocitySnapshot.org_id == org_id,
                ReviewVelocitySnapshot.period == period.value,
                ReviewVelocitySnapshot.period_start >= start_date,
                ReviewVelocitySnapshot.deleted_at.is_(None),
            )
        )
        .order_by(ReviewVelocitySnapshot.period_start.asc())
    )

    result = await db.execute(stmt)
    snapshots = result.scalars().all()

    if not snapshots:
        return await compute_velocity_from_reviews(db, org_id, book_id, period, lookback)

    data_points = [
        VelocityDataPoint(
            period_start=s.period_start,
            period_end=s.period_end,
            review_count=s.review_count,
            avg_rating=s.avg_rating,
            positive_count=s.positive_count,
            neutral_count=s.neutral_count,
            negative_count=s.negative_count,
        )
        for s in snapshots
    ]

    current_rate = data_points[-1].review_count if data_points else 0.0
    previous_rate = data_points[-2].review_count if len(data_points) >= 2 else 0.0

    if previous_rate > 0:
        change_pct = ((current_rate - previous_rate) / previous_rate) * 100
    elif current_rate > 0:
        change_pct = 100.0
    else:
        change_pct = 0.0

    trend = detect_trend(data_points)
    anomalies = detect_anomalies(data_points)

    return VelocityReport(
        book_id=book_id,
        period=period,
        data_points=data_points,
        current_rate=float(current_rate),
        previous_rate=float(previous_rate),
        change_pct=round(change_pct, 1),
        trend=trend,
        anomalies=anomalies,
    )


async def save_velocity_snapshot(
    db: AsyncSession,
    org_id: UUID,
    book_id: UUID,
    period: VelocityPeriod,
    period_start: datetime,
    period_end: datetime,
    review_count: int,
    avg_rating: float | None,
    positive_count: int,
    neutral_count: int,
    negative_count: int,
) -> ReviewVelocitySnapshot:
    """Save a velocity snapshot for a book/period."""
    snapshot = ReviewVelocitySnapshot(
        org_id=org_id,
        book_id=book_id,
        period=period.value,
        period_start=period_start,
        period_end=period_end,
        review_count=review_count,
        avg_rating=avg_rating,
        positive_count=positive_count,
        neutral_count=neutral_count,
        negative_count=negative_count,
    )
    db.add(snapshot)
    await db.flush()
    return snapshot
