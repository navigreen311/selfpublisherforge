"""Tests for the Proof Orders module (scaffold — mocked provider)."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import create_app
from app.modules.proof_orders import service
from app.modules.proof_orders.schemas import (
    Checklist,
    IssuesLevel,
    ProofOrderCreate,
    ProofReviewUpdate,
    ShippingAddress,
    ShippingMethod,
)


@pytest.fixture
def org_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def publishing_id() -> uuid.UUID:
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


def _create_payload() -> ProofOrderCreate:
    return ProofOrderCreate(
        interior_file_url="https://files/x.pdf",
        cover_file_url="https://files/y.pdf",
        trim_size="6x9",
        page_count=280,
        interior_type="standard_color",
        shipping_address=ShippingAddress(
            name="Ivan Green",
            address="123 Main St",
            city="Las Vegas",
            state="NV",
            zip="89101",
        ),
        shipping_method=ShippingMethod.STANDARD,
    )


def _full_checklist(all_checked: bool = True) -> Checklist:
    return Checklist(
        print_quality=all_checked,
        colors=all_checked,
        text=all_checked,
        pages=all_checked,
        cover=all_checked,
        spine=all_checked,
        barcode=all_checked,
        overall=all_checked,
    )


# ---------------------------------------------------------------------------
# Cost estimation
# ---------------------------------------------------------------------------

class TestCostEstimate:
    def test_standard_color_page_cost(self):
        est = service.estimate_cost(280, "standard_color", ShippingMethod.STANDARD)
        # 0.85 + 280 * 0.04 = 12.05 + 3.99
        assert est.print_cost == Decimal("12.05")
        assert est.shipping_cost == Decimal("3.99")
        assert est.total == Decimal("16.04")

    def test_black_white_cheaper_than_premium(self):
        bw = service.estimate_cost(300, "black_white", ShippingMethod.STANDARD)
        premium = service.estimate_cost(300, "premium_color", ShippingMethod.STANDARD)
        assert premium.total > bw.total

    def test_shipping_tiers_increase(self):
        s = service.estimate_cost(100, "black_white", ShippingMethod.STANDARD)
        e = service.estimate_cost(100, "black_white", ShippingMethod.EXPEDITED)
        p = service.estimate_cost(100, "black_white", ShippingMethod.PRIORITY)
        assert s.shipping_cost < e.shipping_cost < p.shipping_cost


# ---------------------------------------------------------------------------
# Order creation & approval gate
# ---------------------------------------------------------------------------

class TestOrderCreation:
    @pytest.mark.asyncio
    async def test_create_order_mocks_tracking(self, db_session, org_id, publishing_id):
        order = await service.create_order(
            db_session, org_id, publishing_id, _create_payload()
        )
        assert order.tracking_number is not None
        assert order.tracking_number.startswith("1Z")
        assert order.estimated_delivery is not None
        assert order.status == "ordered"
        assert order.cost == Decimal("16.04")
        assert order.approved is False

    @pytest.mark.asyncio
    async def test_skip_proof_marks_approved(self, db_session, org_id, publishing_id):
        order = await service.skip_proof(
            db_session, org_id, publishing_id, "Confident in files"
        )
        assert order.skipped is True
        assert order.approved is True
        assert order.status == "skipped"


class TestApprovalGate:
    @pytest.mark.asyncio
    async def test_cannot_approve_with_incomplete_checklist(
        self, db_session, org_id, publishing_id
    ):
        await service.create_order(db_session, org_id, publishing_id, _create_payload())
        review = ProofReviewUpdate(
            checklist=_full_checklist(all_checked=False),
            issues=IssuesLevel.NONE,
            approved=True,
        )
        with pytest.raises(ValueError, match="checklist"):
            await service.update_review(db_session, org_id, publishing_id, review)

    @pytest.mark.asyncio
    async def test_cannot_approve_with_major_issues(
        self, db_session, org_id, publishing_id
    ):
        await service.create_order(db_session, org_id, publishing_id, _create_payload())
        review = ProofReviewUpdate(
            checklist=_full_checklist(),
            issues=IssuesLevel.MAJOR,
            approved=True,
        )
        with pytest.raises(ValueError, match="major issues"):
            await service.update_review(db_session, org_id, publishing_id, review)

    @pytest.mark.asyncio
    async def test_approve_happy_path(self, db_session, org_id, publishing_id):
        await service.create_order(db_session, org_id, publishing_id, _create_payload())
        review = ProofReviewUpdate(
            checklist=_full_checklist(),
            issues=IssuesLevel.NONE,
            notes="Looks great",
            approved=True,
        )
        order = await service.update_review(db_session, org_id, publishing_id, review)
        assert order.approved is True
        assert order.approved_at is not None
        assert order.status == "approved"
        # can_publish gate passes
        assert await service.can_publish(db_session, org_id, publishing_id)

    @pytest.mark.asyncio
    async def test_can_publish_false_without_order(
        self, db_session, org_id, publishing_id
    ):
        assert not await service.can_publish(db_session, org_id, publishing_id)

    @pytest.mark.asyncio
    async def test_partial_checklist_saved_without_approval(
        self, db_session, org_id, publishing_id
    ):
        await service.create_order(db_session, org_id, publishing_id, _create_payload())
        partial = Checklist(print_quality=True, colors=True)
        review = ProofReviewUpdate(
            checklist=partial,
            issues=IssuesLevel.MINOR,
            approved=False,
        )
        order = await service.update_review(db_session, org_id, publishing_id, review)
        assert order.approved is False
        assert order.checklist["print_quality"] is True
        assert order.checklist["overall"] is False


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

class TestProofRouter:
    @pytest.mark.asyncio
    async def test_estimate_endpoint(self, client):
        r = await client.post(
            "/api/v1/publishing/estimate-proof-cost",
            params={"page_count": 280, "interior_type": "standard_color"},
        )
        assert r.status_code == 200
        assert r.json()["total"] == "16.04"

    @pytest.mark.asyncio
    async def test_full_proof_flow(self, client, publishing_id):
        # order
        r = await client.post(
            f"/api/v1/publishing/{publishing_id}/order-proof",
            json={
                "interior_file_url": "https://x/i.pdf",
                "cover_file_url": "https://x/c.pdf",
                "page_count": 280,
                "interior_type": "standard_color",
                "shipping_address": {
                    "name": "Ivan",
                    "address": "123 Main",
                    "city": "LV",
                    "state": "NV",
                    "zip": "89101",
                },
                "shipping_method": "standard",
            },
        )
        assert r.status_code == 201, r.text
        assert r.json()["tracking_number"]

        # status
        r = await client.get(f"/api/v1/publishing/{publishing_id}/proof-status")
        assert r.status_code == 200

        # review — incomplete checklist cannot approve
        r = await client.patch(
            f"/api/v1/publishing/{publishing_id}/proof-review",
            json={
                "checklist": {k: False for k in (
                    "print_quality", "colors", "text", "pages",
                    "cover", "spine", "barcode", "overall",
                )},
                "issues": "none",
                "approved": True,
            },
        )
        assert r.status_code == 400

        # approve correctly
        r = await client.patch(
            f"/api/v1/publishing/{publishing_id}/proof-review",
            json={
                "checklist": {k: True for k in (
                    "print_quality", "colors", "text", "pages",
                    "cover", "spine", "barcode", "overall",
                )},
                "issues": "none",
                "approved": True,
            },
        )
        assert r.status_code == 200
        assert r.json()["approved"] is True

    @pytest.mark.asyncio
    async def test_skip_endpoint(self, client, publishing_id):
        r = await client.post(
            f"/api/v1/publishing/{publishing_id}/skip-proof",
            json={"reason": "confident"},
        )
        assert r.status_code == 201
        assert r.json()["skipped"] is True
        assert r.json()["approved"] is True

    @pytest.mark.asyncio
    async def test_status_404_if_none(self, client, publishing_id):
        r = await client.get(f"/api/v1/publishing/{publishing_id}/proof-status")
        assert r.status_code == 404
