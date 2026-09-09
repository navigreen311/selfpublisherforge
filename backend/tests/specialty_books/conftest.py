"""Standalone conftest for specialty-books coloring tests.

Uses an in-memory SQLite database and does NOT import app.main,
avoiding the chain of router imports that may fail on feature branches.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles

# ---------------------------------------------------------------------------
# SQLite type compilation overrides (must be registered before create_all)
# ---------------------------------------------------------------------------

@compiles(JSONB, "sqlite")
def _jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


@compiles(PG_ARRAY, "sqlite")
def _array_sqlite(type_, compiler, **kw):
    return "TEXT"


@compiles(PG_UUID, "sqlite")
def _uuid_sqlite(type_, compiler, **kw):
    return "CHAR(32)"


# ---------------------------------------------------------------------------
# Import models so they register with Base.metadata
# ---------------------------------------------------------------------------
import app.modules.specialty_books.models_coloring  # noqa: E402
from app.database import Base  # noqa: E402

try:
    import app.modules.specialty_books.models_puzzle  # noqa: F401
except (ImportError, ModuleNotFoundError):
    pass


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def org_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture(scope="session")
def other_org_id() -> uuid.UUID:
    return uuid.uuid4()


def _strip_pg_only(metadata):
    """Remove PostgreSQL-only index kwargs and server_defaults that SQLite cannot handle."""
    for table in metadata.tables.values():
        for col in table.columns:
            if col.server_default is not None:
                col.server_default = None
        idxs_to_drop = []
        for idx in table.indexes:
            if getattr(idx, "dialect_options", {}).get("postgresql", {}):
                pass  # keep but strip options
            idx.dialect_options = {}
        for idx in idxs_to_drop:
            table.indexes.discard(idx)


@pytest_asyncio.fixture
async def db():
    """Yield an async SQLite session with tables created."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    _strip_pg_only(Base.metadata)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
