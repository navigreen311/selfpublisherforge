"""Unit tests for UserService business logic.

These tests mock the database layer to validate pure service logic such as
role validation, permission checks, and error handling.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.core.exceptions import AppException
from app.modules.users.service import UserService, _generate_api_key, _role_level

# ─── Helper Fixtures ──────────────────────────────────────────────────────────

def _make_user(role: str = "owner", org_id: UUID | None = None) -> dict:
    return {
        "user_id": uuid4(),
        "org_id": org_id or uuid4(),
        "role": role,
    }


def _make_mapping_result(rows: list[dict]):
    """Create a mock that behaves like SQLAlchemy result.mappings()."""
    mock_result = MagicMock()
    mapping_mock = MagicMock()
    mapping_mock.first.return_value = rows[0] if rows else None
    mapping_mock.all.return_value = rows
    mock_result.mappings.return_value = mapping_mock
    mock_result.rowcount = len(rows)
    # Also support ORM-style scalar_one_or_none (returns the first row as
    # an object with attributes, or None)
    if rows:
        user_mock = MagicMock()
        for k, v in rows[0].items():
            setattr(user_mock, k, v)
        mock_result.scalar_one_or_none.return_value = user_mock
    else:
        mock_result.scalar_one_or_none.return_value = None
    return mock_result


# ─── Role Hierarchy Tests ─────────────────────────────────────────────────────

class TestRoleHierarchy:
    def test_owner_is_highest(self):
        assert _role_level("owner") > _role_level("admin")

    def test_admin_above_editor(self):
        assert _role_level("admin") > _role_level("editor")

    def test_editor_above_writer(self):
        assert _role_level("editor") > _role_level("writer")

    def test_writer_above_viewer(self):
        assert _role_level("writer") > _role_level("viewer")

    def test_unknown_role_returns_zero(self):
        assert _role_level("unknown") == 0


# ─── API Key Generation ──────────────────────────────────────────────────────

class TestApiKeyGeneration:
    def test_generate_api_key_returns_tuple(self):
        key, prefix = _generate_api_key()
        assert isinstance(key, str)
        assert isinstance(prefix, str)
        assert len(prefix) == 8
        assert key.startswith(prefix)

    def test_generate_api_key_unique(self):
        keys = {_generate_api_key()[0] for _ in range(100)}
        assert len(keys) == 100


# ─── User Profile ─────────────────────────────────────────────────────────────

class TestGetUserProfile:
    @pytest.mark.asyncio
    async def test_user_not_found_raises_404(self):
        db = AsyncMock()
        db.execute.return_value = _make_mapping_result([])

        with pytest.raises(AppException) as exc_info:
            await UserService.get_user_profile(db, uuid4())

        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "USER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_returns_user_dict(self):
        user_id = uuid4()
        org_id = uuid4()
        now = datetime.now(UTC)
        row = {
            "id": user_id,
            "email": "test@example.com",
            "name": "Test User",
            "role": "editor",
            "org_id": org_id,
            "preferences": {},
            "avatar_url": None,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
        }
        db = AsyncMock()
        db.execute.return_value = _make_mapping_result([row])

        result = await UserService.get_user_profile(db, user_id)
        assert result["id"] == user_id
        assert result["email"] == "test@example.com"


class TestUpdateUserProfile:
    @pytest.mark.asyncio
    async def test_no_fields_raises_400(self):
        db = AsyncMock()
        with pytest.raises(AppException) as exc_info:
            await UserService.update_user_profile(db, uuid4(), {})
        assert exc_info.value.status_code == 400
        assert exc_info.value.code == "NO_FIELDS"

    @pytest.mark.asyncio
    async def test_none_values_filtered_out(self):
        db = AsyncMock()
        with pytest.raises(AppException) as exc_info:
            await UserService.update_user_profile(
                db, uuid4(), {"name": None, "avatar_url": None}
            )
        assert exc_info.value.status_code == 400


# ─── Organization Updates ─────────────────────────────────────────────────────

class TestUpdateOrg:
    @pytest.mark.asyncio
    async def test_viewer_cannot_update_org(self):
        db = AsyncMock()
        user = _make_user(role="viewer")
        with pytest.raises(AppException) as exc_info:
            await UserService.update_org(db, user["org_id"], {"name": "New"}, user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_update_org(self):
        org_id = uuid4()
        user = _make_user(role="admin", org_id=org_id)
        now = datetime.now(UTC)
        org_row = {
            "id": org_id,
            "name": "Updated",
            "slug": "updated",
            "plan_tier": "free",
            "logo_url": None,
            "max_members": 5,
            "created_at": now,
            "updated_at": now,
            "deleted_at": None,
        }
        db = AsyncMock()
        db.execute.return_value = _make_mapping_result([org_row])
        db.flush = AsyncMock()

        result = await UserService.update_org(
            db, org_id, {"name": "Updated"}, user
        )
        assert result["name"] == "Updated"

    @pytest.mark.asyncio
    async def test_no_fields_raises_400(self):
        db = AsyncMock()
        user = _make_user(role="owner")
        with pytest.raises(AppException) as exc_info:
            await UserService.update_org(db, user["org_id"], {}, user)
        assert exc_info.value.status_code == 400


# ─── Invite Logic ─────────────────────────────────────────────────────────────

class TestInviteMember:
    @pytest.mark.asyncio
    async def test_viewer_cannot_invite(self):
        db = AsyncMock()
        user = _make_user(role="viewer")
        with pytest.raises(AppException) as exc_info:
            await UserService.invite_member(
                db, user["org_id"], "new@example.com", "viewer", user
            )
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_cannot_invite_equal_role(self):
        db = AsyncMock()
        user = _make_user(role="admin")
        with pytest.raises(AppException) as exc_info:
            await UserService.invite_member(
                db, user["org_id"], "new@example.com", "admin", user
            )
        assert exc_info.value.status_code == 403
        assert exc_info.value.code == "ROLE_ESCALATION"

    @pytest.mark.asyncio
    async def test_cannot_invite_higher_role(self):
        db = AsyncMock()
        user = _make_user(role="admin")
        with pytest.raises(AppException) as exc_info:
            await UserService.invite_member(
                db, user["org_id"], "new@example.com", "owner", user
            )
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_duplicate_invite_raises_409(self):
        db = AsyncMock()
        user = _make_user(role="owner")
        # First execute checks for existing invite — return a row
        db.execute.return_value = _make_mapping_result([{"id": uuid4()}])

        with pytest.raises(AppException) as exc_info:
            await UserService.invite_member(
                db, user["org_id"], "dup@example.com", "viewer", user
            )
        assert exc_info.value.status_code == 409
        assert exc_info.value.code == "INVITE_EXISTS"


# ─── Role Change ──────────────────────────────────────────────────────────────

class TestChangeRole:
    @pytest.mark.asyncio
    async def test_non_owner_cannot_change_role(self):
        db = AsyncMock()
        user = _make_user(role="admin")
        with pytest.raises(AppException) as exc_info:
            await UserService.change_member_role(
                db, user["org_id"], uuid4(), "editor", user
            )
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_cannot_change_own_role(self):
        db = AsyncMock()
        user = _make_user(role="owner")
        with pytest.raises(AppException) as exc_info:
            await UserService.change_member_role(
                db, user["org_id"], user["user_id"], "admin", user
            )
        assert exc_info.value.status_code == 400
        assert exc_info.value.code == "SELF_ROLE_CHANGE"

    @pytest.mark.asyncio
    async def test_member_not_found(self):
        db = AsyncMock()
        user = _make_user(role="owner")
        result_mock = MagicMock()
        result_mock.rowcount = 0
        db.execute.return_value = result_mock
        db.flush = AsyncMock()

        with pytest.raises(AppException) as exc_info:
            await UserService.change_member_role(
                db, user["org_id"], uuid4(), "editor", user
            )
        assert exc_info.value.status_code == 404


# ─── Remove Member ────────────────────────────────────────────────────────────

class TestRemoveMember:
    @pytest.mark.asyncio
    async def test_viewer_cannot_remove(self):
        db = AsyncMock()
        user = _make_user(role="viewer")
        with pytest.raises(AppException) as exc_info:
            await UserService.remove_member(db, user["org_id"], uuid4(), user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_cannot_remove_self(self):
        db = AsyncMock()
        user = _make_user(role="owner")
        with pytest.raises(AppException) as exc_info:
            await UserService.remove_member(
                db, user["org_id"], user["user_id"], user
            )
        assert exc_info.value.status_code == 400
        assert exc_info.value.code == "SELF_REMOVE"

    @pytest.mark.asyncio
    async def test_cannot_remove_higher_role(self):
        db = AsyncMock()
        user = _make_user(role="admin")
        target_id = uuid4()
        # First execute: get target's role
        db.execute.return_value = _make_mapping_result([{"role": "owner"}])

        with pytest.raises(AppException) as exc_info:
            await UserService.remove_member(
                db, user["org_id"], target_id, user
            )
        assert exc_info.value.status_code == 403
        assert exc_info.value.code == "ROLE_ESCALATION"


# ─── API Keys ─────────────────────────────────────────────────────────────────

class TestApiKeys:
    @pytest.mark.asyncio
    async def test_viewer_cannot_create_key(self):
        db = AsyncMock()
        user = _make_user(role="viewer")
        with pytest.raises(AppException) as exc_info:
            await UserService.create_api_key(
                db, user["org_id"], {"name": "test"}, user
            )
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_viewer_cannot_revoke_key(self):
        db = AsyncMock()
        user = _make_user(role="viewer")
        with pytest.raises(AppException) as exc_info:
            await UserService.revoke_api_key(db, user["org_id"], uuid4(), user)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_key(self):
        db = AsyncMock()
        user = _make_user(role="admin")
        result_mock = MagicMock()
        result_mock.rowcount = 0
        db.execute.return_value = result_mock

        with pytest.raises(AppException) as exc_info:
            await UserService.revoke_api_key(db, user["org_id"], uuid4(), user)
        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "API_KEY_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_create_key_returns_full_key(self):
        db = AsyncMock()
        db.flush = AsyncMock()
        user = _make_user(role="admin")

        result = await UserService.create_api_key(
            db,
            user["org_id"],
            {"name": "My Key", "scopes": ["read", "write"]},
            user,
        )
        assert "key" in result
        assert len(result["key"]) > 8
        assert result["name"] == "My Key"
        assert result["scopes"] == ["read", "write"]
        assert result["is_active"] is True


# ─── Session Revocation ───────────────────────────────────────────────────────

class TestSessionRevocation:
    @pytest.mark.asyncio
    async def test_revoke_nonexistent_session(self):
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.rowcount = 0
        db.execute.return_value = result_mock

        with pytest.raises(AppException) as exc_info:
            await UserService.revoke_session(db, uuid4(), uuid4())
        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "SESSION_NOT_FOUND"
