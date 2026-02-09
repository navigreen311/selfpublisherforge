"""Shared test fixtures for the backend test suite."""
from __future__ import annotations

import asyncio
import uuid
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.database import Base, get_db
from app.main import create_app

# Ensure all models are imported so Base.metadata knows about them
import app.models  # noqa: F401

# ---------------------------------------------------------------------------
# In-memory SQLite for tests (async via aiosqlite)
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# ---------------------------------------------------------------------------
# Strip PostgreSQL-only server_defaults before CREATE TABLE on SQLite
# ---------------------------------------------------------------------------

@event.listens_for(Base.metadata, "before_create")
def _strip_pg_server_defaults(target, connection, **kw):
    """Remove server_default values that use PostgreSQL-specific functions
    (e.g. gen_random_uuid()) when running against SQLite for tests.
    The Python-side ``default`` still handles value generation."""
    if connection.dialect.name == "sqlite":
        for table in target.tables.values():
            for column in table.columns:
                if column.server_default is not None:
                    sd = column.server_default
                    if hasattr(sd, "arg") and hasattr(sd.arg, "text"):
                        if "gen_random_uuid" in str(sd.arg.text):
                            column.server_default = None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create a single event loop for the whole test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a fresh database session with tables created/dropped per test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Yield an HTTP test client with the DB dependency overridden."""

    async def _override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def org_id() -> uuid.UUID:
    """Return the placeholder org ID used by the routers."""
    return uuid.UUID("00000000-0000-0000-0000-000000000001")
