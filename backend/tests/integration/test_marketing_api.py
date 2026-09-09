"""Integration tests for the Marketing & Launch Command API endpoints.

Uses an in-memory SQLite database and the FastAPI test client.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.dependencies import get_current_user
from app.database import Base, get_db
from app.main import create_app

_TEST_USER = {"user_id": uuid.uuid4(), "org_id": uuid.uuid4(), "role": "admin"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="module")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(engine: AsyncEngine) -> AsyncGenerator[AsyncClient, None]:
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: _TEST_USER

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def book_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def launch_date() -> str:
    return (datetime.now(UTC) + timedelta(days=30)).isoformat()


# ---------------------------------------------------------------------------
# Launch Plan API Tests
# ---------------------------------------------------------------------------


class TestLaunchPlanAPI:
    """Integration tests for launch plan endpoints."""

    @pytest.mark.asyncio
    async def test_generate_launch_plan(self, client: AsyncClient, book_id: str, launch_date: str):
        response = await client.post(
            "/api/v1/marketing/launch-plan/generate",
            json={
                "book_id": book_id,
                "book_title": "Test Book",
                "genre": "Fantasy",
                "target_audience": "Young adults",
                "launch_date": launch_date,
                "budget": 500.0,
                "goals": ["1000 sales"],
            },
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["title"] == "Launch Plan: Test Book"
        assert data["genre"] == "Fantasy"
        assert len(data["phases"]) == 3

    @pytest.mark.asyncio
    async def test_list_launch_plans(self, client: AsyncClient, book_id: str, launch_date: str):
        # Create a plan first
        await client.post(
            "/api/v1/marketing/launch-plan/generate",
            json={
                "book_id": book_id,
                "book_title": "List Test Book",
                "genre": "Sci-Fi",
                "target_audience": "Adults",
                "launch_date": launch_date,
            },
        )

        response = await client.get("/api/v1/marketing/launch-plans")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total_count"] >= 1

    @pytest.mark.asyncio
    async def test_get_launch_plan_detail(self, client: AsyncClient, book_id: str, launch_date: str):
        # Create
        create_resp = await client.post(
            "/api/v1/marketing/launch-plan/generate",
            json={
                "book_id": book_id,
                "book_title": "Detail Test",
                "genre": "Mystery",
                "target_audience": "Mystery lovers",
                "launch_date": launch_date,
            },
        )
        plan_id = create_resp.json()["data"]["id"]

        # Fetch detail
        response = await client.get(f"/api/v1/marketing/launch-plans/{plan_id}")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == plan_id
        assert len(data["phases"]) == 3

    @pytest.mark.asyncio
    async def test_update_launch_plan(self, client: AsyncClient, book_id: str, launch_date: str):
        # Create
        create_resp = await client.post(
            "/api/v1/marketing/launch-plan/generate",
            json={
                "book_id": book_id,
                "book_title": "Update Test",
                "genre": "Romance",
                "target_audience": "Romance readers",
                "launch_date": launch_date,
            },
        )
        plan_id = create_resp.json()["data"]["id"]

        # Update
        response = await client.patch(
            f"/api/v1/marketing/launch-plans/{plan_id}",
            json={"title": "Updated Title", "status": "active"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["title"] == "Updated Title"
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_get_nonexistent_plan_returns_404(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/marketing/launch-plans/{fake_id}")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Email Sequence API Tests
# ---------------------------------------------------------------------------


class TestEmailSequenceAPI:
    """Integration tests for email sequence endpoints."""

    @pytest.mark.asyncio
    async def test_create_email_sequence(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/marketing/email-sequences",
            json={
                "name": "Launch Sequence",
                "description": "Test email sequence",
                "trigger_event": "book.launch",
                "emails": [
                    {
                        "template_type": "welcome",
                        "subject": "Welcome!",
                        "body_html": "<p>Hello</p>",
                        "body_text": "Hello",
                        "delay_days": 0,
                        "order_index": 0,
                    },
                    {
                        "template_type": "launch_announcement",
                        "subject": "The book is here!",
                        "body_html": "<p>Buy now!</p>",
                        "body_text": "Buy now!",
                        "delay_days": 7,
                        "order_index": 1,
                    },
                ],
            },
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["name"] == "Launch Sequence"
        assert len(data["emails"]) == 2

    @pytest.mark.asyncio
    async def test_list_email_sequences(self, client: AsyncClient):
        # Create
        await client.post(
            "/api/v1/marketing/email-sequences",
            json={
                "name": "Seq for List",
                "emails": [
                    {
                        "template_type": "custom",
                        "subject": "Test",
                        "delay_days": 0,
                        "order_index": 0,
                    }
                ],
            },
        )

        response = await client.get("/api/v1/marketing/email-sequences")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] >= 1

    @pytest.mark.asyncio
    async def test_update_email_sequence(self, client: AsyncClient):
        # Create
        create_resp = await client.post(
            "/api/v1/marketing/email-sequences",
            json={
                "name": "To Update",
                "emails": [],
            },
        )
        seq_id = create_resp.json()["data"]["id"]

        # Update
        response = await client.patch(
            f"/api/v1/marketing/email-sequences/{seq_id}",
            json={"name": "Updated Sequence", "status": "active"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Updated Sequence"

    @pytest.mark.asyncio
    async def test_trigger_email_send(self, client: AsyncClient):
        # Create
        create_resp = await client.post(
            "/api/v1/marketing/email-sequences",
            json={
                "name": "Sendable",
                "emails": [
                    {
                        "template_type": "welcome",
                        "subject": "Hello",
                        "delay_days": 0,
                        "order_index": 0,
                    }
                ],
            },
        )
        seq_id = create_resp.json()["data"]["id"]

        # Trigger send
        response = await client.post(
            f"/api/v1/marketing/email-sequences/{seq_id}/send",
            json={
                "recipient_emails": ["test@example.com", "reader@example.com"],
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status"] == "active"
        assert data["recipient_count"] == 2


# ---------------------------------------------------------------------------
# Social Media API Tests
# ---------------------------------------------------------------------------


class TestSocialMediaAPI:
    """Integration tests for social media endpoints."""

    @pytest.mark.asyncio
    async def test_generate_social_content(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/marketing/social/generate",
            json={
                "book_title": "Social Book",
                "genre": "Thriller",
                "target_audience": "Thriller fans",
                "book_description": "A heart-pounding thriller that never lets up.",
                "platforms": ["twitter", "facebook"],
                "num_posts_per_platform": 2,
            },
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert len(data) >= 2  # At least 2 posts (1 per platform minimum)

    @pytest.mark.asyncio
    async def test_get_social_calendar(self, client: AsyncClient):
        response = await client.get("/api/v1/marketing/social/calendar")
        assert response.status_code == 200
        data = response.json()
        assert "posts" in data
        assert "total_scheduled" in data
        assert "total_published" in data
        assert "platforms" in data

    @pytest.mark.asyncio
    async def test_generate_social_with_invalid_platform(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/marketing/social/calendar",
            params={"platform": "tiktok"},
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# ARC Campaign API Tests
# ---------------------------------------------------------------------------


class TestARCCampaignAPI:
    """Integration tests for ARC campaign endpoints."""

    @pytest.fixture
    def arc_payload(self) -> dict[str, Any]:
        return {
            "book_id": str(uuid.uuid4()),
            "name": "ARC Campaign 1",
            "description": "Test ARC campaign",
            "cover_letter": "Dear reviewer, please enjoy this ARC.",
            "deadline": (datetime.now(UTC) + timedelta(days=14)).isoformat(),
            "recipients": [
                {"name": "Reviewer A", "email": "a@example.com"},
                {"name": "Reviewer B", "email": "b@example.com"},
                {"name": "Reviewer C", "email": "c@example.com"},
            ],
        }

    @pytest.mark.asyncio
    async def test_create_arc_campaign(self, client: AsyncClient, arc_payload: dict):
        response = await client.post(
            "/api/v1/marketing/arc",
            json=arc_payload,
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["name"] == "ARC Campaign 1"
        assert data["total_copies"] == 3
        assert len(data["recipients"]) == 3

    @pytest.mark.asyncio
    async def test_list_arc_campaigns(self, client: AsyncClient, arc_payload: dict):
        await client.post("/api/v1/marketing/arc", json=arc_payload)

        response = await client.get("/api/v1/marketing/arc")
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] >= 1

    @pytest.mark.asyncio
    async def test_send_arc_copies(self, client: AsyncClient, arc_payload: dict):
        # Create
        create_resp = await client.post(
            "/api/v1/marketing/arc",
            json=arc_payload,
        )
        campaign_id = create_resp.json()["data"]["id"]

        # Send to all
        response = await client.post(
            f"/api/v1/marketing/arc/{campaign_id}/send",
            json={},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["sent_copies"] == 3
        # All copies sent, should be completed
        assert data["status"] in ("active", "completed")

    @pytest.mark.asyncio
    async def test_send_arc_to_specific_recipients(self, client: AsyncClient, arc_payload: dict):
        # Create
        create_resp = await client.post(
            "/api/v1/marketing/arc",
            json=arc_payload,
        )
        campaign = create_resp.json()["data"]
        campaign_id = campaign["id"]
        first_recipient_id = campaign["recipients"][0]["id"]

        # Send to only one
        response = await client.post(
            f"/api/v1/marketing/arc/{campaign_id}/send",
            json={"recipient_ids": [first_recipient_id]},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["sent_copies"] == 1
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_send_arc_nonexistent_returns_404(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        response = await client.post(
            f"/api/v1/marketing/arc/{fake_id}/send",
            json={},
        )
        assert response.status_code == 404
