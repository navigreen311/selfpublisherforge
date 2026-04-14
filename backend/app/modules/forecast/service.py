"""Revenue forecasting service.

Uses simple ordinary-least-squares linear regression over daily revenue
from the past lookback window (2x horizon, min 90 days) and projects forward
with a seasonal month-of-year adjustment factor.

No ML frameworks required — pure stdlib math.
"""

from __future__ import annotations

import math
import uuid
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.models import RoyaltyRecord
from app.modules.forecast.schemas import (
    ForecastPoint,
    ForecastResponse,
    ForecastSummary,
)

# Month-of-year multipliers (rough seasonal baseline per spec).
# Values normalized around 1.0 — Nov/Dec up for holiday gifts, Jan up
# slightly for New Year purchases, summer slightly softer.
SEASONAL_FACTORS: dict[int, float] = {
    1: 1.05,   # Jan
    2: 0.98,
    3: 1.00,
    4: 1.00,
    5: 0.98,
    6: 0.95,
    7: 0.95,
    8: 0.97,
    9: 1.02,
    10: 1.05,
    11: 1.20,  # Nov — holiday shopping
    12: 1.30,  # Dec — peak gift season
}


def _seasonal_factor(d: date) -> float:
    return SEASONAL_FACTORS.get(d.month, 1.0)


def _linreg(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    """Return (slope, intercept, r_squared) for simple OLS."""
    n = len(xs)
    if n < 2:
        return 0.0, (ys[0] if ys else 0.0), 0.0
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=False))
    den = sum((x - mean_x) ** 2 for x in xs)
    if den == 0:
        return 0.0, mean_y, 0.0
    slope = num / den
    intercept = mean_y - slope * mean_x
    # r^2
    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys, strict=False))
    r2 = 0.0 if ss_tot == 0 else max(0.0, 1.0 - ss_res / ss_tot)
    return slope, intercept, r2


def _residual_std(xs: list[float], ys: list[float], slope: float, intercept: float) -> float:
    if len(xs) < 2:
        return 0.0
    residuals = [y - (slope * x + intercept) for x, y in zip(xs, ys, strict=False)]
    mean_r = sum(residuals) / len(residuals)
    var = sum((r - mean_r) ** 2 for r in residuals) / max(1, len(residuals) - 1)
    return math.sqrt(var)


async def _daily_revenue(
    db: AsyncSession,
    org_id: uuid.UUID,
    start: datetime,
    end: datetime,
) -> dict[date, float]:
    """Aggregate net_revenue by calendar day from royalty_records."""
    stmt = (
        select(RoyaltyRecord.period_start, RoyaltyRecord.net_revenue)
        .where(
            and_(
                RoyaltyRecord.org_id == org_id,
                RoyaltyRecord.deleted_at.is_(None),
                RoyaltyRecord.period_start >= start,
                RoyaltyRecord.period_start <= end,
            )
        )
    )
    result = await db.execute(stmt)
    rows = result.all()
    bucket: dict[date, float] = defaultdict(float)
    for period_start, net_revenue in rows:
        if period_start is None:
            continue
        d = period_start.date() if isinstance(period_start, datetime) else period_start
        bucket[d] += float(net_revenue or 0)
    return dict(bucket)


async def forecast_revenue(
    db: AsyncSession,
    org_id: uuid.UUID,
    horizon_days: int,
) -> ForecastResponse:
    """Produce a revenue forecast for the given horizon."""
    if horizon_days not in (30, 90, 180):
        horizon_days = 30

    today = datetime.now(UTC).date()
    lookback_days = max(90, horizon_days * 2)
    lookback_start = today - timedelta(days=lookback_days)

    daily = await _daily_revenue(
        db,
        org_id,
        datetime.combine(lookback_start, datetime.min.time()).replace(tzinfo=UTC),
        datetime.combine(today, datetime.max.time()).replace(tzinfo=UTC),
    )

    # Build a dense daily series, filling zero for missing days.
    xs: list[float] = []
    ys: list[float] = []
    historical_points: list[ForecastPoint] = []
    day = lookback_start
    i = 0
    while day <= today:
        val = daily.get(day, 0.0)
        xs.append(float(i))
        ys.append(val)
        historical_points.append(ForecastPoint(date=day, actual=round(val, 2)))
        day += timedelta(days=1)
        i += 1

    past_actual_total = sum(ys)
    has_data = any(v > 0 for v in ys)

    slope, intercept, r2 = _linreg(xs, ys)
    resid_std = _residual_std(xs, ys, slope, intercept)

    # 1-sigma band as a conservative confidence interval.
    forecast_points: list[ForecastPoint] = []
    projected_total = 0.0
    low_total = 0.0
    high_total = 0.0

    for step in range(1, horizon_days + 1):
        xi = float(len(xs) + step - 1)
        base = slope * xi + intercept
        base = max(0.0, base)
        fdate = today + timedelta(days=step)
        seasonal = _seasonal_factor(fdate)
        projected = base * seasonal
        low = max(0.0, (base - resid_std) * seasonal)
        high = (base + resid_std) * seasonal
        projected_total += projected
        low_total += low
        high_total += high
        forecast_points.append(
            ForecastPoint(
                date=fdate,
                projected=round(projected, 2),
                conf_low=round(low, 2),
                conf_high=round(high, 2),
            )
        )

    # Trend pct: slope per day as a % of current mean daily revenue.
    mean_daily = (sum(ys) / len(ys)) if ys else 0.0
    trend_pct = 0.0
    if mean_daily > 0:
        # Expressed as % change over the horizon.
        trend_pct = (slope * horizon_days / mean_daily) * 100.0

    # Confidence: blend of r^2 and data volume.
    data_vol = min(1.0, len(ys) / 180.0)
    confidence = round(max(0.0, min(1.0, 0.5 * r2 + 0.5 * data_vol)) if has_data else 0.0, 3)

    chart_data = historical_points + forecast_points

    insights: list[str] = []
    if has_data:
        # Flag upcoming seasonal bumps within horizon.
        months_in_horizon = {(today + timedelta(days=s)).month for s in range(1, horizon_days + 1)}
        if 11 in months_in_horizon or 12 in months_in_horizon:
            insights.append("Holiday season (Nov-Dec) typically boosts sales 20-30%.")
        if 1 in months_in_horizon:
            insights.append("January often sees a New Year resolution-driven bump.")
        if trend_pct > 5:
            insights.append(f"Revenue trending up {trend_pct:.1f}% over horizon.")
        elif trend_pct < -5:
            insights.append(f"Revenue trending down {abs(trend_pct):.1f}% — consider promos.")

    summary = ForecastSummary(
        horizon_days=horizon_days,
        expected_revenue=round(projected_total, 2),
        best_case=round(high_total, 2),
        worst_case=round(low_total, 2),
        trend_pct=round(trend_pct, 2),
        confidence=confidence,
        past_actual_total=round(past_actual_total, 2),
    )

    return ForecastResponse(
        horizon_days=horizon_days,
        summary=summary,
        chart_data=chart_data,
        seasonality_insights=insights,
        currency="USD",
    )
