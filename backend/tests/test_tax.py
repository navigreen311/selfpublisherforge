"""Tests for the Tax module."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import create_app
from app.modules.royalties import service as royalty_service
from app.modules.royalties.schemas import RoyaltyEntryCreate
from app.modules.tax import service as tax_service
from app.modules.tax.schemas import (
    FilingStatus,
    QuarterlyPaymentUpdate,
    TaxExpenseCreate,
    TaxExpenseUpdate,
    TAX_DISCLAIMER,
)


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


async def _seed_income(db, org_id):
    """Seed $14,280 gross across 3 distributors, Jan-Mar 2026."""
    entries = [
        ("kdp", "kindle_ebook", Decimal("6200"), 3, 2026),
        ("kdp", "paperback", Decimal("2100"), 3, 2026),
        ("kdp", "ku_kenp", Decimal("3800"), 3, 2026),
        ("kdp", "hardcover", Decimal("300"), 3, 2026),
        ("ingram", "print", Decimal("1580"), 3, 2026),
        ("d2d", "ebook", Decimal("300"), 3, 2026),
    ]
    for dist, rtype, amt, m, y in entries:
        await royalty_service.create_manual_entry(
            db,
            org_id,
            RoyaltyEntryCreate(
                distributor=dist,
                royalty_type=rtype,
                amount=amt,
                period_month=m,
                period_year=y,
            ),
        )


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------

class TestExpenseCRUD:
    @pytest.mark.asyncio
    async def test_create_list_update_delete(self, db_session, org_id):
        payload = TaxExpenseCreate(
            category="AI Services",
            amount=Decimal("480"),
            description="OpenAI + Anthropic",
            expense_date=date(2026, 1, 15),
            tax_year=2026,
        )
        created = await tax_service.create_expense(db_session, org_id, payload)
        assert created.id is not None

        rows = await tax_service.list_expenses(db_session, org_id, 2026)
        assert len(rows) == 1

        updated = await tax_service.update_expense(
            db_session, org_id, created.id, TaxExpenseUpdate(amount=Decimal("495"))
        )
        assert updated.amount == Decimal("495")

        ok = await tax_service.delete_expense(db_session, org_id, created.id)
        assert ok
        assert not await tax_service.list_expenses(db_session, org_id, 2026)

    @pytest.mark.asyncio
    async def test_update_missing_returns_none(self, db_session, org_id):
        res = await tax_service.update_expense(
            db_session, org_id, uuid.uuid4(), TaxExpenseUpdate(amount=Decimal("1"))
        )
        assert res is None

    @pytest.mark.asyncio
    async def test_cross_org_isolation(self, db_session, org_id):
        other = uuid.uuid4()
        payload = TaxExpenseCreate(
            category="Other", amount=Decimal("10"), tax_year=2026
        )
        row = await tax_service.create_expense(db_session, other, payload)
        # Our org should not see it.
        rows = await tax_service.list_expenses(db_session, org_id, 2026)
        assert len(rows) == 0
        # Cross-org delete fails.
        assert not await tax_service.delete_expense(db_session, org_id, row.id)


class TestDashboardCalc:
    @pytest.mark.asyncio
    async def test_gross_and_net_calc(self, db_session, org_id):
        await _seed_income(db_session, org_id)
        await tax_service.create_expense(
            db_session,
            org_id,
            TaxExpenseCreate(
                category="AI Services",
                amount=Decimal("480"),
                expense_date=date(2026, 2, 1),
                tax_year=2026,
            ),
        )
        dashboard = await tax_service.get_dashboard(db_session, org_id, 2026)
        assert dashboard.gross_income == Decimal("14280.00")
        assert dashboard.estimated_expenses == Decimal("480.00")
        assert dashboard.net_income == Decimal("13800.00")
        # 25% default rate
        assert dashboard.estimated_tax_owed == Decimal("3450.00")
        # Disclaimer present
        assert dashboard.disclaimer == TAX_DISCLAIMER

    @pytest.mark.asyncio
    async def test_1099_threshold(self, db_session, org_id):
        await _seed_income(db_session, org_id)
        dashboard = await tax_service.get_dashboard(db_session, org_id, 2026)
        by_source = {r.source: r for r in dashboard.income_by_source}
        assert by_source["Amazon KDP"].expects_1099 is True
        assert by_source["IngramSpark"].expects_1099 is True
        assert by_source["Draft2Digital"].expects_1099 is False  # $300 < $600

    @pytest.mark.asyncio
    async def test_quarterly_estimates_created_on_demand(self, db_session, org_id):
        await _seed_income(db_session, org_id)
        dashboard = await tax_service.get_dashboard(db_session, org_id, 2026)
        assert len(dashboard.quarterly_estimates) == 4
        assert dashboard.quarterly_estimates[0].due_date == date(2026, 4, 15)
        assert dashboard.quarterly_estimates[3].due_date == date(2027, 1, 15)
        # Q1 has income ($14,280 all in March) — non-zero estimate.
        q1 = dashboard.quarterly_estimates[0]
        assert q1.estimated_amount == Decimal("3570.00")

    @pytest.mark.asyncio
    async def test_custom_tax_rate(self, db_session, org_id):
        await _seed_income(db_session, org_id)
        dashboard = await tax_service.get_dashboard(
            db_session, org_id, 2026, tax_rate=Decimal("0.30")
        )
        # 14280 * 0.30
        assert dashboard.estimated_tax_owed == Decimal("4284.00")

    @pytest.mark.asyncio
    async def test_mark_quarterly_paid(self, db_session, org_id):
        await _seed_income(db_session, org_id)
        await tax_service.get_dashboard(db_session, org_id, 2026)  # seed rows
        updated = await tax_service.update_quarterly_payment(
            db_session,
            org_id,
            2026,
            1,
            QuarterlyPaymentUpdate(paid=True, actual_amount=Decimal("3500")),
        )
        assert updated.paid is True
        assert updated.paid_date is not None
        assert updated.actual_amount == Decimal("3500")


# ---------------------------------------------------------------------------
# Router tests
# ---------------------------------------------------------------------------

class TestTaxRouter:
    @pytest.mark.asyncio
    async def test_dashboard_endpoint(self, client):
        r = await client.get("/api/v1/tax?year=2026")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["tax_year"] == 2026
        assert data["disclaimer"]
        assert "quarterly_estimates" in data

    @pytest.mark.asyncio
    async def test_expense_crud_endpoints(self, client):
        r = await client.post(
            "/api/v1/tax/expenses",
            json={
                "category": "Software",
                "amount": "240.00",
                "tax_year": 2026,
                "expense_date": "2026-01-15",
            },
        )
        assert r.status_code == 201, r.text
        expense_id = r.json()["id"]

        r = await client.get("/api/v1/tax/expenses?year=2026")
        assert r.status_code == 200
        assert len(r.json()) == 1

        r = await client.patch(
            f"/api/v1/tax/expenses/{expense_id}", json={"amount": "250.00"}
        )
        assert r.status_code == 200
        assert r.json()["amount"] == "250.00"

        r = await client.delete(f"/api/v1/tax/expenses/{expense_id}")
        assert r.status_code == 204

    @pytest.mark.asyncio
    async def test_mark_quarterly_paid_endpoint(self, client):
        r = await client.patch(
            "/api/v1/tax/quarterly-payment/2?year=2026",
            json={"paid": True, "actual_amount": "1000.00"},
        )
        assert r.status_code == 200
        assert r.json()["paid"] is True

    @pytest.mark.asyncio
    async def test_export_csv_includes_disclaimer(self, client):
        r = await client.get("/api/v1/tax/export?format=csv&year=2026")
        assert r.status_code == 200
        assert b"Disclaimer" in r.content

    @pytest.mark.asyncio
    async def test_invalid_quarter_rejected(self, client):
        r = await client.patch(
            "/api/v1/tax/quarterly-payment/5?year=2026",
            json={"paid": True},
        )
        assert r.status_code == 400
