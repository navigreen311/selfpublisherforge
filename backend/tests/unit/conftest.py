"""Shared fixtures for unit tests."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_system.models import (
    Agent,
    AgentBudget,
    AgentTask,
    AgentType,
    PermissionLevel,
)
from tests.conftest import TestingSessionLocal, engine


@pytest.fixture
def org_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def sample_agent(org_id: uuid.UUID) -> Agent:
    """Return a detached Agent instance for pure-unit tests."""
    agent = Agent(
        id=uuid.uuid4(),
        org_id=org_id,
        agent_type=AgentType.RESEARCH,
        name="Test Agent",
        description="A test agent",
        permission_level=PermissionLevel.AUTO_EXECUTE_LOW,
        model_id="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        temperature=0.7,
        is_enabled=True,
    )
    return agent


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    """Yield a fresh database session with tables created/dropped per test."""
    from app.database import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def sample_budget(
    db: AsyncSession,
    org_id: uuid.UUID,
    sample_agent: Agent,
) -> AgentBudget:
    """Create and persist a budget for the sample agent."""
    # Persist the agent first
    db.add(sample_agent)
    await db.flush()
    await db.refresh(sample_agent)

    budget = AgentBudget(
        org_id=org_id,
        agent_id=sample_agent.id,
        daily_token_limit=100000,
        daily_usd_limit=10.0,
        monthly_usd_limit=200.0,
        tokens_used_today=0,
        usd_used_today=0.0,
        usd_used_this_month=0.0,
        total_tokens_used=0,
        total_usd_used=0.0,
        last_reset_daily=datetime.now(UTC),
        last_reset_monthly=datetime.now(UTC),
    )
    db.add(budget)
    await db.flush()
    await db.refresh(budget)
    return budget


@pytest_asyncio.fixture
async def sample_task(
    db: AsyncSession,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    sample_agent: Agent,
    sample_budget: AgentBudget,
) -> AgentTask:
    """Create and persist a task for a draft-only agent.

    Depends on sample_budget to ensure the agent is already persisted.
    """
    # The executor tests expect sample_agent to be DRAFT_ONLY
    sample_agent.permission_level = PermissionLevel.DRAFT_ONLY
    await db.flush()

    task = AgentTask(
        org_id=org_id,
        agent_id=sample_agent.id,
        title="Test Task",
        description="A test task for the executor",
        input_data={"context": "unit test"},
        created_by=user_id,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


@pytest_asyncio.fixture
async def auto_agent(
    db: AsyncSession,
    org_id: uuid.UUID,
) -> Agent:
    """Create and persist an agent with AUTO_EXECUTE_LOW permission."""
    agent = Agent(
        id=uuid.uuid4(),
        org_id=org_id,
        agent_type=AgentType.WRITING_ASSISTANT,
        name="Auto Agent",
        description="An auto-execute agent",
        permission_level=PermissionLevel.AUTO_EXECUTE_LOW,
        model_id="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        temperature=0.7,
        is_enabled=True,
    )
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return agent
