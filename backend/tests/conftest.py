"""Shared test fixtures for the pricing automation module tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings


@pytest.fixture
def org_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def book_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_current_user(user_id: uuid.UUID, org_id: uuid.UUID) -> dict:
    return {
        "user_id": user_id,
        "org_id": org_id,
        "role": "owner",
    }


@pytest.fixture
def fastapi_app(mock_current_user: dict) -> FastAPI:
    """Create a FastAPI app with the pricing router and mocked auth."""
    from app.core.dependencies import get_current_user
    from app.database import get_db
    from app.modules.pricing_automation.router import router

    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/v1")

    # Override auth dependency
    async def override_get_current_user():
        return mock_current_user

    test_app.dependency_overrides[get_current_user] = override_get_current_user

    return test_app


@pytest_asyncio.fixture
async def mock_db() -> AsyncSession:
    """Create a mock async session."""
    session = AsyncMock(spec=AsyncSession)
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session
