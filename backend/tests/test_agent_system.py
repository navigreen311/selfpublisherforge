"""Tests for the Agent System module router endpoints.

Covers agent listing, task CRUD, workflow creation, budget retrieval,
emergency stop, and audit trail.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base, get_db
from app.core.dependencies import get_current_user
from app.main import create_app
from app.modules.agent_system.models import (
    Agent,
    AgentBudget,
    AgentTask,
    AgentType,
    AgentWorkflow,
    AuditTrail,
    PermissionLevel,
    TaskPriority,
    TaskStatus,
    WorkflowStatus,
)

from tests.conftest import TestingSessionLocal, engine as test_engine


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def org_id() -> uuid.UUID:
    return ORG_ID


@pytest.fixture
def user_id() -> uuid.UUID:
    return USER_ID


@pytest.fixture
def admin_user() -> dict:
    return {"user_id": USER_ID, "org_id": ORG_ID, "role": "admin"}


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db: AsyncSession, admin_user: dict) -> AsyncClient:
    """HTTP test client with DB and auth overrides."""
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

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seeded_agent(db: AsyncSession) -> Agent:
    """Create a test agent in the database."""
    agent = Agent(
        org_id=ORG_ID,
        agent_type=AgentType.RESEARCH,
        name="Test Research Agent",
        description="Agent for testing",
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
async def seeded_task(db: AsyncSession, seeded_agent: Agent) -> AgentTask:
    """Create a test task in AWAITING_APPROVAL state."""
    task = AgentTask(
        org_id=ORG_ID,
        agent_id=seeded_agent.id,
        title="Test Task",
        status=TaskStatus.AWAITING_APPROVAL,
        input_data={"context": "test context"},
        output_data={"text": "sample output"},
        tokens_used=500,
        cost_usd=0.0015,
        quality_score=0.85,
        created_by=USER_ID,
        started_at=datetime.now(timezone.utc),
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


@pytest_asyncio.fixture
async def seeded_budget(db: AsyncSession, seeded_agent: Agent) -> AgentBudget:
    """Create a test budget for the seeded agent."""
    budget = AgentBudget(
        org_id=ORG_ID,
        agent_id=seeded_agent.id,
        daily_token_limit=100000,
        daily_usd_limit=10.0,
        monthly_usd_limit=200.0,
        last_reset_daily=datetime.now(timezone.utc),
        last_reset_monthly=datetime.now(timezone.utc),
    )
    db.add(budget)
    await db.flush()
    await db.refresh(budget)
    return budget


# ---------------------------------------------------------------------------
# Test: List Agents
# ---------------------------------------------------------------------------

class TestListAgents:
    @pytest.mark.asyncio
    async def test_list_agents_seeds_defaults(self, client: AsyncClient):
        """GET /agents should return default agents when none exist."""
        resp = await client.get("/api/v1/agents")
        assert resp.status_code == 200

        data = resp.json()
        assert "items" in data
        assert "total_count" in data
        assert data["total_count"] >= 4  # 4 default agents seeded

    @pytest.mark.asyncio
    async def test_list_agents_includes_seeded(
        self, client: AsyncClient, seeded_agent: Agent
    ):
        """GET /agents should include a pre-seeded agent."""
        resp = await client.get("/api/v1/agents")
        assert resp.status_code == 200

        data = resp.json()
        names = [a["name"] for a in data["items"]]
        assert "Test Research Agent" in names


# ---------------------------------------------------------------------------
# Test: Get Agent Config
# ---------------------------------------------------------------------------

class TestGetAgentConfig:
    @pytest.mark.asyncio
    async def test_get_config_success(
        self, client: AsyncClient, seeded_agent: Agent
    ):
        """GET /agents/{id}/config should return agent details."""
        resp = await client.get(f"/api/v1/agents/{seeded_agent.id}/config")
        assert resp.status_code == 200

        data = resp.json()
        assert data["id"] == str(seeded_agent.id)
        assert data["name"] == "Test Research Agent"
        assert data["permission_level"] == "draft_only"

    @pytest.mark.asyncio
    async def test_get_config_not_found(self, client: AsyncClient):
        """GET /agents/{id}/config should 404 for unknown agent."""
        resp = await client.get(f"/api/v1/agents/{uuid.uuid4()}/config")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Test: Create Task
# ---------------------------------------------------------------------------

class TestCreateTask:
    @pytest.mark.asyncio
    async def test_create_task_success(
        self, client: AsyncClient, seeded_agent: Agent
    ):
        """POST /agents/tasks should create a new task."""
        resp = await client.post(
            "/api/v1/agents/tasks",
            json={
                "agent_id": str(seeded_agent.id),
                "title": "Research self-publishing trends",
                "description": "Analyze 2026 trends",
                "priority": "high",
                "input_data": {"topic": "self-publishing"},
            },
        )
        assert resp.status_code == 201

        data = resp.json()
        assert data["title"] == "Research self-publishing trends"
        assert data["status"] == "pending"
        assert data["priority"] == "high"
        assert data["agent_id"] == str(seeded_agent.id)

    @pytest.mark.asyncio
    async def test_create_task_agent_not_found(self, client: AsyncClient):
        """POST /agents/tasks should 404 if agent does not exist."""
        resp = await client.post(
            "/api/v1/agents/tasks",
            json={
                "agent_id": str(uuid.uuid4()),
                "title": "Orphan Task",
            },
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Test: List Tasks
# ---------------------------------------------------------------------------

class TestListTasks:
    @pytest.mark.asyncio
    async def test_list_tasks(
        self, client: AsyncClient, seeded_task: AgentTask
    ):
        """GET /agents/tasks should return tasks."""
        resp = await client.get("/api/v1/agents/tasks")
        assert resp.status_code == 200

        data = resp.json()
        assert data["total_count"] >= 1
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_list_tasks_filter_by_status(
        self, client: AsyncClient, seeded_task: AgentTask
    ):
        """GET /agents/tasks?status=... should filter correctly."""
        resp = await client.get(
            "/api/v1/agents/tasks?status=awaiting_approval"
        )
        assert resp.status_code == 200

        data = resp.json()
        for item in data["items"]:
            assert item["status"] == "awaiting_approval"


# ---------------------------------------------------------------------------
# Test: Get Task
# ---------------------------------------------------------------------------

class TestGetTask:
    @pytest.mark.asyncio
    async def test_get_task_success(
        self, client: AsyncClient, seeded_task: AgentTask
    ):
        """GET /agents/tasks/{id} should return a task."""
        resp = await client.get(f"/api/v1/agents/tasks/{seeded_task.id}")
        assert resp.status_code == 200

        data = resp.json()
        assert data["id"] == str(seeded_task.id)
        assert data["output_data"] is not None

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, client: AsyncClient):
        """GET /agents/tasks/{id} should 404 for unknown task."""
        resp = await client.get(f"/api/v1/agents/tasks/{uuid.uuid4()}")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Test: Approve Task
# ---------------------------------------------------------------------------

class TestApproveTask:
    @pytest.mark.asyncio
    async def test_approve_task(
        self, client: AsyncClient, seeded_task: AgentTask
    ):
        """POST /agents/tasks/{id}/approve should approve awaiting task."""
        resp = await client.post(
            f"/api/v1/agents/tasks/{seeded_task.id}/approve",
            json={"feedback": "Looks good"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"


# ---------------------------------------------------------------------------
# Test: Reject Task
# ---------------------------------------------------------------------------

class TestRejectTask:
    @pytest.mark.asyncio
    async def test_reject_task(
        self, client: AsyncClient, seeded_task: AgentTask
    ):
        """POST /agents/tasks/{id}/reject should reject awaiting task."""
        resp = await client.post(
            f"/api/v1/agents/tasks/{seeded_task.id}/reject",
            json={"reason": "Not accurate enough", "regenerate": False},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"


# ---------------------------------------------------------------------------
# Test: Cancel Task
# ---------------------------------------------------------------------------

class TestCancelTask:
    @pytest.mark.asyncio
    async def test_cancel_task(
        self, client: AsyncClient, seeded_task: AgentTask
    ):
        """POST /agents/tasks/{id}/cancel should cancel a cancellable task."""
        resp = await client.post(
            f"/api/v1/agents/tasks/{seeded_task.id}/cancel",
            json={"reason": "No longer needed"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"


# ---------------------------------------------------------------------------
# Test: Create Workflow
# ---------------------------------------------------------------------------

class TestCreateWorkflow:
    @pytest.mark.asyncio
    async def test_create_workflow(
        self, client: AsyncClient, seeded_agent: Agent
    ):
        """POST /agents/workflows should create a multi-step workflow."""
        resp = await client.post(
            "/api/v1/agents/workflows",
            json={
                "name": "Research & Write Workflow",
                "description": "Two-step pipeline",
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
        assert data["name"] == "Research & Write Workflow"
        assert data["status"] == "draft"
        assert len(data["steps"]) == 2


# ---------------------------------------------------------------------------
# Test: List Workflows
# ---------------------------------------------------------------------------

class TestListWorkflows:
    @pytest.mark.asyncio
    async def test_list_workflows(
        self,
        client: AsyncClient,
        db: AsyncSession,
        seeded_agent: Agent,
    ):
        """GET /agents/workflows should return workflows."""
        wf = AgentWorkflow(
            org_id=ORG_ID,
            name="Test Workflow",
            steps=[
                {
                    "agent_id": str(seeded_agent.id),
                    "title": "Step 1",
                    "status": "pending",
                }
            ],
            created_by=USER_ID,
        )
        db.add(wf)
        await db.flush()

        resp = await client.get("/api/v1/agents/workflows")
        assert resp.status_code == 200

        data = resp.json()
        assert data["total_count"] >= 1


# ---------------------------------------------------------------------------
# Test: Budgets
# ---------------------------------------------------------------------------

class TestBudgets:
    @pytest.mark.asyncio
    async def test_get_budgets(
        self, client: AsyncClient, seeded_budget: AgentBudget
    ):
        """GET /agents/budgets should return budget status."""
        resp = await client.get("/api/v1/agents/budgets")
        assert resp.status_code == 200

        data = resp.json()
        assert len(data["items"]) >= 1
        budget = data["items"][0]
        assert "daily_token_pct" in budget
        assert "daily_usd_pct" in budget
        assert "monthly_usd_pct" in budget

    @pytest.mark.asyncio
    async def test_update_budget(
        self,
        client: AsyncClient,
        seeded_agent: Agent,
        seeded_budget: AgentBudget,
    ):
        """PATCH /agents/budgets should update budget limits."""
        resp = await client.patch(
            f"/api/v1/agents/budgets?agent_id={seeded_agent.id}",
            json={"daily_usd_limit": 25.0, "monthly_usd_limit": 500.0},
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["daily_usd_limit"] == 25.0
        assert data["monthly_usd_limit"] == 500.0


# ---------------------------------------------------------------------------
# Test: Emergency Stop
# ---------------------------------------------------------------------------

class TestEmergencyStop:
    @pytest.mark.asyncio
    async def test_emergency_stop(
        self,
        client: AsyncClient,
        db: AsyncSession,
        seeded_agent: Agent,
    ):
        """POST /agents/emergency-stop should cancel running tasks."""
        task = AgentTask(
            org_id=ORG_ID,
            agent_id=seeded_agent.id,
            title="Running Task",
            status=TaskStatus.RUNNING,
            created_by=USER_ID,
        )
        db.add(task)
        await db.flush()

        resp = await client.post("/api/v1/agents/emergency-stop")
        assert resp.status_code == 200

        data = resp.json()
        assert data["tasks_cancelled"] >= 1
        assert "Emergency stop complete" in data["message"]


# ---------------------------------------------------------------------------
# Test: Audit Trail
# ---------------------------------------------------------------------------

class TestAuditTrail:
    @pytest.mark.asyncio
    async def test_get_audit_trail(
        self,
        client: AsyncClient,
        db: AsyncSession,
    ):
        """GET /agents/audit should return audit entries."""
        entry = AuditTrail(
            org_id=ORG_ID,
            action="config_updated",
            actor_id=USER_ID,
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
    ):
        """GET /agents/audit?limit=2 should paginate results."""
        for _ in range(5):
            entry = AuditTrail(
                org_id=ORG_ID,
                action="config_updated",
                actor_id=USER_ID,
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
