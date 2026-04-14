"""Tests for the Pen Name Management module (Final Gaps Stream 1).

These tests bypass the full ``Base.metadata.create_all`` path because the
global metadata contains tables from other modules (e.g. ``pipeline_tasks``)
that have ``ARRAY(UUID)`` columns SQLite cannot compile. Instead we create
only the tables our feature needs via raw DDL.
"""
from __future__ import annotations

import sqlite3
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Register a UUID adapter so service-layer SQL that passes ``UUID`` objects
# as bind parameters works against aiosqlite (which otherwise rejects them).
sqlite3.register_adapter(uuid.UUID, lambda u: str(u))
sqlite3.register_adapter(list, lambda xs: __import__("json").dumps(xs))
sqlite3.register_adapter(dict, lambda d: __import__("json").dumps(d))

from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import create_app


TEST_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TEST_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")


SCHEMA_SQL = [
    """
    CREATE TABLE organizations (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        slug TEXT,
        plan TEXT,
        is_active INTEGER DEFAULT 1,
        deleted_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE users (
        id TEXT PRIMARY KEY,
        org_id TEXT NOT NULL,
        email TEXT NOT NULL,
        password_hash TEXT,
        name TEXT,
        role TEXT,
        role_id TEXT NULL,
        org_role TEXT DEFAULT 'owner',
        is_active INTEGER DEFAULT 1,
        email_verified INTEGER DEFAULT 0,
        mfa_enabled INTEGER DEFAULT 0,
        deleted_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE roles (
        id TEXT PRIMARY KEY,
        org_id TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        permissions TEXT NOT NULL DEFAULT '{}',
        is_system INTEGER DEFAULT 0,
        deleted_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE pen_names (
        id TEXT PRIMARY KEY,
        org_id TEXT NOT NULL,
        user_id TEXT NULL,
        name TEXT NOT NULL,
        display_name TEXT,
        bio TEXT,
        brand_guidelines TEXT,
        amazon_author_url TEXT,
        photo_url TEXT,
        genres TEXT DEFAULT '[]',
        is_default INTEGER DEFAULT 0,
        book_count INTEGER DEFAULT 0,
        active INTEGER DEFAULT 1,
        deleted_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE projects (
        id TEXT PRIMARY KEY,
        org_id TEXT NOT NULL,
        title TEXT NOT NULL,
        type TEXT,
        status TEXT,
        pen_name_id TEXT NULL,
        deleted_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE team_invitations (
        id TEXT PRIMARY KEY,
        org_id TEXT NOT NULL,
        email TEXT NOT NULL,
        role_id TEXT NOT NULL,
        invited_by TEXT NOT NULL,
        message TEXT,
        status TEXT DEFAULT 'pending',
        token TEXT NOT NULL UNIQUE,
        expires_at TIMESTAMP NOT NULL,
        accepted_at TIMESTAMP NULL,
        deleted_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
]


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        for ddl in SCHEMA_SQL:
            await conn.execute(sa_text(ddl))
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        # Seed org + user
        await session.execute(
            sa_text(
                "INSERT INTO organizations (id, name, slug, plan) "
                "VALUES (:id, 'Test Org', 'test-org', 'free')"
            ),
            {"id": str(TEST_ORG_ID)},
        )
        await session.execute(
            sa_text(
                "INSERT INTO users (id, org_id, email, password_hash, name, role) "
                "VALUES (:id, :oid, 'u@test.com', 'x', 'U', 'owner')"
            ),
            {"id": str(TEST_USER_ID), "oid": str(TEST_ORG_ID)},
        )
        await session.commit()
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    async def _override_get_db():
        yield db_session
        try:
            await db_session.commit()
        except Exception:
            await db_session.rollback()

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": TEST_USER_ID,
        "org_id": TEST_ORG_ID,
        "role": "owner",
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_list_get_pen_name(client):
    resp = await client.post(
        "/api/v1/pen-names",
        json={
            "display_name": "Jane Doe",
            "bio": "Writes children's books.",
            "genres": ["Children's Books"],
            "is_default": True,
        },
    )
    assert resp.status_code == 201, resp.text
    created = resp.json()
    assert created["display_name"] == "Jane Doe"
    assert created["is_default"] is True
    pid = created["id"]

    resp = await client.get("/api/v1/pen-names")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["id"] == pid

    resp = await client.get(f"/api/v1/pen-names/{pid}")
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Jane Doe"


@pytest.mark.asyncio
async def test_update_pen_name_swaps_default(client):
    await client.post("/api/v1/pen-names",
                      json={"display_name": "A", "is_default": True})
    r2 = await client.post("/api/v1/pen-names",
                           json={"display_name": "B", "is_default": False})
    pid_b = r2.json()["id"]

    r = await client.patch(f"/api/v1/pen-names/{pid_b}", json={"is_default": True})
    assert r.status_code == 200
    assert r.json()["is_default"] is True

    items = (await client.get("/api/v1/pen-names")).json()
    defaults = [p for p in items if p["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["display_name"] == "B"


@pytest.mark.asyncio
async def test_cannot_delete_default_pen_name(client):
    r = await client.post("/api/v1/pen-names",
                          json={"display_name": "Primary", "is_default": True})
    pid = r.json()["id"]
    r = await client.delete(f"/api/v1/pen-names/{pid}")
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_delete_non_default_pen_name(client):
    r1 = await client.post("/api/v1/pen-names",
                           json={"display_name": "Primary", "is_default": True})
    r2 = await client.post("/api/v1/pen-names", json={"display_name": "Secondary"})
    pid = r2.json()["id"]
    r = await client.delete(f"/api/v1/pen-names/{pid}")
    assert r.status_code == 200

    items = (await client.get("/api/v1/pen-names")).json()
    assert len(items) == 1
    assert items[0]["id"] == r1.json()["id"]


@pytest.mark.asyncio
async def test_books_and_analytics_endpoints(client):
    r = await client.post("/api/v1/pen-names", json={"display_name": "Solo"})
    pid = r.json()["id"]

    r = await client.get(f"/api/v1/pen-names/{pid}/books")
    assert r.status_code == 200
    assert r.json() == {"books": []}

    r = await client.get(f"/api/v1/pen-names/{pid}/analytics?period=30d")
    assert r.status_code == 200
    body = r.json()
    assert body["period"] == "30d"
    assert body["books_count"] == 0
    assert body["revenue"] == 0.0
