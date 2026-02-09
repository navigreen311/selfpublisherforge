"""Unit tests for velocity tracking module."""

import pytest
from datetime import datetime, timedelta, timezone

from app.modules.review_intelligence.schemas import (
    VelocityDataPoint,
    VelocityPeriod,
    VelocityTrend,
)
from app.modules.review_intelligence.velocity import (
    _default_lookback,
    _period_delta,
    detect_anomalies,
    detect_trend,
)


# --- Period delta tests ---


class TestPeriodDelta:
    def test_daily_delta(self):
        delta = _period_delta(VelocityPeriod.DAILY)
        assert delta == timedelta(days=1)

    def test_weekly_delta(self):
        delta = _period_delta(VelocityPeriod.WEEKLY)
        assert delta == timedelta(weeks=1)

    def test_monthly_delta(self):
        delta = _period_delta(VelocityPeriod.MONTHLY)
        assert delta == timedelta(days=30)


# --- Default lookback tests ---


class TestDefaultLookback:
    def test_daily_lookback(self):
        assert _default_lookback(VelocityPeriod.DAILY) == 30

    def test_weekly_lookback(self):
        assert _default_lookback(VelocityPeriod.WEEKLY) == 12

    def test_monthly_lookback(self):
        assert _default_lookback(VelocityPeriod.MONTHLY) == 12


# --- Trend detection tests ---


def _make_data_points(counts: list[int]) -> list[VelocityDataPoint]:
    """Helper to create data points from a list of review counts."""
    now = datetime.now(timezone.utc)
    return [
        VelocityDataPoint(
            period_start=now - timedelta(weeks=len(counts) - i),
            period_end=now - timedelta(weeks=len(counts) - i - 1),
            review_count=count,
        )
        for i, count in enumerate(counts)
    ]


class TestTrendDetection:
    def test_rising_trend(self):
        data_points = _make_data_points([2, 4, 6, 8, 10, 12])
        trend = detect_trend(data_points)
        assert trend == VelocityTrend.RISING

    def test_declining_trend(self):
        data_points = _make_data_points([12, 10, 8, 6, 4, 2])
        trend = detect_trend(data_points)
        assert trend == VelocityTrend.DECLINING

    def test_stable_trend(self):
        data_points = _make_data_points([5, 5, 5, 5, 5, 5])
        trend = detect_trend(data_points)
        assert trend == VelocityTrend.STABLE

    def test_slightly_rising_stable(self):
        """Small variations should still be STABLE."""
        data_points = _make_data_points([10, 10, 11, 10, 11, 10])
        trend = detect_trend(data_points)
        assert trend == VelocityTrend.STABLE

    def test_too_few_points_stable(self):
        """Less than 3 points should always return STABLE."""
        data_points = _make_data_points([5, 10])
        trend = detect_trend(data_points)
        assert trend == VelocityTrend.STABLE

    def test_empty_points_stable(self):
        trend = detect_trend([])
        assert trend == VelocityTrend.STABLE

    def test_single_point_stable(self):
        data_points = _make_data_points([5])
        trend = detect_trend(data_points)
        assert trend == VelocityTrend.STABLE

    def test_zero_counts_stable(self):
        data_points = _make_data_points([0, 0, 0, 0, 0])
        trend = detect_trend(data_points)
        assert trend == VelocityTrend.STABLE

    def test_sharp_rise(self):
        data_points = _make_data_points([1, 2, 5, 10, 20, 40])
        trend = detect_trend(data_points)
        assert trend == VelocityTrend.RISING

    def test_sharp_decline(self):
        data_points = _make_data_points([40, 20, 10, 5, 2, 1])
        trend = detect_trend(data_points)
        assert trend == VelocityTrend.DECLINING

    def test_v_shape_recovery(self):
        """V-shape recovery could be stable or rising."""
        data_points = _make_data_points([10, 5, 2, 5, 10, 15])
        trend = detect_trend(data_points)
        # The overall linear slope is slightly positive
        assert trend in (VelocityTrend.RISING, VelocityTrend.STABLE)


# --- Anomaly detection tests ---


