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
import contextlib

from app.database import Base

with contextlib.suppress(ImportError, ModuleNotFoundError):
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


# `_strip_pg_only` used to live here. It did three destructive things to the
# shared `Base.metadata`, permanently and for the whole process:
#
#   * `idx.dialect_options = {}` on *every* index of *every* table, replacing
#     SQLAlchemy's lazily-populating PopulateDict with a plain dict. After
#     that, `index.dialect_options["sqlite"]` — which the SQLite DDL compiler
#     reads for every CREATE INDEX — raises KeyError: 'sqlite' forever. That
#     single line accounted for 372 errors across suites that never import
#     anything from this directory.
#   * `col.server_default = None` on every column of every table, so later
#     tests lost defaults they relied on.
#   * built an `idxs_to_drop` list, never appended to it, and looped over it.
#
# The root tests/conftest.py already registers a `before_create` listener that
# does this correctly and only for the duration of the DDL. Nothing needs to be
# stripped here.


@pytest_asyncio.fixture
async def db():
    """Yield an async SQLite session with tables created."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
