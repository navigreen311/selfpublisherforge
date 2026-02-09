"""Shared pytest fixtures for backend tests.

Uses an in-memory SQLite database for fast, isolated tests.
"""

import asyncio
from typing import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

# ---------------------------------------------------------------------------
# Override settings BEFORE any app module is imported so that the config
# singleton picks up test values.
# ---------------------------------------------------------------------------
import os

os.environ["SECRET_KEY"] = "test-secret-key-for-ci"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///test.db"

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

# In-memory async SQLite engine for tests
TEST_DATABASE_URL = "sqlite+aiosqlite://"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the whole test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test and drop them after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional DB session that rolls back after each test."""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTPX async client wired to the FastAPI app with a test DB session."""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    # Register the auth router for integration tests
    from app.modules.auth.router import router as auth_router
    from app.config import get_settings

    settings = get_settings()
    prefix = f"{settings.API_V1_PREFIX}/auth"

    # Only add if not already registered (avoids duplicate on re-runs)
    route_paths = {r.path for r in app.routes}
    if f"{prefix}/register" not in route_paths:
        app.include_router(auth_router, prefix=prefix, tags=["auth"])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
