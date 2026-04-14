"""Tests for the Royalties module."""

from __future__ import annotations

import uuid
from decimal import Decimal
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import create_app
from app.modules.royalties import importer, service
from app.modules.royalties.schemas import RoyaltyEntryCreate


FIXTURES = Path(__file__).parent / "fixtures" / "royalty_imports"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def org_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_user(org_id):
    return {"user_id": uuid.uuid4(), "org_id": org_id, "role": "owner"}


@pytest_asyncio.fixture
async def client(mock_user, db_session):
    app = create_app()

    async def _override_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Importer (pure unit tests, no DB)
# ---------------------------------------------------------------------------

class TestKDPParser:
    def test_parses_known_headers(self):
        result = importer.parse_kdp((FIXTURES / "kdp_sample.csv").read_bytes())
        assert len(result.rows) == 10
        total = sum((r.amount for r in result.rows), Decimal("0"))
        assert total > Decimal("6000")
        # KENP rows detected
        kenp = [r for r in result.rows if r.royalty_type == "ku_kenp"]
        assert len(kenp) == 3
        assert all(r.kenp_pages and r.kenp_pages > 0 for r in kenp)

    def test_kdp_header_flexibility(self):
        csv_data = (
            "Earnings,Type,Date,Units\n"
            "$125.50,Kindle eBook,2026-01,15\n"
            "$45.00,Paperback,2026-01,3\n"
        )
        result = importer.parse_kdp(csv_data)
        assert len(result.rows) == 2
        assert result.rows[0].amount == Decimal("125.50")
        assert result.rows[0].royalty_type == "kindle_ebook"
        assert result.rows[1].royalty_type == "paperback"

    def test_kdp_normalizes_types(self):
        csv_data = (
            "Royalty,Transaction Type,Date\n"
            "$10.00,Kindle Unlimited - KENP,2026-03\n"
            "$20.00,Pages Read,2026-03\n"
            "$30.00,Hardcover,2026-03\n"
        )
        result = importer.parse_kdp(csv_data)
        types = [r.royalty_type for r in result.rows]
        assert "ku_kenp" in types
        assert types.count("ku_kenp") == 2
        assert "hardcover" in types

    def test_kdp_skips_zero_amount(self):
        csv_data = (
            "Royalty,Transaction Type,Date\n"
            "$0.00,Kindle eBook,2026-01\n"
            "$10.00,Kindle eBook,2026-01\n"
        )
        result = importer.parse_kdp(csv_data)
        assert len(result.rows) == 1
        assert result.skipped == 1


class TestIngramParser:
    def test_parses_ingram_fixture(self):
        result = importer.parse_ingram((FIXTURES / "ingram_sample.csv").read_bytes())
        assert len(result.rows) == 3  # zero row skipped
        total = sum((r.amount for r in result.rows), Decimal("0"))
        assert total == Decimal("736.00")
        assert all(r.distributor == "ingram" for r in result.rows)

    def test_ingram_alt_headers(self):
        csv_data = (
            "Month,ISBN,Compensation,Net Qty\n"
            "2026-02,9780000000000,$125.00,20\n"
        )
        result = importer.parse_ingram(csv_data)
        assert len(result.rows) == 1
        assert result.rows[0].amount == Decimal("125.00")
        assert result.rows[0].period_month == 2


class TestD2DParser:
    def test_parses_d2d_fixture(self):
        result = importer.parse_d2d((FIXTURES / "d2d_sample.csv").read_bytes())
        assert len(result.rows) == 5
        total = sum((r.amount for r in result.rows), Decimal("0"))
        assert total == Decimal("179.22")
        # Retailer captured in notes
        assert all(r.notes for r in result.rows)


class TestParenthesisAndNegatives:
    def test_parens_negative(self):
        csv_data = "Earnings,Type,Date\n($5.00),Kindle eBook,2026-01\n"
        result = importer.parse_kdp(csv_data)
        assert len(result.rows) == 1
        assert result.rows[0].amount == Decimal("-5.00")


# ---------------------------------------------------------------------------
# Service & aggregation (DB-backed)
# ---------------------------------------------------------------------------

