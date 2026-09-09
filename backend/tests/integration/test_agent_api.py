"""Integration tests for the Agent System API endpoints.

Tests use an in-memory SQLite database and override FastAPI dependencies.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import Base, get_db
from app.main import create_app
from app.modules.agent_system.models import (
    Agent,
    AgentBudget,
    AgentTask,
    AgentType,
    AgentWorkflow,
    AuditTrail,
    PermissionLevel,
    TaskStatus,
)
from tests.conftest import TestingSessionLocal
from tests.conftest import engine as test_engine

TestSessionLocal = TestingSessionLocal


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def org_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def admin_user(org_id: uuid.UUID, user_id: uuid.UUID) -> dict:
    return {"user_id": user_id, "org_id": org_id, "role": "admin"}


@pytest.fixture
def viewer_user(org_id: uuid.UUID, user_id: uuid.UUID) -> dict:
    return {"user_id": user_id, "org_id": org_id, "role": "viewer"}


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db: AsyncSession, admin_user: dict) -> AsyncClient:
    """Create a test HTTP client with overridden dependencies."""
    app = create_app()

    async def override_get_db():
        yield db

    def override_get_current_user():
        return admin_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def viewer_client(db: AsyncSession, viewer_user: dict) -> AsyncClient:
    """Client with viewer-level permissions."""
    app = create_app()

    async def override_get_db():
        yield db

    def override_get_current_user():
        return viewer_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def seeded_agent(db: AsyncSession, org_id: uuid.UUID) -> Agent:
    agent = Agent(
        org_id=org_id,
        agent_type=AgentType.RESEARCH,
        name="Seeded Research Agent",
        description="Pre-seeded for tests",
        permission_level=PermissionLevel.DRAFT_ONLY,
        model_id="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        temperature=0.7,
    )
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return agent


@pytest_asyncio.fixture
async def seeded_task(
    db: AsyncSession,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    seeded_agent: Agent,
) -> AgentTask:
    task = AgentTask(
        org_id=org_id,
        agent_id=seeded_agent.id,
        title="Test Task",
        status=TaskStatus.AWAITING_APPROVAL,
        input_data={"context": "test"},
        output_data={"text": "output"},
        tokens_used=500,
        cost_usd=0.0015,
        quality_score=0.85,
        created_by=user_id,
        started_at=datetime.now(UTC),
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


@pytest_asyncio.fixture
async def seeded_budget(
    db: AsyncSession,
    org_id: uuid.UUID,
    seeded_agent: Agent,
) -> AgentBudget:
    budget = AgentBudget(
        org_id=org_id,
        agent_id=seeded_agent.id,
        daily_token_limit=100000,
        daily_usd_limit=10.0,
        monthly_usd_limit=200.0,
        last_reset_daily=datetime.now(UTC),
        last_reset_monthly=datetime.now(UTC),
    )
    db.add(budget)
    await db.flush()
    await db.refresh(budget)
    return budget


# ---------------------------------------------------------------------------
# Agent endpoints
# ---------------------------------------------------------------------------


class TestListAgents:
    @pytest.mark.asyncio
    async def test_list_agents_seeds_defaults(self, client: AsyncClient):
        """GET /agents should seed defaults if none exist."""
        resp = await client.get("/api/v1/agents")
        assert resp.status_code == 200

        data = resp.json()
        assert "items" in data
        assert data["total_count"] >= 4  # 4 default agents

    @pytest.mark.asyncio
    async def test_list_agents_returns_existing(
        self,
        client: AsyncClient,
        seeded_agent: Agent,
    ):
        """GET /agents should return seeded agents."""
        resp = await client.get("/api/v1/agents")
        assert resp.status_code == 200

        data = resp.json()
        assert data["total_count"] >= 1
        names = [a["name"] for a in data["items"]]
        assert "Seeded Research Agent" in names


class TestGetAgentConfig:
    @pytest.mark.asyncio
    async def test_get_config(self, client: AsyncClient, seeded_agent: Agent):
        resp = await client.get(f"/api/v1/agents/{seeded_agent.id}/config")
        assert resp.status_code == 200

        data = resp.json()
        assert data["id"] == str(seeded_agent.id)
        assert data["name"] == "Seeded Research Agent"
        assert data["permission_level"] == "draft_only"

    @pytest.mark.asyncio
    async def test_get_config_not_found(self, client: AsyncClient):
        fake_id = uuid.uuid4()
        resp = await client.get(f"/api/v1/agents/{fake_id}/config")
        assert resp.status_code == 404


class TestUpdateAgentConfig:
    @pytest.mark.asyncio
    async def test_update_config(self, client: AsyncClient, seeded_agent: Agent):
        resp = await client.patch(
            f"/api/v1/agents/{seeded_agent.id}/config",
            json={"name": "Updated Agent", "max_tokens": 8192},
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["name"] == "Updated Agent"
        assert data["max_tokens"] == 8192

    @pytest.mark.asyncio
    async def test_update_permission_level(self, client: AsyncClient, seeded_agent: Agent):
        resp = await client.patch(
            f"/api/v1/agents/{seeded_agent.id}/config",
            json={"permission_level": "auto_execute_low"},
        )
        assert resp.status_code == 200
        assert resp.json()["permission_level"] == "auto_execute_low"


# ---------------------------------------------------------------------------
# Task endpoints
# ---------------------------------------------------------------------------


class TestCreateTask:
    @pytest.mark.asyncio
    async def test_create_task(self, client: AsyncClient, seeded_agent: Agent):
        resp = await client.post(
            "/api/v1/agents/tasks",
            json={
                "agent_id": str(seeded_agent.id),
                "title": "New Research Task",
                "description": "Research self-publishing trends",
                "priority": "high",
                "input_data": {"topic": "self-publishing 2026"},
            },
        )
        assert resp.status_code == 201

        data = resp.json()
        assert data["title"] == "New Research Task"
        assert data["status"] == "pending"
        assert data["priority"] == "high"

    @pytest.mark.asyncio
    async def test_create_task_agent_not_found(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/agents/tasks",
            json={
                "agent_id": str(uuid.uuid4()),
                "title": "Bad Task",
            },
        )
        assert resp.status_code == 404


class TestListTasks:
    @pytest.mark.asyncio
    async def test_list_tasks(
        self,
        client: AsyncClient,
        seeded_task: AgentTask,
    ):
        resp = await client.get("/api/v1/agents/tasks")
        assert resp.status_code == 200

        data = resp.json()
        assert data["total_count"] >= 1

    @pytest.mark.asyncio
    async def test_filter_by_status(
        self,
        client: AsyncClient,
        seeded_task: AgentTask,
    ):
        resp = await client.get("/api/v1/agents/tasks?status=awaiting_approval")
        assert resp.status_code == 200

        data = resp.json()
        for item in data["items"]:
            assert item["status"] == "awaiting_approval"


class TestGetTask:
    @pytest.mark.asyncio
    async def test_get_task(self, client: AsyncClient, seeded_task: AgentTask):
        resp = await client.get(f"/api/v1/agents/tasks/{seeded_task.id}")
        assert resp.status_code == 200

        data = resp.json()
        assert data["id"] == str(seeded_task.id)
        assert data["output_data"] is not None

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, client: AsyncClient):
        resp = await client.get(f"/api/v1/agents/tasks/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestApproveTask:
    @pytest.mark.asyncio
    async def test_approve_awaiting_task(
        self,
        client: AsyncClient,
        seeded_task: AgentTask,
    ):
        resp = await client.post(
            f"/api/v1/agents/tasks/{seeded_task.id}/approve",
            json={"feedback": "Looks good"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"


class TestRejectTask:
    @pytest.mark.asyncio
    async def test_reject_task(
        self,
        client: AsyncClient,
        seeded_task: AgentTask,
    ):
        resp = await client.post(
            f"/api/v1/agents/tasks/{seeded_task.id}/reject",
            json={"reason": "Not accurate", "regenerate": False},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_reject_and_regenerate(
        self,
        client: AsyncClient,
        seeded_task: AgentTask,
    ):
        resp = await client.post(
            f"/api/v1/agents/tasks/{seeded_task.id}/reject",
            json={"reason": "Needs improvement", "regenerate": True},
        )
        assert resp.status_code == 200
        # Returns the new task when regenerate=True
        data = resp.json()
        assert data["status"] == "pending"
        assert data["id"] != str(seeded_task.id)


class TestCancelTask:
    @pytest.mark.asyncio
    async def test_cancel_task(
        self,
        client: AsyncClient,
        seeded_task: AgentTask,
    ):
        resp = await client.post(
            f"/api/v1/agents/tasks/{seeded_task.id}/cancel",
            json={"reason": "No longer needed"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"


# ---------------------------------------------------------------------------
# Workflow endpoints
# ---------------------------------------------------------------------------


class TestCreateWorkflow:
    @pytest.mark.asyncio
    async def test_create_workflow(
        self,
        client: AsyncClient,
        seeded_agent: Agent,
    ):
        resp = await client.post(
            "/api/v1/agents/workflows",
            json={
                "name": "Research & Write",
                "description": "Research then write",
                "steps": [
                    {
                        "agent_id": str(seeded_agent.id),
                        "title": "Research Step",
                        "on_failure": "stop",
                        "max_retries": 0,
                    },
                    {
                        "agent_id": str(seeded_agent.id),
                        "title": "Write Step",
                        "on_failure": "skip",
                        "max_retries": 1,
                    },
                ],
            },
        )
        assert resp.status_code == 201

        data = resp.json()
        assert data["name"] == "Research & Write"
        assert data["status"] == "draft"
        assert len(data["steps"]) == 2


class TestListWorkflows:
    @pytest.mark.asyncio
    async def test_list_workflows(
        self,
        client: AsyncClient,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        seeded_agent: Agent,
    ):
        # Create a workflow
        wf = AgentWorkflow(
            org_id=org_id,
            name="Test WF",
            steps=[{"agent_id": str(seeded_agent.id), "title": "Step 1", "status": "pending"}],
            created_by=user_id,
        )
        db.add(wf)
        await db.flush()

        resp = await client.get("/api/v1/agents/workflows")
        assert resp.status_code == 200

        data = resp.json()
        assert data["total_count"] >= 1


# ---------------------------------------------------------------------------
# Budget endpoints
# ---------------------------------------------------------------------------


class TestGetBudgets:
    @pytest.mark.asyncio
    async def test_get_budgets(
        self,
        client: AsyncClient,
        seeded_budget: AgentBudget,
    ):
        resp = await client.get("/api/v1/agents/budgets")
        assert resp.status_code == 200

        data = resp.json()
        assert len(data["items"]) >= 1
        budget = data["items"][0]
        assert "daily_token_pct" in budget
        assert "daily_usd_pct" in budget
        assert "monthly_usd_pct" in budget


class TestUpdateBudgets:
    @pytest.mark.asyncio
    async def test_update_budget(
        self,
        client: AsyncClient,
        seeded_agent: Agent,
        seeded_budget: AgentBudget,
    ):
        resp = await client.patch(
            f"/api/v1/agents/budgets?agent_id={seeded_agent.id}",
            json={"daily_usd_limit": 25.0, "monthly_usd_limit": 500.0},
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["daily_usd_limit"] == 25.0
        assert data["monthly_usd_limit"] == 500.0


# ---------------------------------------------------------------------------
# Emergency stop
# ---------------------------------------------------------------------------


class TestEmergencyStop:
    @pytest.mark.asyncio
    async def test_emergency_stop(
        self,
        client: AsyncClient,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        seeded_agent: Agent,
    ):
        # Create a running task
        task = AgentTask(
            org_id=org_id,
            agent_id=seeded_agent.id,
            title="Running Task",
            status=TaskStatus.RUNNING,
            created_by=user_id,
        )
        db.add(task)
        await db.flush()

        resp = await client.post("/api/v1/agents/emergency-stop")
        assert resp.status_code == 200

        data = resp.json()
        assert data["tasks_cancelled"] >= 1
        assert "Emergency stop complete" in data["message"]


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------


class TestAuditTrail:
    @pytest.mark.asyncio
    async def test_get_audit_trail(
        self,
        client: AsyncClient,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
    ):
        # Create an audit entry
        entry = AuditTrail(
            org_id=org_id,
            action="config_updated",
            actor_id=user_id,
            actor_type="user",
            resource_type="agent",
            resource_id=uuid.uuid4(),
            details={"test": True},
        )
        db.add(entry)
        await db.flush()

        resp = await client.get("/api/v1/agents/audit")
        assert resp.status_code == 200

        data = resp.json()
        assert data["total_count"] >= 1
        assert data["items"][0]["action"] == "config_updated"

    @pytest.mark.asyncio
    async def test_audit_pagination(
        self,
        client: AsyncClient,
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
    ):
        # Create multiple audit entries
        for i in range(5):
            entry = AuditTrail(
                org_id=org_id,
                action="config_updated",
                actor_id=user_id,
                actor_type="user",
                resource_type="agent",
                resource_id=uuid.uuid4(),
            )
            db.add(entry)
        await db.flush()

        resp = await client.get("/api/v1/agents/audit?limit=2")
        assert resp.status_code == 200

        data = resp.json()
        assert len(data["items"]) == 2
        assert data["has_more"] is True
        assert data["next_cursor"] is not None
