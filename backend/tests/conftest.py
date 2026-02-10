"""Pytest fixtures for the SelfPublisherForge backend test suite.

Provides:
* ``test_app`` / ``client`` -- async HTTPX test client against a fresh FastAPI app
* ``test_db`` -- async SQLAlchemy session backed by an in-memory SQLite database
* ``mock_redis`` -- a fake Redis instance (``fakeredis.aioredis``)
* ``test_user_factory`` -- factory function to generate user dicts / JWT tokens
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings
from app.core.security import create_access_token
from app.database import Base

# ---------------------------------------------------------------------------
# Settings override for tests
# ---------------------------------------------------------------------------

settings = get_settings()


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean async database session for each test.

    Uses SQLite in-memory via aiosqlite to avoid needing a real Postgres.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# ---------------------------------------------------------------------------
# Mock Redis fixture
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def mock_redis():
    """Return a fakeredis async Redis instance.

    Falls back to a simple dict-based stub if ``fakeredis`` is not installed.
    """
    try:
        import fakeredis.aioredis

        redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        yield redis
        await redis.aclose()
    except ImportError:
        # Minimal in-memory stub so tests can run without fakeredis
        yield _DictRedisStub()


class _DictRedisStub:
    """Minimal Redis-like async stub backed by a plain dict (test fallback)."""

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._store[key] = value

    async def delete(self, *keys: str) -> int:
        deleted = 0
        for k in keys:
            if k in self._store:
                del self._store[k]
                deleted += 1
        return deleted

    async def ping(self) -> bool:
        return True

    async def zremrangebyscore(self, key: str, _min: float, _max: float) -> int:
        return 0

    async def zadd(self, key: str, mapping: dict[str, float]) -> int:
        if key not in self._store:
            self._store[key] = {}
        self._store[key].update(mapping)
        return len(mapping)

    async def zcard(self, key: str) -> int:
        data = self._store.get(key, {})
        return len(data) if isinstance(data, dict) else 0

    async def expire(self, key: str, seconds: int) -> bool:
        return True

    def pipeline(self) -> "_PipelineStub":
        return _PipelineStub(self)


class _PipelineStub:
    """Pipeline stub that records calls and executes them sequentially."""

    def __init__(self, redis: _DictRedisStub) -> None:
        self._redis = redis
        self._calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def __getattr__(self, name: str):
        def _record(*args: Any, **kwargs: Any) -> "_PipelineStub":
            self._calls.append((name, args, kwargs))
            return self
        return _record

    async def execute(self) -> list[Any]:
        results: list[Any] = []
        for method_name, args, kwargs in self._calls:
            method = getattr(self._redis, method_name, None)
            if method:
                result = await method(*args, **kwargs)
                results.append(result)
            else:
                results.append(None)
        return results


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def test_app():
    """Create a fresh FastAPI app instance for testing."""
    from app.main import create_app

    app = create_app()
    return app


@pytest_asyncio.fixture
async def client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTPX client wired to the test app."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ---------------------------------------------------------------------------
# User factory
# ---------------------------------------------------------------------------

class _UserFactory:
    """Factory for generating test user dicts and JWT tokens."""

    def __call__(
        self,
        *,
        user_id: str | None = None,
        org_id: str | None = None,
        email: str | None = None,
        name: str | None = None,
        role: str = "editor",
        plan_tier: str = "free",
    ) -> dict[str, Any]:
        uid = user_id or str(uuid.uuid4())
        oid = org_id or str(uuid.uuid4())
        return {
            "user_id": uid,
            "org_id": oid,
            "email": email or f"test-{uid[:8]}@example.com",
            "name": name or f"Test User {uid[:8]}",
            "role": role,
            "plan_tier": plan_tier,
        }

    def with_token(
        self,
        *,
        user_id: str | None = None,
        org_id: str | None = None,
        role: str = "editor",
        plan_tier: str = "free",
    ) -> tuple[dict[str, Any], str]:
        """Return ``(user_dict, bearer_token)``."""
        user = self(user_id=user_id, org_id=org_id, role=role, plan_tier=plan_tier)
        token = create_access_token(
            data={
                "sub": user["user_id"],
                "org_id": user["org_id"],
                "role": user["role"],
            },
            expires_delta=timedelta(hours=1),
        )
        return user, token

    def auth_headers(
        self,
        *,
        user_id: str | None = None,
        org_id: str | None = None,
        role: str = "editor",
        plan_tier: str = "free",
    ) -> dict[str, str]:
        """Return headers dict with Authorization, X-User-ID, and X-Plan-Tier."""
        user, token = self.with_token(
            user_id=user_id, org_id=org_id, role=role, plan_tier=plan_tier,
        )
        return {
            "Authorization": f"Bearer {token}",
            "X-User-ID": user["user_id"],
            "X-Plan-Tier": plan_tier,
        }


@pytest.fixture
def test_user_factory() -> _UserFactory:
    """Provide a user factory for generating test users and tokens."""
    return _UserFactory()
