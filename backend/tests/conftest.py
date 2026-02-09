"""Shared test fixtures for the Agent System tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import StaticPool, event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base, get_db
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


# ---------------------------------------------------------------------------
# In-memory SQLite async engine for tests
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Create all tables, yield a session, then drop everything."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ---------------------------------------------------------------------------
# Identity fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def org_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


# ---------------------------------------------------------------------------
# Model factories
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def sample_agent(db: AsyncSession, org_id: uuid.UUID) -> Agent:
    agent = Agent(
        org_id=org_id,
        agent_type=AgentType.RESEARCH,
        name="Test Research Agent",
        description="A test agent",
        permission_level=PermissionLevel.DRAFT_ONLY,
        model_id="claude-sonnet-4-5-20250929",
        system_prompt="You are a test agent.",
        max_tokens=4096,
        temperature=0.7,
    )
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return agent


@pytest_asyncio.fixture
async def auto_agent(db: AsyncSession, org_id: uuid.UUID) -> Agent:
    """An agent with auto-execute low permission."""
    agent = Agent(
        org_id=org_id,
        agent_type=AgentType.EDITOR,
        name="Auto Editor Agent",
        description="Auto-executing editor",
        permission_level=PermissionLevel.AUTO_EXECUTE_LOW,
        model_id="claude-sonnet-4-5-20250929",
        max_tokens=2048,
        temperature=0.5,
    )
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return agent


@pytest_asyncio.fixture
async def sample_budget(
    db: AsyncSession,
    org_id: uuid.UUID,
    sample_agent: Agent,
) -> AgentBudget:
    budget = AgentBudget(
        org_id=org_id,
        agent_id=sample_agent.id,
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


@pytest_asyncio.fixture
async def sample_task(
    db: AsyncSession,
    org_id: uuid.UUID,
    sample_agent: Agent,
    user_id: uuid.UUID,
) -> AgentTask:
    task = AgentTask(
        org_id=org_id,
        agent_id=sample_agent.id,
        title="Test Task",
        description="A test task",
        priority=TaskPriority.MEDIUM,
        input_data={"context": "test context", "instructions": "do something"},
        created_by=user_id,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


@pytest_asyncio.fixture
async def awaiting_task(
    db: AsyncSession,
    org_id: uuid.UUID,
    sample_agent: Agent,
    user_id: uuid.UUID,
) -> AgentTask:
    """A task in awaiting_approval status."""
    task = AgentTask(
        org_id=org_id,
        agent_id=sample_agent.id,
        title="Awaiting Task",
        description="Needs approval",
        status=TaskStatus.AWAITING_APPROVAL,
        priority=TaskPriority.MEDIUM,
        input_data={"context": "test"},
        output_data={"text": "Generated output"},
        tokens_used=500,
        cost_usd=0.0015,
        quality_score=0.85,
        created_by=user_id,
        started_at=datetime.now(timezone.utc),
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


@pytest_asyncio.fixture
async def sample_workflow(
    db: AsyncSession,
    org_id: uuid.UUID,
    sample_agent: Agent,
    user_id: uuid.UUID,
) -> AgentWorkflow:
    workflow = AgentWorkflow(
        org_id=org_id,
        name="Test Workflow",
        description="A test workflow",
        steps=[
            {
                "agent_id": str(sample_agent.id),
                "title": "Step 1: Research",
                "description": "Do research",
                "input_data": {"topic": "test"},
                "condition": None,
                "on_failure": "stop",
                "max_retries": 0,
                "status": "pending",
            },
            {
                "agent_id": str(sample_agent.id),
                "title": "Step 2: Write",
                "description": "Write content",
                "input_data": {"style": "formal"},
                "condition": None,
                "on_failure": "skip",
                "max_retries": 1,
                "status": "pending",
            },
        ],
        created_by=user_id,
    )
    db.add(workflow)
    await db.flush()
    await db.refresh(workflow)
    return workflow
