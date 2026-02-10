"""Shared test fixtures for the analytics module tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
def org_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_user(org_id: uuid.UUID, user_id: uuid.UUID) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "org_id": org_id,
        "role": "owner",
    }


@pytest.fixture
def mock_db() -> AsyncMock:
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    return db


@pytest_asyncio.fixture
async def app():
    """Create a test FastAPI application."""
    return create_app()


@pytest_asyncio.fixture
async def client(app, mock_db, mock_user) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client with mocked dependencies."""
    from app.database import get_db
    from app.core.dependencies import get_current_user

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