class TestImportAndAggregate:
    @pytest.mark.asyncio
    async def test_import_kdp_writes_rows(self, db_session, org_id):
        content = (FIXTURES / "kdp_sample.csv").read_bytes()
        result = await service.import_csv(db_session, org_id, "kdp", content)
        assert result.imported == 10
        assert result.total_amount > Decimal("6000")

    @pytest.mark.asyncio
    async def test_dashboard_aggregates_by_distributor(self, db_session, org_id):
        await service.import_csv(
            db_session, org_id, "kdp", (FIXTURES / "kdp_sample.csv").read_bytes()
        )
        await service.import_csv(
            db_session, org_id, "ingram", (FIXTURES / "ingram_sample.csv").read_bytes()
        )
        await service.import_csv(
            db_session, org_id, "d2d", (FIXTURES / "d2d_sample.csv").read_bytes()
        )
        dashboard = await service.get_dashboard(db_session, org_id, year=2026)
        dist_totals = {d.distributor: d.total for d in dashboard.by_distributor}
        assert dist_totals["kdp"] > dist_totals["ingram"] > dist_totals["d2d"]
        assert dashboard.ytd_earnings == sum(dist_totals.values(), Decimal("0"))

    @pytest.mark.asyncio
    async def test_monthly_statement_groups_columns(self, db_session, org_id):
        await service.import_csv(
            db_session, org_id, "kdp", (FIXTURES / "kdp_sample.csv").read_bytes()
        )
        await service.import_csv(
            db_session, org_id, "ingram", (FIXTURES / "ingram_sample.csv").read_bytes()
        )
        stmt = await service.get_monthly_statement(db_session, org_id, 2026)
        assert len(stmt.rows) == 12
        jan = next(r for r in stmt.rows if r.month == 1)
        assert jan.kdp_ebook > 0
        assert jan.kdp_print > 0
        assert jan.ku_kenp > 0
        assert jan.ingram > 0
        # YTD totals sum to rows' totals
        row_sum = sum((r.total for r in stmt.rows), Decimal("0"))
        assert stmt.ytd_totals.total == row_sum


class TestManualEntry:
    @pytest.mark.asyncio
    async def test_manual_entry_persists(self, db_session, org_id):
        payload = RoyaltyEntryCreate(
            distributor="kdp",
            royalty_type="kindle_ebook",
            amount=Decimal("99.99"),
            period_month=3,
            period_year=2026,
        )
        entry = await service.create_manual_entry(db_session, org_id, payload)
        assert entry.id is not None
        assert entry.source == "manual"


class TestExport:
    @pytest.mark.asyncio
    async def test_export_csv_shape(self, db_session, org_id):
        await service.import_csv(
            db_session, org_id, "kdp", (FIXTURES / "kdp_sample.csv").read_bytes()
        )
        stmt = await service.get_monthly_statement(db_session, org_id, 2026)
        csv_str = service.export_csv(stmt)
        assert "Month,KDP eBook" in csv_str
        assert "YTD Total" in csv_str

    @pytest.mark.asyncio
    async def test_export_pdf_header(self, db_session, org_id):
        stmt = await service.get_monthly_statement(db_session, org_id, 2026)
        pdf = service.export_pdf(stmt)
        assert pdf.startswith(b"%PDF-1.4")
        assert b"%%EOF" in pdf


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

class TestRouter:
    @pytest.mark.asyncio
    async def test_by_distributor_endpoint(self, client):
        r = await client.get("/api/v1/royalties/by-distributor?year=2026")
        assert r.status_code == 200
        data = r.json()
        assert "by_distributor" in data
        assert "ytd_earnings" in data

    @pytest.mark.asyncio
    async def test_monthly_statement_endpoint(self, client):
        r = await client.get("/api/v1/royalties/monthly-statement?year=2026")
        assert r.status_code == 200
        data = r.json()
        assert data["year"] == 2026
        assert len(data["rows"]) == 12

    @pytest.mark.asyncio
    async def test_import_endpoint(self, client):
        content = (FIXTURES / "kdp_sample.csv").read_bytes()
        r = await client.post(
            "/api/v1/royalties/import",
            files={"file": ("kdp.csv", content, "text/csv")},
            data={"distributor": "kdp"},
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["imported"] == 10
        assert data["distributor"] == "kdp"

    @pytest.mark.asyncio
    async def test_manual_entry_endpoint(self, client):
        payload = {
            "distributor": "kdp",
            "royalty_type": "kindle_ebook",
            "amount": "125.50",
            "period_month": 3,
            "period_year": 2026,
        }
        r = await client.post("/api/v1/royalties/manual-entry", json=payload)
        assert r.status_code == 201, r.text
        assert r.json()["source"] == "manual"

    @pytest.mark.asyncio
    async def test_export_csv_endpoint(self, client):
        r = await client.get("/api/v1/royalties/export?format=csv&year=2026")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/csv")

    @pytest.mark.asyncio
    async def test_unsupported_distributor_rejected(self, client):
        r = await client.post(
            "/api/v1/royalties/import",
            files={"file": ("x.csv", b"a,b\n1,2\n", "text/csv")},
            data={"distributor": "bogus"},
        )
        assert r.status_code == 400
