"""Shared test fixtures for Review Intelligence tests."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database import Base


# Use an in-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
def org_id() -> uuid.UUID:
    """A test organization ID."""
    return uuid.uuid4()


@pytest.fixture
def book_id() -> uuid.UUID:
    """A test book ID."""
    return uuid.uuid4()


@pytest.fixture
def user_id() -> uuid.UUID:
    """A test user ID."""
    return uuid.uuid4()


@pytest.fixture
def current_user(org_id, user_id):
    """Mock current user dict as returned by get_current_user."""
    return {
        "user_id": user_id,
        "org_id": org_id,
        "role": "owner",
    }


def make_review(
    org_id: uuid.UUID,
    book_id: uuid.UUID,
    star_rating: float = 4.0,
    body: str = "Great book!",
    sentiment: str | None = None,
    sentiment_score: float | None = None,
    is_competitor: bool = False,
    review_date: datetime | None = None,
    source: str = "amazon",
):
    """Helper to create a BookReview instance for testing."""
    from app.modules.review_intelligence.models import BookReview

    return BookReview(
        org_id=org_id,
        book_id=book_id,
        source=source,
        star_rating=star_rating,
        body=body,
        sentiment=sentiment,
        sentiment_score=sentiment_score,
        is_competitor=is_competitor,
        review_date=review_date or datetime.now(timezone.utc),
        title="Test Review",
        verified_purchase=True,
    )
