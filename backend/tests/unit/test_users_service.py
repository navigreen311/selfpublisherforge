"""Unit tests for the users service layer.

Tests cover user profile management, organization operations, member management,
invitation flow, role changes, session management, and API key operations.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.core.exceptions import AppException
from app.core.security import hash_password
from app.models.user import User
from app.modules.users.service import UserService, _generate_api_key, _role_level

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _seed_user_and_org(db, email="user@test.com", role="owner", org_name="TestOrg"):
    """Create an organization and a user, return both."""
    from app.models.user import Organization

    org_id = uuid4()
    org = Organization(
        id=org_id,
        name=org_name,
        slug=f"{org_name.lower()}-{str(org_id)[:8]}",
    )
    db.add(org)

    user_id = uuid4()
    user = User(
        id=user_id,
        org_id=org_id,
        email=email,
        name="Test User",
        password_hash=hash_password("StrongP@ss1"),
        role=role,
        email_verified=True,
    )
    db.add(user)
    await db.flush()
    return org, user


async def _seed_session(db, user_id):
    """Create a user session."""
    from sqlalchemy import text as sa_text
    session_id = uuid4()
    await db.execute(
        sa_text(
            "INSERT INTO user_sessions (id, user_id, token_hash, ip_address, user_agent, created_at, last_active_at) "
            "VALUES (:sid, :uid, :th, :ip, :ua, :created, :active)"
        ),
        {
            "sid": session_id,
            "uid": user_id,
            "th": "dummyhash",
            "ip": "127.0.0.1",
            "ua": "TestAgent/1.0",
            "created": datetime.now(UTC),
            "active": datetime.now(UTC),
        },
    )
    await db.flush()
    return session_id


# ---------------------------------------------------------------------------
# User Profile tests
# ---------------------------------------------------------------------------

class TestUserProfile:

    @pytest.mark.asyncio
    async def test_get_user_profile_success(self, db_session):
        _, user = await _seed_user_and_org(db_session)
        profile = await UserService.get_user_profile(db_session, user.id)
        assert profile["email"] == user.email
        assert profile["name"] == user.name
        assert profile["role"] == user.role

    @pytest.mark.asyncio
    async def test_get_user_profile_not_found(self, db_session):
        with pytest.raises(AppException) as exc_info:
            await UserService.get_user_profile(db_session, uuid4())
        assert exc_info.value.code == "USER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_update_user_profile_success(self, db_session):
        _, user = await _seed_user_and_org(db_session, email="old@test.com")
        updated = await UserService.update_user_profile(
            db_session,
            user.id,
            {"name": "New Name", "email": "new@test.com"},
        )
        assert updated["name"] == "New Name"
        assert updated["email"] == "new@test.com"

    @pytest.mark.asyncio
    async def test_update_user_profile_no_fields(self, db_session):
        _, user = await _seed_user_and_org(db_session)
        with pytest.raises(AppException) as exc_info:
            await UserService.update_user_profile(db_session, user.id, {})
        assert exc_info.value.code == "NO_FIELDS"

    @pytest.mark.asyncio
    async def test_update_preferences_success(self, db_session):
        _, user = await _seed_user_and_org(db_session)
        updated = await UserService.update_preferences(
            db_session,
            user.id,
            {"theme": "dark", "notifications": True},
        )
        # Preferences should be merged
        from sqlalchemy import select
        result = await db_session.execute(select(User).where(User.id == user.id))
        u = result.scalar_one()
        assert u.preferences["theme"] == "dark"
        assert u.preferences["notifications"] is True


# ---------------------------------------------------------------------------
# Session Management tests
# ---------------------------------------------------------------------------

class TestSessionManagement:

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, db_session):
        _, user = await _seed_user_and_org(db_session)
        sessions = await UserService.list_sessions(db_session, user.id)
        assert sessions == []

    @pytest.mark.asyncio
    async def test_list_sessions_with_data(self, db_session):
        _, user = await _seed_user_and_org(db_session)
        await _seed_session(db_session, user.id)
        sessions = await UserService.list_sessions(db_session, user.id)
        assert len(sessions) == 1
        assert sessions[0]["user_agent"] == "TestAgent/1.0"

    @pytest.mark.asyncio
    async def test_revoke_session_success(self, db_session):
        _, user = await _seed_user_and_org(db_session)
        session_id = await _seed_session(db_session, user.id)
        await UserService.revoke_session(db_session, user.id, session_id)
        # Session should no longer appear in active sessions
        sessions = await UserService.list_sessions(db_session, user.id)
        assert len(sessions) == 0

    @pytest.mark.asyncio
    async def test_revoke_session_not_found(self, db_session):
        _, user = await _seed_user_and_org(db_session)
        with pytest.raises(AppException) as exc_info:
            await UserService.revoke_session(db_session, user.id, uuid4())
        assert exc_info.value.code == "SESSION_NOT_FOUND"


# ---------------------------------------------------------------------------
# Organization tests
# ---------------------------------------------------------------------------

class TestOrganization:

    @pytest.mark.asyncio
    async def test_get_org_success(self, db_session):
        org, _ = await _seed_user_and_org(db_session, org_name="MyOrg")
        result = await UserService.get_org(db_session, org.id)
        assert result["name"] == "MyOrg"

    @pytest.mark.asyncio
    async def test_get_org_not_found(self, db_session):
        with pytest.raises(AppException) as exc_info:
            await UserService.get_org(db_session, uuid4())
        assert exc_info.value.code == "ORG_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_update_org_owner_success(self, db_session):
        org, user = await _seed_user_and_org(db_session, role="owner")
        current_user = {"user_id": user.id, "role": "owner"}
        updated = await UserService.update_org(
            db_session,
            org.id,
            {"name": "Updated Org"},
            current_user,
        )
        assert updated["name"] == "Updated Org"

    @pytest.mark.asyncio
    async def test_update_org_admin_success(self, db_session):
        org, user = await _seed_user_and_org(db_session, role="admin")
        current_user = {"user_id": user.id, "role": "admin"}
        updated = await UserService.update_org(
            db_session,
            org.id,
            {"name": "Admin Updated"},
            current_user,
        )
        assert updated["name"] == "Admin Updated"

    @pytest.mark.asyncio
    async def test_update_org_forbidden(self, db_session):
        org, user = await _seed_user_and_org(db_session, role="editor")
        current_user = {"user_id": user.id, "role": "editor"}
        with pytest.raises(AppException) as exc_info:
            await UserService.update_org(
                db_session,
                org.id,
                {"name": "Should Fail"},
                current_user,
            )
        assert exc_info.value.code == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_update_org_no_fields(self, db_session):
        org, user = await _seed_user_and_org(db_session, role="owner")
        current_user = {"user_id": user.id, "role": "owner"}
        with pytest.raises(AppException) as exc_info:
            await UserService.update_org(db_session, org.id, {}, current_user)
        assert exc_info.value.code == "NO_FIELDS"


# ---------------------------------------------------------------------------
# Member Management tests
# ---------------------------------------------------------------------------

class TestMemberManagement:

    @pytest.mark.asyncio
    async def test_list_members(self, db_session):
        org, user = await _seed_user_and_org(db_session)
        members = await UserService.list_members(db_session, org.id)
        assert len(members) == 1
        assert members[0]["email"] == user.email

    @pytest.mark.asyncio
    async def test_invite_member_success(self, db_session):
        org, user = await _seed_user_and_org(db_session, role="owner")
        inviter = {"user_id": user.id, "role": "owner"}
        invite = await UserService.invite_member(
            db_session,
            org.id,
            "newuser@test.com",
            "editor",
            inviter,
        )
        assert invite["email"] == "newuser@test.com"
        assert invite["role"] == "editor"
        assert invite["id"] is not None

    @pytest.mark.asyncio
    async def test_invite_member_forbidden(self, db_session):
        org, user = await _seed_user_and_org(db_session, role="viewer")
        inviter = {"user_id": user.id, "role": "viewer"}
        with pytest.raises(AppException) as exc_info:
            await UserService.invite_member(
                db_session,
                org.id,
                "fail@test.com",
                "editor",
                inviter,
            )
        assert exc_info.value.code == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_invite_member_role_escalation(self, db_session):
        org, user = await _seed_user_and_org(db_session, role="admin")
        inviter = {"user_id": user.id, "role": "admin"}
        with pytest.raises(AppException) as exc_info:
            await UserService.invite_member(
                db_session,
                org.id,
                "escalate@test.com",
                "owner",
                inviter,
            )
        assert exc_info.value.code == "ROLE_ESCALATION"

    @pytest.mark.asyncio
    async def test_invite_member_duplicate(self, db_session):
        org, user = await _seed_user_and_org(db_session, role="owner")
        inviter = {"user_id": user.id, "role": "owner"}
        await UserService.invite_member(
            db_session,
            org.id,
            "dup@test.com",
            "editor",
            inviter,
        )
        with pytest.raises(AppException) as exc_info:
            await UserService.invite_member(
                db_session,
                org.id,
                "dup@test.com",
                "editor",
                inviter,
            )
        assert exc_info.value.code == "INVITE_EXISTS"

    @pytest.mark.asyncio
    async def test_change_member_role_success(self, db_session):
        org, owner = await _seed_user_and_org(db_session, email="owner@test.com", role="owner")
        # Add another member
        member_id = uuid4()
        member = User(
            id=member_id,
            org_id=org.id,
            email="member@test.com",
            name="Member",
            password_hash=hash_password("Pass1234"),
            role="viewer",
        )
        db_session.add(member)
        await db_session.flush()

        current_user = {"user_id": owner.id, "role": "owner"}
        result = await UserService.change_member_role(
            db_session,
            org.id,
            member_id,
            "editor",
            current_user,
        )
        assert result["role"] == "editor"

    @pytest.mark.asyncio
    async def test_change_member_role_forbidden(self, db_session):
        org, admin = await _seed_user_and_org(db_session, email="admin@test.com", role="admin")
        current_user = {"user_id": admin.id, "role": "admin"}
        with pytest.raises(AppException) as exc_info:
            await UserService.change_member_role(
                db_session,
                org.id,
                uuid4(),
                "editor",
                current_user,
            )
        assert exc_info.value.code == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_change_member_role_self(self, db_session):
        org, owner = await _seed_user_and_org(db_session, role="owner")
        current_user = {"user_id": owner.id, "role": "owner"}
        with pytest.raises(AppException) as exc_info:
            await UserService.change_member_role(
                db_session,
                org.id,
                owner.id,
                "admin",
                current_user,
            )
        assert exc_info.value.code == "SELF_ROLE_CHANGE"

    @pytest.mark.asyncio
    async def test_change_member_role_not_found(self, db_session):
        org, owner = await _seed_user_and_org(db_session, role="owner")
        current_user = {"user_id": owner.id, "role": "owner"}
        with pytest.raises(AppException) as exc_info:
            await UserService.change_member_role(
                db_session,
                org.id,
                uuid4(),
                "editor",
                current_user,
            )
        assert exc_info.value.code == "MEMBER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_remove_member_success(self, db_session):
        org, owner = await _seed_user_and_org(db_session, email="owner@test.com", role="owner")
        # Add another member
        member_id = uuid4()
        member = User(
            id=member_id,
            org_id=org.id,
            email="toremove@test.com",
            name="ToRemove",
            password_hash=hash_password("Pass1234"),
            role="viewer",
        )
        db_session.add(member)
        await db_session.flush()

        current_user = {"user_id": owner.id, "role": "owner"}
        await UserService.remove_member(db_session, org.id, member_id, current_user)

        # Member should be soft-deleted
        from sqlalchemy import select
        result = await db_session.execute(
            select(User).where(User.id == member_id, User.deleted_at.is_(None))
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_remove_member_forbidden(self, db_session):
        org, editor = await _seed_user_and_org(db_session, role="editor")
        current_user = {"user_id": editor.id, "role": "editor"}
        with pytest.raises(AppException) as exc_info:
            await UserService.remove_member(db_session, org.id, uuid4(), current_user)
        assert exc_info.value.code == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_remove_member_self(self, db_session):
        org, owner = await _seed_user_and_org(db_session, role="owner")
        current_user = {"user_id": owner.id, "role": "owner"}
        with pytest.raises(AppException) as exc_info:
            await UserService.remove_member(db_session, org.id, owner.id, current_user)
        assert exc_info.value.code == "SELF_REMOVE"

    @pytest.mark.asyncio
    async def test_remove_member_role_escalation(self, db_session):
        org, admin = await _seed_user_and_org(db_session, email="admin@test.com", role="admin")
        # Add an owner
        owner_id = uuid4()
        owner = User(
            id=owner_id,
            org_id=org.id,
            email="owner@test.com",
            name="Owner",
            password_hash=hash_password("Pass1234"),
            role="owner",
        )
        db_session.add(owner)
        await db_session.flush()

        current_user = {"user_id": admin.id, "role": "admin"}
        with pytest.raises(AppException) as exc_info:
            await UserService.remove_member(db_session, org.id, owner_id, current_user)
        assert exc_info.value.code == "ROLE_ESCALATION"

    @pytest.mark.asyncio
    async def test_remove_member_not_found(self, db_session):
        org, owner = await _seed_user_and_org(db_session, role="owner")
        current_user = {"user_id": owner.id, "role": "owner"}
        with pytest.raises(AppException) as exc_info:
            await UserService.remove_member(db_session, org.id, uuid4(), current_user)
        assert exc_info.value.code == "MEMBER_NOT_FOUND"


# ---------------------------------------------------------------------------
# API Key tests
# ---------------------------------------------------------------------------

class TestAPIKeys:

    @pytest.mark.asyncio
    async def test_create_api_key_success(self, db_session):
        org, user = await _seed_user_and_org(db_session, role="owner")
        current_user = {"user_id": user.id, "role": "owner"}
        key_data = await UserService.create_api_key(
            db_session,
            org.id,
            {"name": "Test Key", "scopes": ["read", "write"]},
            current_user,
        )
        assert key_data["name"] == "Test Key"
        assert key_data["scopes"] == ["read", "write"]
        assert key_data["key"] is not None  # Raw key returned once
        assert key_data["prefix"] is not None

    @pytest.mark.asyncio
    async def test_create_api_key_with_expiry(self, db_session):
        org, user = await _seed_user_and_org(db_session, role="admin")
        current_user = {"user_id": user.id, "role": "admin"}
        key_data = await UserService.create_api_key(
            db_session,
            org.id,
            {"name": "Expiring Key", "expires_in_days": 30},
            current_user,
        )
        assert key_data["expires_at"] is not None
        assert key_data["expires_at"] > datetime.now(UTC)

    @pytest.mark.asyncio
    async def test_create_api_key_forbidden(self, db_session):
        org, user = await _seed_user_and_org(db_session, role="viewer")
        current_user = {"user_id": user.id, "role": "viewer"}
        with pytest.raises(AppException) as exc_info:
            await UserService.create_api_key(
                db_session,
                org.id,
                {"name": "Forbidden Key"},
                current_user,
            )
        assert exc_info.value.code == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_list_api_keys_empty(self, db_session):
        org, _ = await _seed_user_and_org(db_session)
        keys = await UserService.list_api_keys(db_session, org.id)
        assert keys == []

    @pytest.mark.asyncio
    async def test_list_api_keys_with_data(self, db_session):
        org, user = await _seed_user_and_org(db_session, role="owner")
        current_user = {"user_id": user.id, "role": "owner"}
        await UserService.create_api_key(
            db_session,
            org.id,
            {"name": "Key 1"},
            current_user,
        )
        keys = await UserService.list_api_keys(db_session, org.id)
        assert len(keys) == 1
        assert keys[0]["name"] == "Key 1"
        assert "key" not in keys[0]  # Raw key not returned in list

    @pytest.mark.asyncio
    async def test_revoke_api_key_success(self, db_session):
        org, user = await _seed_user_and_org(db_session, role="owner")
        current_user = {"user_id": user.id, "role": "owner"}
        key_data = await UserService.create_api_key(
            db_session,
            org.id,
            {"name": "To Revoke"},
            current_user,
        )
        await UserService.revoke_api_key(db_session, org.id, key_data["id"], current_user)
        # Key should no longer be in active list
        keys = await UserService.list_api_keys(db_session, org.id)
        assert len(keys) == 0

    @pytest.mark.asyncio
    async def test_revoke_api_key_forbidden(self, db_session):
        org, user = await _seed_user_and_org(db_session, role="viewer")
        current_user = {"user_id": user.id, "role": "viewer"}
        with pytest.raises(AppException) as exc_info:
            await UserService.revoke_api_key(db_session, org.id, uuid4(), current_user)
        assert exc_info.value.code == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_revoke_api_key_not_found(self, db_session):
        org, user = await _seed_user_and_org(db_session, role="owner")
        current_user = {"user_id": user.id, "role": "owner"}
        with pytest.raises(AppException) as exc_info:
            await UserService.revoke_api_key(db_session, org.id, uuid4(), current_user)
        assert exc_info.value.code == "API_KEY_NOT_FOUND"


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------

class TestHelperFunctions:

    def test_role_level(self):
        assert _role_level("owner") == 100
        assert _role_level("admin") == 80
        assert _role_level("editor") == 60
        assert _role_level("writer") == 40
        assert _role_level("viewer") == 20
        assert _role_level("unknown") == 0

    def test_generate_api_key(self):
        key, prefix = _generate_api_key()
        assert len(key) > 20
        assert len(prefix) == 8
        assert key.startswith(prefix)
