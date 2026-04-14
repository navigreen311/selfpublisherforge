"""Tests for Team / Roles / Permissions (Final Gaps Stream 1).

See docstring in ``test_pen_names.py`` for why we use raw DDL rather than
``Base.metadata.create_all``.
"""
from __future__ import annotations

import json
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import create_app
from app.modules.team.permissions import load_effective_permissions

from tests.test_pen_names import SCHEMA_SQL


TEST_ORG_ID = uuid.UUID("00000000-0000-0000-0000-00000000aaaa")
OWNER_USER_ID = uuid.UUID("00000000-0000-0000-0000-00000000bbbb")
VIEWER_USER_ID = uuid.UUID("00000000-0000-0000-0000-00000000cccc")


async def _seed(session):
    await session.execute(
        sa_text(
            "INSERT INTO organizations (id, name, slug, plan) "
            "VALUES (:id, 'Test', 'test', 'free')"
        ),
        {"id": str(TEST_ORG_ID)},
    )
    await session.execute(
        sa_text(
            "INSERT INTO users (id, org_id, email, password_hash, name, role) "
            "VALUES (:id, :oid, 'o@t.co', 'x', 'Owner', 'owner')"
        ),
        {"id": str(OWNER_USER_ID), "oid": str(TEST_ORG_ID)},
    )
    await session.execute(
        sa_text(
            "INSERT INTO users (id, org_id, email, password_hash, name, role) "
            "VALUES (:id, :oid, 'v@t.co', 'x', 'Viewer', 'viewer')"
        ),
        {"id": str(VIEWER_USER_ID), "oid": str(TEST_ORG_ID)},
    )
    owner_role_id = uuid.uuid4()
    viewer_role_id = uuid.uuid4()
    owner_perms = {
        "team": {"view": True, "create": True, "edit": True, "delete": True, "publish": False},
        "pen_names": {"view": True, "create": True, "edit": True, "delete": True, "publish": False},
        "billing": {"view": True, "create": True, "edit": True, "delete": False, "publish": False},
        "publishing": {"view": True, "create": True, "edit": True, "delete": False, "publish": True},
    }
    viewer_perms = {
        "team": {"view": True, "create": False, "edit": False, "delete": False, "publish": False},
        "pen_names": {"view": True, "create": False, "edit": False, "delete": False, "publish": False},
        "billing": {"view": False, "create": False, "edit": False, "delete": False, "publish": False},
        "publishing": {"view": True, "create": False, "edit": False, "delete": False, "publish": False},
    }
    await session.execute(
        sa_text(
            "INSERT INTO roles (id, org_id, name, description, permissions, is_system) "
            "VALUES (:id, :oid, 'Owner', 'owner', :p, 1)"
        ),
        {"id": str(owner_role_id), "oid": str(TEST_ORG_ID),
         "p": json.dumps(owner_perms)},
    )
    await session.execute(
        sa_text(
            "INSERT INTO roles (id, org_id, name, description, permissions, is_system) "
            "VALUES (:id, :oid, 'Viewer', 'read only', :p, 1)"
        ),
        {"id": str(viewer_role_id), "oid": str(TEST_ORG_ID),
         "p": json.dumps(viewer_perms)},
    )
    await session.execute(
        sa_text("UPDATE users SET role_id = :rid WHERE id = :uid"),
        {"rid": str(owner_role_id), "uid": str(OWNER_USER_ID)},
    )
    await session.execute(
        sa_text("UPDATE users SET role_id = :rid WHERE id = :uid"),
        {"rid": str(viewer_role_id), "uid": str(VIEWER_USER_ID)},
    )
    await session.commit()
    return owner_role_id, viewer_role_id


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
        await _seed(session)
        yield session


def _client(db_session, user_id, role_name):
    async def _override_get_db():
        yield db_session
        try:
            await db_session.commit()
        except Exception:
            await db_session.rollback()

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": user_id,
        "org_id": TEST_ORG_ID,
        "role": role_name,
    }
    transport = ASGITransport(app=app)
    return app, AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_load_effective_permissions_uses_role_id(db_session):
    perms = await load_effective_permissions(
        db_session, VIEWER_USER_ID, TEST_ORG_ID, legacy_role="viewer"
    )
    assert perms["team"]["view"] is True
    assert perms["team"]["create"] is False


@pytest.mark.asyncio
async def test_viewer_cannot_create_pen_name(db_session):
    app, client = _client(db_session, VIEWER_USER_ID, "viewer")
    async with client as ac:
        r = await ac.post(
            "/api/v1/pen-names",
            json={"display_name": "Blocked"},
        )
        assert r.status_code == 403
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_owner_can_create_pen_name(db_session):
    app, client = _client(db_session, OWNER_USER_ID, "owner")
    async with client as ac:
        r = await ac.post(
            "/api/v1/pen-names",
            json={"display_name": "Allowed"},
        )
        assert r.status_code == 201, r.text
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_roles(db_session):
    app, client = _client(db_session, OWNER_USER_ID, "owner")
    async with client as ac:
        r = await ac.get("/api/v1/roles")
        assert r.status_code == 200
        items = r.json()
        assert {i["name"] for i in items} == {"Owner", "Viewer"}
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_viewer_cannot_invite_teammate(db_session):
    row = await db_session.execute(
        sa_text("SELECT id FROM roles WHERE name = 'Viewer'")
    )
    viewer_role_id = row.scalar()

    app, client = _client(db_session, VIEWER_USER_ID, "viewer")
    async with client as ac:
        r = await ac.post(
            "/api/v1/team/invite",
            json={"email": "newbie@test.com", "role_id": str(viewer_role_id)},
        )
        assert r.status_code == 403
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_owner_can_invite_teammate(db_session):
    row = await db_session.execute(
        sa_text("SELECT id FROM roles WHERE name = 'Viewer'")
    )
    viewer_role_id = row.scalar()

    app, client = _client(db_session, OWNER_USER_ID, "owner")
    async with client as ac:
        r = await ac.post(
            "/api/v1/team/invite",
            json={"email": "new@test.com", "role_id": str(viewer_role_id)},
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["email"] == "new@test.com"
        assert body["status"] == "pending"
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_custom_role(db_session):
    app, client = _client(db_session, OWNER_USER_ID, "owner")
    async with client as ac:
        r = await ac.post(
            "/api/v1/roles",
            json={
                "name": "Cookbook Editor",
                "description": "Edits cookbook content",
                "permissions": {
                    "cookbooks": {
                        "view": True, "create": True, "edit": True,
                        "delete": False, "publish": False,
                    },
                },
            },
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["name"] == "Cookbook Editor"
        assert body["is_system"] is False
        assert body["permissions"]["cookbooks"]["edit"] is True
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_cannot_modify_system_role(db_session):
    row = await db_session.execute(
        sa_text("SELECT id FROM roles WHERE name = 'Owner'")
    )
    owner_role_id = row.scalar()

    app, client = _client(db_session, OWNER_USER_ID, "owner")
    async with client as ac:
        r = await ac.patch(
            f"/api/v1/roles/{owner_role_id}",
            json={"name": "Hacked"},
        )
        assert r.status_code == 400
    app.dependency_overrides.clear()
