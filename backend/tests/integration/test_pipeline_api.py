"""Integration tests for the Production Pipeline API endpoints.

Uses an in-memory SQLite database via httpx + FastAPI TestClient.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.dependencies import get_current_user
from app.database import Base, get_db
from app.main import create_app

# ── Test database setup ───────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

ORG_ID = "00000000-0000-0000-0000-000000000001"
BOOK_ID = "00000000-0000-0000-0000-000000000099"
_TEST_USER = {"user_id": str(uuid.uuid4()), "org_id": uuid.UUID(ORG_ID), "role": "admin"}


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture
async def fastapi_app():
    """Create a fresh app with a clean in-memory database."""
    # Import models so they are registered on Base.metadata
    import app.modules.production_pipeline.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    application = create_app()
    application.dependency_overrides[get_db] = override_get_db
    application.dependency_overrides[get_current_user] = lambda: _TEST_USER
    yield application

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(fastapi_app):
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Helper ────────────────────────────────────────────────────────────────


def _pipeline_url(path: str = "") -> str:
    return f"/api/v1/pipelines{path}"


# ── Tests: Create Pipeline ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_pipeline(client: AsyncClient):
    resp = await client.post(
        _pipeline_url(),
        params={"org_id": ORG_ID},
        json={
            "name": "Test Pipeline",
            "book_id": BOOK_ID,
            "description": "Integration test pipeline",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Pipeline"
    assert data["status"] == "draft"
    assert data["book_id"] == BOOK_ID
    assert "id" in data


@pytest.mark.asyncio
async def test_create_pipeline_with_deadline(client: AsyncClient):
    deadline = (datetime.now(UTC) + timedelta(days=30)).isoformat()
    resp = await client.post(
        _pipeline_url(),
        params={"org_id": ORG_ID},
        json={
            "name": "Deadline Pipeline",
            "book_id": BOOK_ID,
            "deadline": deadline,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["deadline"] is not None


# ── Tests: List Pipelines ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_pipelines_empty(client: AsyncClient):
    resp = await client.get(_pipeline_url(), params={"org_id": ORG_ID})
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_list_pipelines_returns_created(client: AsyncClient):
    # Create two pipelines
    await client.post(
        _pipeline_url(),
        params={"org_id": ORG_ID},
        json={"name": "Pipeline A", "book_id": BOOK_ID},
    )
    await client.post(
        _pipeline_url(),
        params={"org_id": ORG_ID},
        json={"name": "Pipeline B", "book_id": BOOK_ID},
    )
    resp = await client.get(_pipeline_url(), params={"org_id": ORG_ID})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_pipelines_filter_by_status(client: AsyncClient):
    # Create a draft pipeline
    resp = await client.post(
        _pipeline_url(),
        params={"org_id": ORG_ID},
        json={"name": "Draft Pipeline", "book_id": BOOK_ID},
    )
    assert resp.status_code == 201

    # Filter for active (should be empty)
    resp = await client.get(_pipeline_url(), params={"org_id": ORG_ID, "status": "active"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 0

    # Filter for draft (should find it)
    resp = await client.get(_pipeline_url(), params={"org_id": ORG_ID, "status": "draft"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


# ── Tests: Get Pipeline Detail ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_pipeline_detail(client: AsyncClient):
    create_resp = await client.post(
        _pipeline_url(),
        params={"org_id": ORG_ID},
        json={"name": "Detail Pipeline", "book_id": BOOK_ID},
    )
    pipeline_id = create_resp.json()["id"]

    resp = await client.get(_pipeline_url(f"/{pipeline_id}"), params={"org_id": ORG_ID})
    assert resp.status_code == 200
    assert resp.json()["id"] == pipeline_id
    assert resp.json()["tasks"] == []


@pytest.mark.asyncio
async def test_get_pipeline_not_found(client: AsyncClient):
    fake_id = str(uuid.uuid4())
    resp = await client.get(_pipeline_url(f"/{fake_id}"), params={"org_id": ORG_ID})
    assert resp.status_code == 404


# ── Tests: Update Pipeline ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_pipeline_name(client: AsyncClient):
    create_resp = await client.post(
        _pipeline_url(),
        params={"org_id": ORG_ID},
        json={"name": "Old Name", "book_id": BOOK_ID},
    )
    pipeline_id = create_resp.json()["id"]

    resp = await client.patch(
        _pipeline_url(f"/{pipeline_id}"),
        params={"org_id": ORG_ID},
        json={"name": "New Name"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_update_pipeline_status_transition(client: AsyncClient):
    create_resp = await client.post(
        _pipeline_url(),
        params={"org_id": ORG_ID},
        json={"name": "Transition Test", "book_id": BOOK_ID},
    )
    pipeline_id = create_resp.json()["id"]

    # Draft -> Active
    resp = await client.patch(
        _pipeline_url(f"/{pipeline_id}"),
        params={"org_id": ORG_ID},
        json={"status": "active"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


@pytest.mark.asyncio
async def test_update_pipeline_invalid_transition(client: AsyncClient):
    create_resp = await client.post(
        _pipeline_url(),
        params={"org_id": ORG_ID},
        json={"name": "Invalid Transition", "book_id": BOOK_ID},
    )
    pipeline_id = create_resp.json()["id"]

    # Draft -> Completed (invalid)
    resp = await client.patch(
        _pipeline_url(f"/{pipeline_id}"),
        params={"org_id": ORG_ID},
        json={"status": "completed"},
    )
    assert resp.status_code == 422


# ── Tests: Add Task ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_task_to_pipeline(client: AsyncClient):
    create_resp = await client.post(
        _pipeline_url(),
        params={"org_id": ORG_ID},
        json={"name": "Task Pipeline", "book_id": BOOK_ID},
    )
    pipeline_id = create_resp.json()["id"]

    resp = await client.post(
        _pipeline_url(f"/{pipeline_id}/tasks"),
        params={"org_id": ORG_ID},
        json={"title": "Write chapter 1", "type": "writing"},
    )
    assert resp.status_code == 201
    task = resp.json()
    assert task["title"] == "Write chapter 1"
    assert task["type"] == "writing"
    assert task["status"] == "pending"


@pytest.mark.asyncio
async def test_add_task_with_dependencies(client: AsyncClient):
    create_resp = await client.post(
        _pipeline_url(),
        params={"org_id": ORG_ID},
        json={"name": "Dep Pipeline", "book_id": BOOK_ID},
    )
    pipeline_id = create_resp.json()["id"]

    # Task 1
    t1_resp = await client.post(
        _pipeline_url(f"/{pipeline_id}/tasks"),
        params={"org_id": ORG_ID},
        json={"title": "Writing", "type": "writing"},
    )
    t1_id = t1_resp.json()["id"]

    # Task 2 depends on Task 1
    t2_resp = await client.post(
        _pipeline_url(f"/{pipeline_id}/tasks"),
        params={"org_id": ORG_ID},
        json={
            "title": "Editing",
            "type": "editing",
            "depends_on": [t1_id],
        },
    )
    assert t2_resp.status_code == 201
    t2 = t2_resp.json()
    assert t1_id in t2["depends_on"]


# ── Tests: Update Task ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_task_status(client: AsyncClient):
    create_resp = await client.post(
        _pipeline_url(),
        params={"org_id": ORG_ID},
        json={"name": "Status Pipeline", "book_id": BOOK_ID},
    )
    pipeline_id = create_resp.json()["id"]

    task_resp = await client.post(
        _pipeline_url(f"/{pipeline_id}/tasks"),
        params={"org_id": ORG_ID},
        json={"title": "Test Task", "type": "writing"},
    )
    task_id = task_resp.json()["id"]

    # pending -> in_progress
    resp = await client.patch(
        _pipeline_url(f"/{pipeline_id}/tasks/{task_id}"),
        params={"org_id": ORG_ID},
        json={"status": "in_progress"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_update_task_invalid_transition(client: AsyncClient):
    create_resp = await client.post(
        _pipeline_url(),
        params={"org_id": ORG_ID},
        json={"name": "Invalid Task", "book_id": BOOK_ID},
    )
    pipeline_id = create_resp.json()["id"]

    task_resp = await client.post(
        _pipeline_url(f"/{pipeline_id}/tasks"),
        params={"org_id": ORG_ID},
        json={"title": "Test Task", "type": "writing"},
    )
    task_id = task_resp.json()["id"]

    # pending -> completed (invalid, must go through in_progress)
    resp = await client.patch(
        _pipeline_url(f"/{pipeline_id}/tasks/{task_id}"),
        params={"org_id": ORG_ID},
        json={"status": "completed"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_complete_task_sets_completed_at(client: AsyncClient):
    create_resp = await client.post(
        _pipeline_url(),
        params={"org_id": ORG_ID},
        json={"name": "Complete Pipeline", "book_id": BOOK_ID},
    )
    pipeline_id = create_resp.json()["id"]

    task_resp = await client.post(
        _pipeline_url(f"/{pipeline_id}/tasks"),
        params={"org_id": ORG_ID},
        json={"title": "Task to Complete", "type": "writing"},
    )
    task_id = task_resp.json()["id"]

    # pending -> in_progress
    await client.patch(
        _pipeline_url(f"/{pipeline_id}/tasks/{task_id}"),
        params={"org_id": ORG_ID},
        json={"status": "in_progress"},
    )

    # in_progress -> completed
    resp = await client.patch(
        _pipeline_url(f"/{pipeline_id}/tasks/{task_id}"),
        params={"org_id": ORG_ID},
        json={"status": "completed"},
    )
    assert resp.status_code == 200
    assert resp.json()["completed_at"] is not None


# ── Tests: Timeline ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_timeline(client: AsyncClient):
    create_resp = await client.post(
        _pipeline_url(),
        params={"org_id": ORG_ID},
        json={"name": "Timeline Pipeline", "book_id": BOOK_ID},
    )
    pipeline_id = create_resp.json()["id"]

    # Add tasks
    await client.post(
        _pipeline_url(f"/{pipeline_id}/tasks"),
        params={"org_id": ORG_ID},
        json={"title": "Writing", "type": "writing"},
    )
    await client.post(
        _pipeline_url(f"/{pipeline_id}/tasks"),
        params={"org_id": ORG_ID},
        json={"title": "Editing", "type": "editing"},
    )

    resp = await client.get(
        _pipeline_url(f"/{pipeline_id}/timeline"),
        params={"org_id": ORG_ID},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["pipeline_id"] == pipeline_id
    assert len(data["tasks"]) == 2
    assert "critical_path" in data


@pytest.mark.asyncio
async def test_timeline_not_found(client: AsyncClient):
    fake_id = str(uuid.uuid4())
    resp = await client.get(_pipeline_url(f"/{fake_id}/timeline"), params={"org_id": ORG_ID})
    assert resp.status_code == 404


# ── Tests: Templates ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_template(client: AsyncClient):
    resp = await client.post(
        _pipeline_url("/templates"),
        params={"org_id": ORG_ID},
        json={
            "name": "Standard Book Pipeline",
            "description": "A standard editorial pipeline",
            "task_definitions": [
                {"title": "Draft", "type": "writing", "estimated_days": 14},
                {
                    "title": "Edit",
                    "type": "editing",
                    "depends_on": [],
                    "estimated_days": 7,
                },
            ],
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Standard Book Pipeline"
    assert len(data["task_definitions"]) == 2


@pytest.mark.asyncio
async def test_list_templates(client: AsyncClient):
    # Create a template first
    await client.post(
        _pipeline_url("/templates"),
        params={"org_id": ORG_ID},
        json={
            "name": "Template 1",
            "task_definitions": [],
        },
    )

    resp = await client.get(_pipeline_url("/templates"), params={"org_id": ORG_ID})
    assert resp.status_code == 200
    templates = resp.json()
    assert len(templates) >= 1
    assert templates[0]["name"] == "Template 1"


@pytest.mark.asyncio
async def test_list_templates_empty(client: AsyncClient):
    resp = await client.get(_pipeline_url("/templates"), params={"org_id": ORG_ID})
    assert resp.status_code == 200
    assert resp.json() == []
