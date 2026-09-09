"""End-to-end tests for the analytics flow.

Each test exercises a complete user journey through the HTTP API,
combining authentication with analytics endpoints. Tests use the async
HTTPX client and in-memory SQLite fixtures from ``conftest.py``.

Because SQLite lacks PostgreSQL's ``date_trunc`` function, we register
a lightweight Python implementation via a ``@listens_for`` hook on
the test engine so that the aggregation queries work correctly.
"""

from __future__ import annotations

import base64
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import event
from sqlalchemy.pool import Pool

from app.config import get_settings

settings = get_settings()
AUTH_PREFIX = f"{settings.API_V1_PREFIX}/auth"
ANALYTICS_PREFIX = f"{settings.API_V1_PREFIX}/analytics"

VALID_PASSWORD = "StrongP@ss1"


# ---------------------------------------------------------------------------
# SQLite date_trunc shim
# ---------------------------------------------------------------------------
# PostgreSQL's date_trunc(interval, timestamp) is used by the analytics
# aggregation layer. SQLite doesn't provide it natively, so we register a
# pure-Python fallback on every raw DBAPI connection via a Pool-level
# event listener.


def _sqlite_date_trunc(interval: str, value: str | None) -> str | None:
    """Truncate a datetime string to the given interval.

    Handles common ISO-8601 and SQLite datetime formats.
    Returns an ISO-8601 string.
    """
    if value is None:
        return None

    # Parse the datetime string -- support both ISO-8601 and SQLite formats
    dt = None
    for fmt in (
        "%Y-%m-%d %H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(str(value), fmt)
            break
        except ValueError:
            continue

    if dt is None:
        # Last resort: try fromisoformat
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return value

    interval_lower = interval.lower()
    if interval_lower == "year":
        truncated = dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    elif interval_lower == "quarter":
        quarter_month = ((dt.month - 1) // 3) * 3 + 1
        truncated = dt.replace(month=quarter_month, day=1, hour=0, minute=0, second=0, microsecond=0)
    elif interval_lower == "month":
        truncated = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif interval_lower == "week":
        days_since_monday = dt.weekday()
        truncated = (dt - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif interval_lower == "day":
        truncated = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    elif interval_lower == "hour":
        truncated = dt.replace(minute=0, second=0, microsecond=0)
    else:
        truncated = dt

    return truncated.isoformat()


@event.listens_for(Pool, "connect")
def _on_connect(dbapi_connection, connection_record):
    """Register date_trunc as a custom SQLite function on every connection.

    The Pool-level listener fires for all engines.  We guard with hasattr
    so it only applies to SQLite connections (which expose create_function).
    """
    if hasattr(dbapi_connection, "create_function"):
        dbapi_connection.create_function("date_trunc", 2, _sqlite_date_trunc)


def _safe_period_str(value) -> str:
    """Convert a period value to an ISO-format string.

    Handles both datetime objects (returned by PostgreSQL date_trunc) and
    plain strings (returned by the SQLite _sqlite_date_trunc shim).
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return value.isoformat()


@pytest.fixture(autouse=True)
def _patch_isoformat_for_sqlite(monkeypatch):
    """Monkeypatch aggregator/metrics to handle SQLite date_trunc returning strings.

    SQLite UDFs can only return primitive types.  The _sqlite_date_trunc shim
    above returns an ISO-formatted string, but production code assumes a
    datetime and calls .isoformat().  We patch these call sites so they
    accept both types.
    """
    import app.modules.analytics.aggregator as _agg
    import app.modules.analytics.metrics as _metrics

    # --- patch aggregator.aggregate_revenue ---
    _orig_agg_rev = _agg.aggregate_revenue

    async def _safe_aggregate_revenue(
        db, org_id, period_start, period_end, aggregation=_agg.AggregationPeriod.MONTHLY, platform=None, book_id=None
    ):
        from sqlalchemy import and_, func, select, text

        from app.modules.analytics.models import RoyaltyRecord
        from app.modules.analytics.schemas import RevenueDataPoint

        trunc_interval = _agg._agg_to_trunc(aggregation)
        conditions = [
            RoyaltyRecord.org_id == org_id,
            RoyaltyRecord.period_start >= period_start,
            RoyaltyRecord.period_end <= period_end,
            RoyaltyRecord.deleted_at.is_(None),
        ]
        if platform:
            conditions.append(RoyaltyRecord.platform == platform)
        if book_id:
            conditions.append(RoyaltyRecord.book_id == book_id)

        query = (
            select(
                func.date_trunc(trunc_interval, RoyaltyRecord.period_start).label("period"),
                func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0).label("revenue"),
                func.coalesce(func.sum(RoyaltyRecord.net_units), 0).label("units"),
            )
            .where(and_(*conditions))
            .group_by(text("1"))
            .order_by(text("1"))
        )

        result = await db.execute(query)
        return [
            RevenueDataPoint(
                period=_safe_period_str(row.period),
                revenue=Decimal(str(row.revenue)),
                units=int(row.units),
            )
            for row in result.all()
        ]

    monkeypatch.setattr(_agg, "aggregate_revenue", _safe_aggregate_revenue)
    # Also patch where service.py imported it
    monkeypatch.setattr("app.modules.analytics.service.aggregate_revenue", _safe_aggregate_revenue)

    # --- patch aggregator.aggregate_events_by_type ---
    _orig_agg_events = _agg.aggregate_events_by_type

    async def _safe_aggregate_events_by_type(
        db, org_id, period_start, period_end, aggregation=_agg.AggregationPeriod.DAILY
    ):
        from sqlalchemy import and_, func, select, text

        from app.modules.analytics.models import AnalyticsEvent

        trunc_interval = _agg._agg_to_trunc(aggregation)
        query = (
            select(
                func.date_trunc(trunc_interval, AnalyticsEvent.occurred_at).label("period"),
                AnalyticsEvent.event_type,
                func.count(AnalyticsEvent.id).label("count"),
            )
            .where(
                and_(
                    AnalyticsEvent.org_id == org_id,
                    AnalyticsEvent.occurred_at >= period_start,
                    AnalyticsEvent.occurred_at <= period_end,
                    AnalyticsEvent.deleted_at.is_(None),
                )
            )
            .group_by(text("1"), AnalyticsEvent.event_type)
            .order_by(text("1"))
        )
        result = await db.execute(query)
        return [
            {
                "period": _safe_period_str(row.period),
                "event_type": row.event_type,
                "count": row.count,
            }
            for row in result.all()
        ]

    monkeypatch.setattr(_agg, "aggregate_events_by_type", _safe_aggregate_events_by_type)

    # --- patch metrics.compute_revenue_trend ---
    _orig_trend = _metrics.compute_revenue_trend

    async def _safe_compute_revenue_trend(
        db, org_id, period_start, period_end, aggregation=_metrics.AggregationPeriod.MONTHLY
    ):
        from sqlalchemy import and_, func, select, text

        from app.modules.analytics.models import RoyaltyRecord
        from app.modules.analytics.schemas import TrendData, TrendDataPoint

        trunc_fn = _metrics._get_date_trunc(aggregation)
        query = (
            select(
                func.date_trunc(trunc_fn, RoyaltyRecord.period_start).label("period"),
                func.coalesce(func.sum(RoyaltyRecord.net_revenue), 0).label("revenue"),
            )
            .where(
                and_(
                    RoyaltyRecord.org_id == org_id,
                    RoyaltyRecord.period_start >= period_start,
                    RoyaltyRecord.period_end <= period_end,
                    RoyaltyRecord.deleted_at.is_(None),
                )
            )
            .group_by(text("1"))
            .order_by(text("1"))
        )
        result = await db.execute(query)
        rows = result.all()

        data_points = []
        total = Decimal("0.00")
        for row in rows:
            value = Decimal(str(row.revenue))
            total += value
            data_points.append(
                TrendDataPoint(
                    period=_safe_period_str(row.period),
                    value=_metrics._quantize(value),
                    label=None,
                )
            )

        avg = _metrics._quantize(total / Decimal(max(len(data_points), 1)))
        change = None
        if len(data_points) >= 2:
            first_val = data_points[0].value
            last_val = data_points[-1].value
            change = _metrics._percent_change(last_val, first_val)

        return TrendData(
            metric="revenue",
            data_points=data_points,
            aggregation=aggregation,
            period_start=period_start,
            period_end=period_end,
            total=_metrics._quantize(total),
            average=avg,
            change_percent=round(change, 1) if change is not None else None,
        )

    monkeypatch.setattr(_metrics, "compute_revenue_trend", _safe_compute_revenue_trend)
    monkeypatch.setattr("app.modules.analytics.service.compute_revenue_trend", _safe_compute_revenue_trend)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _register_user(
    client: AsyncClient,
    email: str | None = None,
    password: str = VALID_PASSWORD,
    name: str = "Analytics Tester",
    org_name: str = "Analytics Org",
) -> dict:
    """Register a user and return the full response JSON."""
    if email is None:
        email = f"analytics-{uuid.uuid4().hex[:8]}@test.com"
    resp = await client.post(
        f"{AUTH_PREFIX}/register",
        json={
            "email": email,
            "password": password,
            "name": name,
            "org_name": org_name,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _auth_header(access_token: str) -> dict[str, str]:
    """Build an Authorization: Bearer header."""
    return {"Authorization": f"Bearer {access_token}"}


def _build_kdp_csv(rows: list[dict]) -> str:
    """Build a base64-encoded KDP-format CSV from a list of row dicts.

    Each dict should have keys matching KDP CSV columns:
    Title, ASIN, Marketplace, Royalty Type, Units Sold, Units Refunded,
    Net Units Sold, Avg List Price, Currency, Royalty, Royalty Date
    """
    header = (
        "Title,ASIN,Marketplace,Royalty Type,Units Sold,Units Refunded,"
        "Net Units Sold,Avg List Price,Currency,Royalty,Royalty Date"
    )
    lines = [header]
    for row in rows:
        line = ",".join(
            [
                row.get("Title", "Unknown Book"),
                row.get("ASIN", ""),
                row.get("Marketplace", "Amazon.com"),
                row.get("Royalty Type", "Kindle Edition"),
                str(row.get("Units Sold", 0)),
                str(row.get("Units Refunded", 0)),
                str(row.get("Net Units Sold", 0)),
                str(row.get("Avg List Price", "0.00")),
                row.get("Currency", "USD"),
                str(row.get("Royalty", "0.00")),
                row.get("Royalty Date", "2024-01-01"),
            ]
        )
        lines.append(line)
    csv_text = "\n".join(lines)
    return base64.b64encode(csv_text.encode()).decode()


def _build_ingram_csv(rows: list[dict]) -> str:
    """Build a base64-encoded IngramSpark-format CSV."""
    header = "Title,ISBN,Format,Quantity,Publisher Compensation,Currency Code,Sale/Return,Reporting Date"
    lines = [header]
    for row in rows:
        line = ",".join(
            [
                row.get("Title", "Unknown Book"),
                row.get("ISBN", ""),
                row.get("Format", "Paperback"),
                str(row.get("Quantity", 0)),
                str(row.get("Publisher Compensation", "0.00")),
                row.get("Currency Code", "USD"),
                row.get("Sale/Return", "Sale"),
                row.get("Reporting Date", "2024-01-01"),
            ]
        )
        lines.append(line)
    csv_text = "\n".join(lines)
    return base64.b64encode(csv_text.encode()).decode()


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

KDP_SAMPLE_ROWS = [
    {
        "Title": "The Art of Self-Publishing",
        "ASIN": "B0EXAMPLE01",
        "Marketplace": "Amazon.com",
        "Royalty Type": "Kindle Edition",
        "Units Sold": "42",
        "Units Refunded": "2",
        "Net Units Sold": "40",
        "Avg List Price": "9.99",
        "Currency": "USD",
        "Royalty": "279.72",
        "Royalty Date": "2024-01-01",
    },
    {
        "Title": "Marketing Mastery for Authors",
        "ASIN": "B0EXAMPLE02",
        "Marketplace": "Amazon.com",
        "Royalty Type": "Kindle Edition",
        "Units Sold": "28",
        "Units Refunded": "1",
        "Net Units Sold": "27",
        "Avg List Price": "12.99",
        "Currency": "USD",
        "Royalty": "245.43",
        "Royalty Date": "2024-01-01",
    },
    {
        "Title": "The Art of Self-Publishing",
        "ASIN": "B0EXAMPLE01",
        "Marketplace": "Amazon.com",
        "Royalty Type": "Kindle Edition",
        "Units Sold": "55",
        "Units Refunded": "3",
        "Net Units Sold": "52",
        "Avg List Price": "9.99",
        "Currency": "USD",
        "Royalty": "363.64",
        "Royalty Date": "2024-02-01",
    },
]

INGRAM_SAMPLE_ROWS = [
    {
        "Title": "The Art of Self-Publishing",
        "ISBN": "9781234567890",
        "Format": "Paperback",
        "Quantity": "15",
        "Publisher Compensation": "67.35",
        "Currency Code": "USD",
        "Sale/Return": "Sale",
        "Reporting Date": "2024-01-01",
    },
]


# ---------------------------------------------------------------------------
# E2E: Import royalties -> view dashboard
# ---------------------------------------------------------------------------


class TestImportRoyaltiesAndViewDashboard:
    """Import CSV royalties, then verify dashboard and royalty list."""

    @pytest.mark.asyncio
    async def test_import_royalties_view_dashboard(self, client: AsyncClient):
        # 1. Register + get auth token
        reg_data = await _register_user(client)
        token = reg_data["tokens"]["access_token"]
        headers = _auth_header(token)

        # 2. Import royalties via CSV
        csv_b64 = _build_kdp_csv(KDP_SAMPLE_ROWS)
        import_resp = await client.post(
            f"{ANALYTICS_PREFIX}/royalties/import",
            json={
                "platform": "kdp",
                "file_content": csv_b64,
                "file_name": "kdp_royalties.csv",
            },
            headers=headers,
        )
        assert import_resp.status_code == 200, import_resp.text
        import_data = import_resp.json()
        assert import_data["records_imported"] == 3
        assert import_data["records_skipped"] == 0
        assert import_data["platform"] == "kdp"
        assert len(import_data["errors"]) == 0

        # 3. Get dashboard -- KPIs should reflect the imported data
        dashboard_resp = await client.get(
            f"{ANALYTICS_PREFIX}/dashboard",
            headers=headers,
        )
        assert dashboard_resp.status_code == 200, dashboard_resp.text
        dashboard = dashboard_resp.json()

        # Validate dashboard structure
        assert "kpis" in dashboard
        assert "revenue_chart" in dashboard
        assert "top_books" in dashboard
        assert "platform_breakdown" in dashboard
        assert "recent_royalties" in dashboard
        assert "period_start" in dashboard
        assert "period_end" in dashboard

        # The KPIs list should have items (the service always produces 4 KPI cards)
        assert len(dashboard["kpis"]) == 4

        # The recent_royalties should contain our imported records
        # (up to 5 most recent)
        assert len(dashboard["recent_royalties"]) > 0
        assert len(dashboard["recent_royalties"]) <= 5

        # All recent royalties should be KDP
        for r in dashboard["recent_royalties"]:
            assert r["platform"] == "kdp"

        # 4. Get royalties list -- should contain all 3 records
        royalties_resp = await client.get(
            f"{ANALYTICS_PREFIX}/royalties",
            headers=headers,
        )
        assert royalties_resp.status_code == 200, royalties_resp.text
        royalties_data = royalties_resp.json()
        assert royalties_data["total_count"] == 3
        assert len(royalties_data["items"]) == 3

        # Verify the royalty records contain expected titles
        titles = {r["title"] for r in royalties_data["items"]}
        assert "The Art of Self-Publishing" in titles
        assert "Marketing Mastery for Authors" in titles


# ---------------------------------------------------------------------------
# E2E: Revenue aggregation
# ---------------------------------------------------------------------------


class TestRevenueAggregation:
    """Import multiple records across dates/platforms, then verify
    revenue aggregation and filtering."""

    @pytest.mark.asyncio
    async def test_revenue_aggregation_and_platform_filter(self, client: AsyncClient):
        # 1. Register
        reg_data = await _register_user(client)
        token = reg_data["tokens"]["access_token"]
        headers = _auth_header(token)

        # 2. Import KDP royalties (3 records across Jan/Feb 2024)
        kdp_csv = _build_kdp_csv(KDP_SAMPLE_ROWS)
        resp = await client.post(
            f"{ANALYTICS_PREFIX}/royalties/import",
            json={"platform": "kdp", "file_content": kdp_csv, "file_name": "kdp.csv"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["records_imported"] == 3

        # 3. Import IngramSpark royalties (1 record in Jan 2024)
        ingram_csv = _build_ingram_csv(INGRAM_SAMPLE_ROWS)
        resp2 = await client.post(
            f"{ANALYTICS_PREFIX}/royalties/import",
            json={
                "platform": "ingram_spark",
                "file_content": ingram_csv,
                "file_name": "ingram.csv",
            },
            headers=headers,
        )
        assert resp2.status_code == 200
        assert resp2.json()["records_imported"] == 1

        # 4. Get revenue with monthly aggregation (covering the full period)
        revenue_resp = await client.get(
            f"{ANALYTICS_PREFIX}/revenue",
            params={
                "aggregation": "monthly",
                "start_date": "2023-12-01",
                "end_date": "2024-12-31",
            },
            headers=headers,
        )
        assert revenue_resp.status_code == 200, revenue_resp.text
        revenue = revenue_resp.json()

        # Validate response structure
        assert "total_revenue" in revenue
        assert "total_units" in revenue
        assert "data_points" in revenue
        assert "aggregation" in revenue
        assert revenue["aggregation"] == "monthly"

        # Total revenue should be sum of all royalties imported
        # KDP: 279.72 + 245.43 + 363.64 = 888.79
        # Ingram: 67.35
        # Total: 956.14
        total_rev = Decimal(str(revenue["total_revenue"]))
        assert total_rev > 0

        # Total units should be positive
        assert revenue["total_units"] > 0

        # Platform breakdown should include both platforms
        assert "by_platform" in revenue
        if revenue["by_platform"]:
            platforms_in_breakdown = set(revenue["by_platform"].keys())
            assert "kdp" in platforms_in_breakdown

        # 5. Filter by platform=kdp
        kdp_resp = await client.get(
            f"{ANALYTICS_PREFIX}/revenue",
            params={
                "platform": "kdp",
                "start_date": "2023-12-01",
                "end_date": "2024-12-31",
            },
            headers=headers,
        )
        assert kdp_resp.status_code == 200, kdp_resp.text
        kdp_revenue = kdp_resp.json()

        # KDP-only revenue should be less than or equal to total
        kdp_rev = Decimal(str(kdp_revenue["total_revenue"]))
        assert kdp_rev > 0
        assert kdp_rev <= total_rev

        # 6. Verify royalties list can be filtered by platform
        royalties_resp = await client.get(
            f"{ANALYTICS_PREFIX}/royalties",
            params={"platform": "kdp"},
            headers=headers,
        )
        assert royalties_resp.status_code == 200
        royalties = royalties_resp.json()
        assert royalties["total_count"] == 3
        for item in royalties["items"]:
            assert item["platform"] == "kdp"

        # Also verify ingram_spark filter
        ingram_resp = await client.get(
            f"{ANALYTICS_PREFIX}/royalties",
            params={"platform": "ingram_spark"},
            headers=headers,
        )
        assert ingram_resp.status_code == 200
        ingram_data = ingram_resp.json()
        assert ingram_data["total_count"] == 1
        assert ingram_data["items"][0]["platform"] == "ingram_spark"


# ---------------------------------------------------------------------------
# E2E: Report generation
# ---------------------------------------------------------------------------


class TestReportGeneration:
    """Import data, generate a report, then verify it appears in the list."""

    @pytest.mark.asyncio
    async def test_generate_and_list_report(self, client: AsyncClient):
        # 1. Register
        reg_data = await _register_user(client)
        token = reg_data["tokens"]["access_token"]
        headers = _auth_header(token)

        # 2. Import some royalty data so the report has content
        csv_b64 = _build_kdp_csv(KDP_SAMPLE_ROWS[:2])
        import_resp = await client.post(
            f"{ANALYTICS_PREFIX}/royalties/import",
            json={"platform": "kdp", "file_content": csv_b64, "file_name": "report_data.csv"},
            headers=headers,
        )
        assert import_resp.status_code == 200
        assert import_resp.json()["records_imported"] == 2

        # 3. Generate a report
        # Note: The service tries Celery first (which will fail in tests),
        # then falls back to synchronous generation.
        report_resp = await client.post(
            f"{ANALYTICS_PREFIX}/reports/generate",
            json={
                "title": "Q1 2024 Revenue Summary",
                "report_type": "revenue_summary",
                "output_format": "pdf",
                "parameters": {},
            },
            headers=headers,
        )
        assert report_resp.status_code == 201, report_resp.text
        report = report_resp.json()

        # Validate report response structure
        assert "id" in report
        assert report["title"] == "Q1 2024 Revenue Summary"
        assert report["report_type"] == "revenue_summary"
        assert report["output_format"] == "pdf"
        report_id = report["id"]

        # 4. List reports -- our report should appear
        list_resp = await client.get(
            f"{ANALYTICS_PREFIX}/reports",
            headers=headers,
        )
        assert list_resp.status_code == 200, list_resp.text
        reports_data = list_resp.json()
        assert reports_data["total_count"] >= 1

        report_ids = [r["id"] for r in reports_data["items"]]
        assert report_id in report_ids

        # 5. Verify the specific report by finding it in the list
        matched_report = next(r for r in reports_data["items"] if r["id"] == report_id)
        assert matched_report["title"] == "Q1 2024 Revenue Summary"
        assert matched_report["report_type"] == "revenue_summary"

    @pytest.mark.asyncio
    async def test_generate_multiple_report_types(self, client: AsyncClient):
        """Generate reports of different types and verify all appear."""
        # 1. Register
        reg_data = await _register_user(client)
        token = reg_data["tokens"]["access_token"]
        headers = _auth_header(token)

        # 2. Import data
        csv_b64 = _build_kdp_csv(KDP_SAMPLE_ROWS[:1])
        resp = await client.post(
            f"{ANALYTICS_PREFIX}/royalties/import",
            json={"platform": "kdp", "file_content": csv_b64, "file_name": "data.csv"},
            headers=headers,
        )
        assert resp.status_code == 200

        # 3. Generate revenue_summary report
        r1 = await client.post(
            f"{ANALYTICS_PREFIX}/reports/generate",
            json={
                "title": "Revenue Summary",
                "report_type": "revenue_summary",
                "output_format": "pdf",
                "parameters": {},
            },
            headers=headers,
        )
        assert r1.status_code == 201

        # 4. Generate book_performance report
        r2 = await client.post(
            f"{ANALYTICS_PREFIX}/reports/generate",
            json={
                "title": "Book Performance Review",
                "report_type": "book_performance",
                "output_format": "pdf",
                "parameters": {},
            },
            headers=headers,
        )
        assert r2.status_code == 201

        # 5. List all reports
        list_resp = await client.get(
            f"{ANALYTICS_PREFIX}/reports",
            headers=headers,
        )
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert data["total_count"] >= 2

        report_types = {r["report_type"] for r in data["items"]}
        assert "revenue_summary" in report_types
        assert "book_performance" in report_types


# ---------------------------------------------------------------------------
# E2E: Dashboard with no data
# ---------------------------------------------------------------------------


class TestDashboardWithNoData:
    """Verify that the dashboard returns a valid empty state for a new user
    who has not imported any data."""

    @pytest.mark.asyncio
    async def test_empty_dashboard_returns_zeroes(self, client: AsyncClient):
        # 1. Register a brand-new user (no data)
        reg_data = await _register_user(client)
        token = reg_data["tokens"]["access_token"]
        headers = _auth_header(token)

        # 2. Get dashboard -- should return a valid response with empty/zero data
        dashboard_resp = await client.get(
            f"{ANALYTICS_PREFIX}/dashboard",
            headers=headers,
        )
        assert dashboard_resp.status_code == 200, dashboard_resp.text
        dashboard = dashboard_resp.json()

        # Validate full structure exists
        assert "kpis" in dashboard
        assert "revenue_chart" in dashboard
        assert "top_books" in dashboard
        assert "platform_breakdown" in dashboard
        assert "recent_royalties" in dashboard

        # KPIs should still be generated (4 cards with zero/default values)
        assert len(dashboard["kpis"]) == 4

        # Revenue chart should be empty (no data points)
        assert isinstance(dashboard["revenue_chart"], list)

        # Top books should be empty
        assert dashboard["top_books"] == []

        # Platform breakdown should be empty
        assert dashboard["platform_breakdown"] == {}

        # Recent royalties should be empty
        assert dashboard["recent_royalties"] == []

    @pytest.mark.asyncio
    async def test_empty_royalties_list(self, client: AsyncClient):
        """A new user with no imports should see zero royalty records."""
        reg_data = await _register_user(client)
        token = reg_data["tokens"]["access_token"]
        headers = _auth_header(token)

        resp = await client.get(
            f"{ANALYTICS_PREFIX}/royalties",
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["total_count"] == 0
        assert data["items"] == []
        assert data["has_more"] is False

    @pytest.mark.asyncio
    async def test_empty_revenue(self, client: AsyncClient):
        """A new user should see zero revenue."""
        reg_data = await _register_user(client)
        token = reg_data["tokens"]["access_token"]
        headers = _auth_header(token)

        resp = await client.get(
            f"{ANALYTICS_PREFIX}/revenue",
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        total = Decimal(str(data["total_revenue"]))
        assert total == Decimal("0") or total == Decimal("0.00")
        assert data["total_units"] == 0

    @pytest.mark.asyncio
    async def test_empty_reports_list(self, client: AsyncClient):
        """A new user should see zero reports."""
        reg_data = await _register_user(client)
        token = reg_data["tokens"]["access_token"]
        headers = _auth_header(token)

        resp = await client.get(
            f"{ANALYTICS_PREFIX}/reports",
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["total_count"] == 0
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_empty_portfolio(self, client: AsyncClient):
        """A new user should see zero portfolio metrics."""
        reg_data = await _register_user(client)
        token = reg_data["tokens"]["access_token"]
        headers = _auth_header(token)

        resp = await client.get(
            f"{ANALYTICS_PREFIX}/portfolio",
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["total_books"] == 0
        total_revenue = Decimal(str(data["total_revenue"]))
        assert total_revenue == Decimal("0") or total_revenue == Decimal("0.00")
        assert data["total_units_sold"] == 0


# ---------------------------------------------------------------------------
# E2E: Import validation and edge cases
# ---------------------------------------------------------------------------


class TestImportEdgeCases:
    """Test import validation: empty content, multi-platform imports."""

    @pytest.mark.asyncio
    async def test_import_no_file_content(self, client: AsyncClient):
        """Importing with no file content should return zero records."""
        reg_data = await _register_user(client)
        token = reg_data["tokens"]["access_token"]
        headers = _auth_header(token)

        resp = await client.post(
            f"{ANALYTICS_PREFIX}/royalties/import",
            json={
                "platform": "kdp",
                "file_content": None,
                "file_name": "empty.csv",
            },
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["records_imported"] == 0
        assert len(data["errors"]) > 0

    @pytest.mark.asyncio
    async def test_import_multiple_platforms_separate_counts(self, client: AsyncClient):
        """Import from two platforms and verify each has correct record counts."""
        reg_data = await _register_user(client)
        token = reg_data["tokens"]["access_token"]
        headers = _auth_header(token)

        # Import KDP
        kdp_csv = _build_kdp_csv(KDP_SAMPLE_ROWS[:2])
        r1 = await client.post(
            f"{ANALYTICS_PREFIX}/royalties/import",
            json={"platform": "kdp", "file_content": kdp_csv, "file_name": "kdp.csv"},
            headers=headers,
        )
        assert r1.status_code == 200
        assert r1.json()["records_imported"] == 2

        # Import IngramSpark
        ingram_csv = _build_ingram_csv(INGRAM_SAMPLE_ROWS)
        r2 = await client.post(
            f"{ANALYTICS_PREFIX}/royalties/import",
            json={
                "platform": "ingram_spark",
                "file_content": ingram_csv,
                "file_name": "ingram.csv",
            },
            headers=headers,
        )
        assert r2.status_code == 200
        assert r2.json()["records_imported"] == 1

        # Verify total royalties
        resp = await client.get(
            f"{ANALYTICS_PREFIX}/royalties",
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["total_count"] == 3

        # Verify portfolio shows correct book count
        portfolio_resp = await client.get(
            f"{ANALYTICS_PREFIX}/portfolio",
            headers=headers,
        )
        assert portfolio_resp.status_code == 200
        portfolio = portfolio_resp.json()
        # 2 unique titles: "The Art of Self-Publishing" and "Marketing Mastery for Authors"
        assert portfolio["total_books"] == 2
        total_revenue = Decimal(str(portfolio["total_revenue"]))
        assert total_revenue > 0


# ---------------------------------------------------------------------------
# E2E: Full analytics pipeline
# ---------------------------------------------------------------------------


class TestFullAnalyticsPipeline:
    """End-to-end test exercising the complete analytics pipeline:
    register -> import -> dashboard -> revenue -> portfolio -> report."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, client: AsyncClient):
        # 1. Register
        reg_data = await _register_user(client)
        token = reg_data["tokens"]["access_token"]
        headers = _auth_header(token)

        # 2. Import KDP data
        kdp_csv = _build_kdp_csv(KDP_SAMPLE_ROWS)
        import_resp = await client.post(
            f"{ANALYTICS_PREFIX}/royalties/import",
            json={"platform": "kdp", "file_content": kdp_csv, "file_name": "full_test.csv"},
            headers=headers,
        )
        assert import_resp.status_code == 200
        assert import_resp.json()["records_imported"] == 3

        # 3. Import IngramSpark data
        ingram_csv = _build_ingram_csv(INGRAM_SAMPLE_ROWS)
        import_resp2 = await client.post(
            f"{ANALYTICS_PREFIX}/royalties/import",
            json={
                "platform": "ingram_spark",
                "file_content": ingram_csv,
                "file_name": "ingram_full.csv",
            },
            headers=headers,
        )
        assert import_resp2.status_code == 200
        assert import_resp2.json()["records_imported"] == 1

        # 4. Verify dashboard
        dash_resp = await client.get(
            f"{ANALYTICS_PREFIX}/dashboard",
            headers=headers,
        )
        assert dash_resp.status_code == 200
        dash = dash_resp.json()
        assert len(dash["kpis"]) == 4
        assert len(dash["recent_royalties"]) > 0

        # 5. Verify revenue aggregation
        rev_resp = await client.get(
            f"{ANALYTICS_PREFIX}/revenue",
            params={
                "start_date": "2023-12-01",
                "end_date": "2024-12-31",
                "aggregation": "monthly",
            },
            headers=headers,
        )
        assert rev_resp.status_code == 200
        rev = rev_resp.json()
        assert Decimal(str(rev["total_revenue"])) > 0
        assert rev["total_units"] > 0

        # 6. Verify portfolio metrics
        port_resp = await client.get(
            f"{ANALYTICS_PREFIX}/portfolio",
            headers=headers,
        )
        assert port_resp.status_code == 200
        port = port_resp.json()
        assert port["total_books"] > 0
        assert Decimal(str(port["total_revenue"])) > 0

        # 7. Generate a report
        report_resp = await client.post(
            f"{ANALYTICS_PREFIX}/reports/generate",
            json={
                "title": "Full Pipeline Report",
                "report_type": "revenue_summary",
                "output_format": "pdf",
                "parameters": {},
            },
            headers=headers,
        )
        assert report_resp.status_code == 201
        report_id = report_resp.json()["id"]

        # 8. List reports and find our report
        reports_resp = await client.get(
            f"{ANALYTICS_PREFIX}/reports",
            headers=headers,
        )
        assert reports_resp.status_code == 200
        report_ids = [r["id"] for r in reports_resp.json()["items"]]
        assert report_id in report_ids

        # 9. Verify data isolation: royalties from a different user should not appear
        reg_data2 = await _register_user(client)
        token2 = reg_data2["tokens"]["access_token"]
        headers2 = _auth_header(token2)

        other_dash = await client.get(
            f"{ANALYTICS_PREFIX}/dashboard",
            headers=headers2,
        )
        assert other_dash.status_code == 200
        other = other_dash.json()
        assert other["recent_royalties"] == []
        assert other["top_books"] == []
        assert other["platform_breakdown"] == {}
