"""Integration tests for User & Organization API endpoints.

Tests the full HTTP request/response cycle through FastAPI's TestClient,
mocking only the database session and authentication dependencies.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.users.router import router
from app.database import get_db
from app.core.dependencies import get_current_user, require_role


# ─── Fixtures ─────────────────────────────────────────────────────────────────

_OWNER_ID = uuid4()
_ORG_ID = uuid4()
_ADMIN_ID = uuid4()
_VIEWER_ID = uuid4()


def _owner_user():
    return {"user_id": _OWNER_ID, "org_id": _ORG_ID, "role": "owner"}


def _admin_user():
    return {"user_id": _ADMIN_ID, "org_id": _ORG_ID, "role": "admin"}


def _viewer_user():
    return {"user_id": _VIEWER_ID, "org_id": _ORG_ID, "role": "viewer"}


def _make_mapping_result(rows: list[dict]):
    mock_result = MagicMock()
    mapping_mock = MagicMock()
    mapping_mock.first.return_value = rows[0] if rows else None
    mapping_mock.all.return_value = rows
    mock_result.mappings.return_value = mapping_mock
    mock_result.rowcount = len(rows)
    return mock_result


def _create_app(user_factory=None) -> tuple[FastAPI, AsyncMock]:
    """Build a test app with mocked dependencies."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    mock_db = AsyncMock()
    mock_db.flush = AsyncMock()

    async def override_get_db():
        yield mock_db

    user = (user_factory or _owner_user)()

    async def override_get_current_user():
        return user

    def override_require_role(*roles):
        async def checker():
            if user["role"] not in roles:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions",
                )
            return user
        return checker

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    # Patch require_role for each specific set of roles used
    for role_set in [("owner",), ("owner", "admin")]:
        app.dependency_overrides[require_role(*role_set)] = override_require_role(*role_set)

    return app, mock_db


# ─── User Profile Endpoints ──────────────────────────────────────────────────

class TestGetUserProfile:
    def test_get_me_success(self):
        app, mock_db = _create_app()
        now = datetime.now(timezone.utc)
        mock_db.execute.return_value = _make_mapping_result([{
            "id": _OWNER_ID,
            "email": "owner@example.com",
            "name": "Owner",
            "role": "owner",
            "org_id": _ORG_ID,
            "preferences": {},
            "avatar_url": None,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
        }])

        client = TestClient(app)
        resp = client.get("/api/v1/users/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "owner@example.com"
        assert data["role"] == "owner"

    def test_get_me_not_found(self):
        app, mock_db = _create_app()
        mock_db.execute.return_value = _make_mapping_result([])

        client = TestClient(app)
        resp = client.get("/api/v1/users/me")
        assert resp.status_code == 404


class TestUpdateUserProfile:
    def test_update_name(self):
        app, mock_db = _create_app()
        now = datetime.now(timezone.utc)
        row = {
            "id": _OWNER_ID,
            "email": "owner@example.com",
            "name": "New Name",
            "role": "owner",
            "org_id": _ORG_ID,
            "preferences": {},
            "avatar_url": None,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
        }
        mock_db.execute.return_value = _make_mapping_result([row])

        client = TestClient(app)
        resp = client.patch("/api/v1/users/me", json={"name": "New Name"})
        assert resp.status_code == 200

    def test_update_empty_body_returns_400(self):
        app, mock_db = _create_app()
        # The service will raise 400 when all fields are None
        from app.core.exceptions import AppException
        mock_db.execute.side_effect = AppException(400, "NO_FIELDS", "No fields to update")

        client = TestClient(app)
        resp = client.patch("/api/v1/users/me", json={})
        # With empty body all fields default to None; service raises 400
        assert resp.status_code in (400, 422)


# ─── Organization Endpoints ──────────────────────────────────────────────────

class TestOrgEndpoints:
    def test_get_org_success(self):
        app, mock_db = _create_app()
        now = datetime.now(timezone.utc)
        mock_db.execute.return_value = _make_mapping_result([{
            "id": _ORG_ID,
            "name": "My Org",
            "slug": "my-org",
            "plan_tier": "free",
            "logo_url": None,
            "max_members": 5,
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
        }])

        client = TestClient(app)
        resp = client.get(f"/api/v1/orgs/{_ORG_ID}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "My Org"

    def test_get_org_wrong_org_returns_403(self):
        app, mock_db = _create_app()
        client = TestClient(app)
        wrong_org = uuid4()
        resp = client.get(f"/api/v1/orgs/{wrong_org}")
        assert resp.status_code == 403

    def test_list_members(self):
        app, mock_db = _create_app()
        now = datetime.now(timezone.utc)
        mock_db.execute.return_value = _make_mapping_result([{
            "user_id": _OWNER_ID,
            "email": "owner@example.com",
            "name": "Owner",
            "role": "owner",
            "joined_at": now,
        }])

        client = TestClient(app)
        resp = client.get(f"/api/v1/orgs/{_ORG_ID}/members")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


# ─── Session Endpoints ───────────────────────────────────────────────────────

class TestSessionEndpoints:
    def test_list_sessions(self):
        app, mock_db = _create_app()
        now = datetime.now(timezone.utc)
        mock_db.execute.return_value = _make_mapping_result([{
            "id": uuid4(),
            "ip_address": "127.0.0.1",
            "user_agent": "TestAgent",
            "created_at": now,
            "last_active_at": now,
        }])

        client = TestClient(app)
        resp = client.get("/api/v1/users/me/sessions")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_revoke_session_not_found(self):
        app, mock_db = _create_app()
        result_mock = MagicMock()
        result_mock.rowcount = 0
        mock_db.execute.return_value = result_mock

        client = TestClient(app)
        resp = client.delete(f"/api/v1/users/me/sessions/{uuid4()}")
        assert resp.status_code == 404


# ─── API Key Endpoints ───────────────────────────────────────────────────────

class TestApiKeyEndpoints:
    def test_list_api_keys(self):
        app, mock_db = _create_app()
        now = datetime.now(timezone.utc)
        mock_db.execute.return_value = _make_mapping_result([{
            "id": uuid4(),
            "name": "Test Key",
            "prefix": "abc12345",
            "scopes": ["read"],
            "created_at": now,
            "expires_at": None,
            "last_used_at": None,
            "is_active": True,
        }])

        client = TestClient(app)
        resp = client.get(f"/api/v1/orgs/{_ORG_ID}/api-keys")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_create_api_key(self):
        app, mock_db = _create_app()
        mock_db.execute.return_value = MagicMock(rowcount=1)

        client = TestClient(app)
        resp = client.post(
            f"/api/v1/orgs/{_ORG_ID}/api-keys",
            json={"name": "CI Key", "scopes": ["read", "write"]},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "key" in data
        assert data["name"] == "CI Key"

    def test_revoke_api_key_not_found(self):
        app, mock_db = _create_app()
        result_mock = MagicMock()
        result_mock.rowcount = 0
        mock_db.execute.return_value = result_mock

        client = TestClient(app)
        resp = client.delete(f"/api/v1/orgs/{_ORG_ID}/api-keys/{uuid4()}")
        assert resp.status_code == 404