class TestAnomalyDetection:
    def test_no_anomalies_uniform(self):
        data_points = _make_data_points([10, 10, 10, 10, 10, 10, 10])
        anomalies = detect_anomalies(data_points)
        assert anomalies == []

    def test_spike_anomaly(self):
        # Normal range is ~5, one big spike at 50
        data_points = _make_data_points([5, 5, 5, 5, 50, 5, 5])
        anomalies = detect_anomalies(data_points)
        assert len(anomalies) >= 1
        spike = anomalies[0]
        assert spike["direction"] == "spike"
        assert spike["review_count"] == 50

    def test_drop_anomaly(self):
        # Normal range is ~30, one big drop to 0
        data_points = _make_data_points([30, 30, 30, 30, 0, 30, 30])
        anomalies = detect_anomalies(data_points)
        assert len(anomalies) >= 1
        drop = [a for a in anomalies if a["direction"] == "drop"]
        assert len(drop) >= 1
        assert drop[0]["review_count"] == 0

    def test_too_few_points_no_anomalies(self):
        """Need at least 5 points for anomaly detection."""
        data_points = _make_data_points([5, 5, 50, 5])
        anomalies = detect_anomalies(data_points)
        assert anomalies == []

    def test_anomaly_z_threshold(self):
        """Higher threshold should detect fewer anomalies."""
        data_points = _make_data_points([5, 5, 5, 5, 15, 5, 5])

        # Low threshold
        anomalies_low = detect_anomalies(data_points, z_threshold=1.5)
        # High threshold
        anomalies_high = detect_anomalies(data_points, z_threshold=3.0)

        assert len(anomalies_low) >= len(anomalies_high)

    def test_anomaly_has_expected_range(self):
        data_points = _make_data_points([5, 5, 5, 5, 50, 5, 5])
        anomalies = detect_anomalies(data_points)
        assert len(anomalies) >= 1
        assert "expected_range" in anomalies[0]
        assert "low" in anomalies[0]["expected_range"]
        assert "high" in anomalies[0]["expected_range"]

    def test_anomaly_has_z_score(self):
        data_points = _make_data_points([5, 5, 5, 5, 50, 5, 5])
        anomalies = detect_anomalies(data_points)
        assert len(anomalies) >= 1
        assert "z_score" in anomalies[0]
        assert isinstance(anomalies[0]["z_score"], float)

    def test_no_anomalies_all_zeros(self):
        """All zeros => stdev is 0, no anomalies."""
        data_points = _make_data_points([0, 0, 0, 0, 0, 0])
        anomalies = detect_anomalies(data_points)
        assert anomalies == []

    def test_anomaly_period_info(self):
        data_points = _make_data_points([5, 5, 5, 5, 50, 5, 5])
        anomalies = detect_anomalies(data_points)
        assert len(anomalies) >= 1
        assert "period_start" in anomalies[0]
        assert "period_end" in anomalies[0]

    def test_multiple_anomalies(self):
        """Multiple anomalies in one dataset."""
        data_points = _make_data_points([5, 50, 5, 5, 5, 50, 5])
        anomalies = detect_anomalies(data_points)
        assert len(anomalies) >= 2


# --- Integration-style pure function tests ---


class TestVelocityComputations:
    def test_trend_and_anomaly_combined(self):
        """Rising trend with one anomaly spike."""
        data_points = _make_data_points([2, 4, 6, 8, 50, 12, 14])
        trend = detect_trend(data_points)
        anomalies = detect_anomalies(data_points)

        # Should still detect rising despite the spike
        assert trend in (VelocityTrend.RISING, VelocityTrend.STABLE)
        assert len(anomalies) >= 1

    def test_declining_with_anomaly_drop(self):
        """Declining trend with one anomaly drop."""
        data_points = _make_data_points([30, 25, 20, 0, 15, 10, 5])
        trend = detect_trend(data_points)
        anomalies = detect_anomalies(data_points)

        assert trend == VelocityTrend.DECLINING
        assert len(anomalies) >= 1

    def test_data_point_rating_info(self):
        """Data points can carry rating distribution info."""
        now = datetime.now(timezone.utc)
        dp = VelocityDataPoint(
            period_start=now - timedelta(weeks=1),
            period_end=now,
            review_count=10,
            avg_rating=4.2,
            positive_count=7,
            neutral_count=2,
            negative_count=1,
        )
        assert dp.review_count == 10
        assert dp.avg_rating == 4.2
        assert dp.positive_count + dp.neutral_count + dp.negative_count == 10
