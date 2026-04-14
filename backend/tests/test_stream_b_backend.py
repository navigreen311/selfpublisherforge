"""Tests for Stream B backend APIs: dashboard, projects extensions, search.

Uses mocked auth + DB dependencies like the other endpoint tests.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import create_app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def org_id():
    return uuid.uuid4()


@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
def mock_user(org_id, user_id):
    return {"user_id": user_id, "org_id": org_id, "role": "owner"}


@pytest_asyncio.fixture
async def client(mock_user):
    app = create_app()

    from app.core.dependencies import get_current_user
    from app.database import get_db

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()
    mock_db.close = AsyncMock()
    mock_db.refresh = AsyncMock()

    async def _override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


class TestDashboard:
    @pytest.mark.asyncio
    async def test_get_dashboard_happy_path(self, client, org_id):
        from app.modules.dashboard.schemas import (
            DashboardResponse,
            DashboardStats,
        )

        payload = DashboardResponse(
            stats=DashboardStats(
                total_projects=2,
                in_progress=1,
                published=1,
                monthly_revenue=Decimal("123.45"),
            ),
            revenue_trend=[],
            active_pipelines=[],
            recent_activity=[],
            ai_insights=[],
            upcoming_deadlines=[],
        )

        with patch("app.modules.dashboard.router.service") as mock_service:
            mock_service.get_dashboard = AsyncMock(return_value=payload)
            resp = await client.get("/api/v1/dashboard")
            assert resp.status_code == 200
            body = resp.json()
            assert body["stats"]["total_projects"] == 2
            assert body["stats"]["published"] == 1
            assert "revenue_trend" in body
            assert "ai_insights" in body
            assert "recent_activity" in body
            assert "upcoming_deadlines" in body


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


class TestProjectsEndpoints:
    @pytest.mark.asyncio
    async def test_list_projects(self, client, org_id):
        from app.modules.projects.schemas import ProjectListResponse

        with patch("app.modules.projects.router.service") as mock_service:
            mock_service.list_projects = AsyncMock(
                return_value=ProjectListResponse(projects=[], total=0)
            )
            resp = await client.get(
                "/api/v1/projects/",
                params={"book_type": "cookbook", "sort": "-created_at"},
            )
            assert resp.status_code == 200
            assert resp.json() == {"projects": [], "total": 0}
            mock_service.list_projects.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_project(self, client, org_id):
        from datetime import datetime, timezone

        from app.modules.projects.schemas import ProjectResponse

        now = datetime.now(timezone.utc)
        pid = uuid.uuid4()
        response_obj = ProjectResponse(
            id=pid,
            title="Keto Cookbook",
            description=None,
            project_type="book",
            book_type="cookbook",
            target_launch_date=None,
            status="draft",
            organization_id=org_id,
            linked_modules=[],
            created_at=now,
            updated_at=now,
        )
        with patch("app.modules.projects.router.service") as mock_service:
            mock_service.create_project = AsyncMock(return_value=response_obj)
            resp = await client.post(
                "/api/v1/projects/",
                json={
                    "title": "Keto Cookbook",
                    "book_type": "cookbook",
                },
            )
            assert resp.status_code == 201
            body = resp.json()
            assert body["title"] == "Keto Cookbook"
            assert body["book_type"] == "cookbook"

    @pytest.mark.asyncio
    async def test_get_project_detail(self, client, org_id):
        from datetime import datetime, timezone

        from app.modules.projects.schemas import (
            ProjectModuleProgress,
            ProjectResponse,
        )

        now = datetime.now(timezone.utc)
        pid = uuid.uuid4()
        response_obj = ProjectResponse(
            id=pid,
            title="Alpha",
            description="desc",
            project_type="book",
            book_type=None,
            status="draft",
            organization_id=org_id,
            linked_modules=[
                ProjectModuleProgress(module_type="books", status="linked", count=1)
            ],
            created_at=now,
            updated_at=now,
        )
        with patch("app.modules.projects.router.service") as mock_service:
            mock_service.get_project = AsyncMock(return_value=response_obj)
            resp = await client.get(f"/api/v1/projects/{pid}")
            assert resp.status_code == 200
            body = resp.json()
            assert body["id"] == str(pid)
            assert body["linked_modules"][0]["module_type"] == "books"

    @pytest.mark.asyncio
    async def test_patch_project(self, client, org_id):
        from datetime import datetime, timezone

        from app.modules.projects.schemas import ProjectResponse

        now = datetime.now(timezone.utc)
        pid = uuid.uuid4()
        response_obj = ProjectResponse(
            id=pid,
            title="Renamed",
            description=None,
            project_type="book",
            book_type="fiction",
            status="active",
            organization_id=org_id,
            linked_modules=[],
            created_at=now,
            updated_at=now,
        )
        with patch("app.modules.projects.router.service") as mock_service:
            mock_service.update_project = AsyncMock(return_value=response_obj)
            resp = await client.patch(
                f"/api/v1/projects/{pid}",
                json={"title": "Renamed", "book_type": "fiction", "status": "active"},
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["title"] == "Renamed"
            assert body["book_type"] == "fiction"
            assert body["status"] == "active"


# ---------------------------------------------------------------------------
# Global search
# ---------------------------------------------------------------------------


class TestSearch:
    @pytest.mark.asyncio
    async def test_search_happy_path(self, client, org_id):
        from app.modules.search.schemas import SearchResponse, SearchResultItem

        payload = SearchResponse(
            query="keto",
            results_by_type={
                "projects": [
                    SearchResultItem(
                        id=uuid.uuid4(),
                        title="Keto Cookbook",
                        snippet="A book",
                        resource_type="project",
                    )
                ],
            },
            total_count=1,
        )
        with patch("app.modules.search.router.service") as mock_service:
            mock_service.search = AsyncMock(return_value=payload)
            resp = await client.get(
                "/api/v1/search", params={"q": "keto", "types": "projects"}
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["total_count"] == 1
            assert "projects" in body["results_by_type"]
            mock_service.search.assert_awaited_once()


# ---------------------------------------------------------------------------
# Notifications (already-existing endpoints -- sanity-check contract)
# ---------------------------------------------------------------------------


class TestNotificationsContract:
    @pytest.mark.asyncio
    async def test_list_notifications_registered(self, client):
        with patch("app.modules.notifications.router.service") as mock_service:
            mock_service.list_notifications = AsyncMock(return_value=([], None, False))
            resp = await client.get("/api/v1/notifications")
            assert resp.status_code == 200
            body = resp.json()
            assert body["items"] == []
            assert body["has_more"] is False

    @pytest.mark.asyncio
    async def test_mark_all_read_registered(self, client):
        with patch("app.modules.notifications.router.service") as mock_service:
            mock_service.mark_all_as_read = AsyncMock(return_value=3)
            resp = await client.post("/api/v1/notifications/read-all")
            assert resp.status_code == 200
            assert "3" in resp.json()["message"]


# ---------------------------------------------------------------------------
# Activity log helper
# ---------------------------------------------------------------------------


class TestActivityLog:
    @pytest.mark.asyncio
    async def test_log_activity_adds_entry(self, org_id, user_id):
        from app.modules.activity.service import log_activity

        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        entry = await log_activity(
            mock_db,
            org_id=org_id,
            user_id=user_id,
            action="project.created",
            description="Created project",
            resource_type="project",
            resource_id=uuid.uuid4(),
            metadata={"foo": "bar"},
        )
        assert entry.org_id == org_id
        assert entry.action == "project.created"
        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()
