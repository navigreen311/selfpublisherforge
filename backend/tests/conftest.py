"""Shared test fixtures for the backend test suite."""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator, Generator
from datetime import UTC

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import (
    ARRAY as PG_ARRAY,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
)
from sqlalchemy.dialects.postgresql import (
    UUID as PG_UUID,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# ---------------------------------------------------------------------------
# Register SQLite-compatible type compilation for PostgreSQL-specific types
# ---------------------------------------------------------------------------
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import ARRAY as SA_ARRAY

# Ensure all models are imported so Base.metadata knows about them
from app.database import Base, get_db
from app.main import create_app


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(element, compiler, **kw):
    """JSONB -> JSON on SQLite."""
    return "JSON"


@compiles(PG_ARRAY, "sqlite")
def _compile_array_sqlite(element, compiler, **kw):
    """PostgreSQL ARRAY -> TEXT on SQLite."""
    return "TEXT"


@compiles(SA_ARRAY, "sqlite")
def _compile_generic_array_sqlite(element, compiler, **kw):
    """Generic sqlalchemy.ARRAY -> TEXT on SQLite.

    Ten model modules import ARRAY from sqlalchemy rather than from
    sqlalchemy.dialects.postgresql, so the PG_ARRAY rule above never applied
    to them and every fixture touching those tables failed to create a schema.
    """
    return "TEXT"


@compiles(PG_UUID, "sqlite")
def _compile_pg_uuid_sqlite(element, compiler, **kw):
    """PostgreSQL UUID -> CHAR(32) on SQLite."""
    return "CHAR(32)"


# ---------------------------------------------------------------------------
# In-memory SQLite for tests (async via aiosqlite)
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ---------------------------------------------------------------------------
# Neutralize PostgreSQL-specific indexes before table creation on SQLite
# ---------------------------------------------------------------------------


def _is_pg_only_index(idx) -> bool:
    """Return True if the index uses PostgreSQL-specific features that
    would cause a syntax error on SQLite (GIN, BRIN, partial, trgm, etc.)."""
    dialect_opts = getattr(idx, "dialect_options", {})
    pg_opts = dialect_opts.get("postgresql", {})

    # postgresql_using (gin, brin, gist, etc.)
    if pg_opts.get("using"):
        return True

    # postgresql_where (partial indexes)
    if pg_opts.get("where") is not None:
        return True

    # postgresql_ops (e.g. gin_trgm_ops)
    if pg_opts.get("ops"):
        return True

    # Also check older-style attributes for compatibility
    kw = getattr(idx, "kwargs", {})
    if kw.get("postgresql_using"):
        return True
    if kw.get("postgresql_where") is not None:
        return True
    return bool(kw.get("postgresql_ops"))


@event.listens_for(Base.metadata, "before_create")
def _patch_for_sqlite(target, connection, **kw):
    """Adjust PostgreSQL-specific schema features when running on SQLite.

    This handles:
    1. Removing server_default values that use PG-specific functions
       (gen_random_uuid, NOW(), etc.)
    2. Removing PostgreSQL-specific indexes (GIN, BRIN, partial, trgm)
    3. Stripping ARRAY server_defaults like '{}' that SQLite cannot parse
    """
    if connection.dialect.name != "sqlite":
        return

    for table in target.tables.values():
        # ---- Fix columns ----
        for column in table.columns:
            if column.server_default is not None:
                sd = column.server_default
                sd_text = ""
                if hasattr(sd, "arg"):
                    sd_text = str(sd.arg.text) if hasattr(sd.arg, "text") else str(sd.arg)

                # Strip PG-only function calls in server_default
                pg_functions = ["gen_random_uuid", "uuid_generate"]
                if any(fn in sd_text.lower() for fn in pg_functions):
                    column.server_default = None

        # ---- Remove PG-only indexes ----
        pg_indexes = [idx for idx in table.indexes if _is_pg_only_index(idx)]
        for idx in pg_indexes:
            table.indexes.discard(idx)

        # ---- Deduplicate indexes by name ----
        # When two model files define the same table with extend_existing,
        # duplicate Index objects (same name) can accumulate and cause
        # "index already exists" errors on SQLite.
        seen_names: set[str] = set()
        dupes = []
        for idx in table.indexes:
            if idx.name in seen_names:
                dupes.append(idx)
            else:
                seen_names.add(idx.name)
        for idx in dupes:
            table.indexes.discard(idx)


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

    logger = logging.getLogger(__name__)

    async def _override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except (SQLAlchemyError, ValueError, TypeError, KeyError) as exc:
            logger.error("DB error in test session override: %s", exc, exc_info=True)
            await db_session.rollback()
            raise

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Yield the async engine after creating all tables, then drop them."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session (alias used by integration tests)."""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
def org_id() -> uuid.UUID:
    """Return the placeholder org ID used by the routers."""
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


def make_review(
    org_id: uuid.UUID | None = None,
    book_id: uuid.UUID | None = None,
    source: str = "amazon",
    star_rating: float = 3.0,
    body: str = "",
    sentiment: str | None = None,
    sentiment_score: float | None = None,
    is_competitor: bool = False,
    review_date=None,
    **kwargs,
):
    """Factory helper to create a BookReview ORM instance for tests."""
    from datetime import datetime

    from app.modules.review_intelligence.models import BookReview

    return BookReview(
        org_id=org_id or uuid.uuid4(),
        book_id=book_id or uuid.uuid4(),
        source=source,
        star_rating=star_rating,
        body=body,
        sentiment=sentiment,
        sentiment_score=sentiment_score,
        is_competitor=is_competitor,
        review_date=review_date or datetime.now(UTC),
        **kwargs,
    )
