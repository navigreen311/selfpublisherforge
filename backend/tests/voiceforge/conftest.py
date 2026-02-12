"""Isolated test fixtures for voiceforge tests.

These fixtures replicate the DB setup from the root conftest but avoid
importing ``app.main`` (which triggers a chain of imports that may fail
when model re-exports are incomplete).
"""
from __future__ import annotations

import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from sqlalchemy.dialects.postgresql import (
    JSONB,
    ARRAY as PG_ARRAY,
    UUID as PG_UUID,
)
from sqlalchemy.ext.compiler import compiles

from app.database import Base

# ---------------------------------------------------------------------------
# SQLite-compatible type compilation for PostgreSQL-specific types
# ---------------------------------------------------------------------------


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"


@compiles(PG_ARRAY, "sqlite")
def _compile_array_sqlite(element, compiler, **kw):
    return "TEXT"


@compiles(PG_UUID, "sqlite")
def _compile_pg_uuid_sqlite(element, compiler, **kw):
    return "CHAR(32)"


# ---------------------------------------------------------------------------
# In-memory SQLite engine
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# ---------------------------------------------------------------------------
# Strip PostgreSQL-specific DDL features before creating tables on SQLite
# ---------------------------------------------------------------------------


def _is_pg_only_index(idx) -> bool:
    dialect_opts = getattr(idx, "dialect_options", {})
    pg_opts = dialect_opts.get("postgresql", {})
    if pg_opts.get("using") or pg_opts.get("where") is not None or pg_opts.get("ops"):
        return True
    kw = getattr(idx, "kwargs", {})
    if kw.get("postgresql_using") or kw.get("postgresql_where") is not None or kw.get("postgresql_ops"):
        return True
    return False


@event.listens_for(Base.metadata, "before_create")
def _patch_for_sqlite(target, connection, **kw):
    if connection.dialect.name != "sqlite":
        return
    for table in target.tables.values():
        for column in table.columns:
            if column.server_default is not None:
                sd = column.server_default
                sd_text = ""
                if hasattr(sd, "arg"):
                    if hasattr(sd.arg, "text"):
                        sd_text = str(sd.arg.text)
                    else:
                        sd_text = str(sd.arg)
                pg_functions = ["gen_random_uuid", "uuid_generate"]
                if any(fn in sd_text.lower() for fn in pg_functions):
                    column.server_default = None

        pg_indexes = [idx for idx in table.indexes if _is_pg_only_index(idx)]
        for idx in pg_indexes:
            table.indexes.discard(idx)

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
# Ensure relevant models are registered on Base.metadata
# ---------------------------------------------------------------------------

import app.modules.dictation.models  # noqa: F401, E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a fresh database session with tables created/dropped per test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def org_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000002")
