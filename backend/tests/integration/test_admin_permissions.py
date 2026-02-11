"""Integration tests for admin router permission enforcement.

These tests verify that admin-only endpoints are properly protected.
"""

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole
from app.models.organization import Organization

settings = get_settings()
PREFIX = f"{settings.API_V1_PREFIX}/admin"


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

async def _create_org(db: AsyncSession, name: str = "Test Org") -> Organization:
    """Create a test organization."""
    org = Organization(
        name=name,
        slug=f"test-org-{uuid.uuid4().hex[:8]}",
        plan_tier="free",
        subscription_status="active",
    )
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org


async def _create_user(
    db: AsyncSession,
    org_id: uuid.UUID,
    email: str,
    role: UserRole = UserRole.VIEWER,
    is_platform_admin: bool = False,
) -> User:
    """Create a test user with a specific role.

    Note: Platform admin status is typically stored in preferences or a separate field.
    For this test, we'll use role=OWNER as a proxy for admin privileges.
    """
    user = User(
        org_id=org_id,
        email=email,
        password_hash=hash_password("TestPassword123!"),
        name="Test User",
        role=role,
        is_active=True,
        preferences={"is_platform_admin": is_platform_admin} if is_platform_admin else None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _make_token(user: User, is_admin: bool = False) -> str:
    """Generate an access token for a user."""
    return create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "org_id": str(user.org_id),
            "role": user.role.value,
            "is_admin": is_admin,
        }
    )


def _auth_headers(token: str) -> dict:
    """Build authorization headers."""
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Unauthenticated Access Tests
# ---------------------------------------------------------------------------

class TestUnauthenticatedAccess:
    """Verify unauthenticated users cannot access admin endpoints."""

    @pytest.mark.asyncio
    async def test_list_users_requires_auth(self, client: AsyncClient):
        """Unauthenticated user cannot list users."""
        resp = await client.get(f"{PREFIX}/users")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_get_feature_flags_requires_auth(self, client: AsyncClient):
        """Unauthenticated user cannot get feature flags."""
        resp = await client.get(f"{PREFIX}/feature-flags")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_update_feature_flag_requires_auth(self, client: AsyncClient):
        """Unauthenticated user cannot update feature flags."""
        resp = await client.put(
            f"{PREFIX}/feature-flags/test-flag",
            json={"enabled": True, "description": "Test"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_deactivate_user_requires_auth(self, client: AsyncClient):
        """Unauthenticated user cannot deactivate users."""
        user_id = uuid.uuid4()
        resp = await client.delete(f"{PREFIX}/users/{user_id}")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Non-Admin User Access Tests
# ---------------------------------------------------------------------------

class TestNonAdminAccess:
    """Verify non-admin users cannot access admin endpoints."""

    @pytest.mark.asyncio
    async def test_viewer_cannot_list_users(self, client: AsyncClient, db: AsyncSession):
        """Viewer cannot access user list."""
        org = await _create_org(db)
        user = await _create_user(db, org.id, "viewer@test.com", UserRole.VIEWER)
        token = _make_token(user, is_admin=False)

        resp = await client.get(f"{PREFIX}/users", headers=_auth_headers(token))

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_editor_cannot_get_feature_flags(self, client: AsyncClient, db: AsyncSession):
        """Editor cannot access feature flags."""
        org = await _create_org(db)
        user = await _create_user(db, org.id, "editor@test.com", UserRole.EDITOR)
        token = _make_token(user, is_admin=False)

        resp = await client.get(f"{PREFIX}/feature-flags", headers=_auth_headers(token))

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_owner_cannot_update_feature_flags(self, client: AsyncClient, db: AsyncSession):
        """Organization owner (non-platform-admin) cannot update feature flags."""
        org = await _create_org(db)
        user = await _create_user(db, org.id, "owner@test.com", UserRole.OWNER)
        token = _make_token(user, is_admin=False)

        resp = await client.put(
            f"{PREFIX}/feature-flags/test-flag",
            json={"enabled": True, "description": "Test"},
            headers=_auth_headers(token),
        )

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_cannot_deactivate_users(self, client: AsyncClient, db: AsyncSession):
        """Organization admin (non-platform-admin) cannot deactivate users."""
        org = await _create_org(db)
        admin = await _create_user(db, org.id, "admin@test.com", UserRole.ADMIN)
        target_user = await _create_user(db, org.id, "target@test.com", UserRole.VIEWER)
        token = _make_token(admin, is_admin=False)

        resp = await client.delete(
            f"{PREFIX}/users/{target_user.id}",
            headers=_auth_headers(token),
        )

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Platform Admin Access Tests
# ---------------------------------------------------------------------------

class TestPlatformAdminAccess:
    """Verify platform admins can access all admin endpoints."""

    @pytest.mark.asyncio
    async def test_admin_can_list_users(self, client: AsyncClient, db: AsyncSession):
        """Platform admin can list all users."""
        org = await _create_org(db)
        admin = await _create_user(
            db, org.id, "admin@test.com", UserRole.OWNER, is_platform_admin=True
        )
        # Create some additional users
        await _create_user(db, org.id, "user1@test.com", UserRole.VIEWER)
        await _create_user(db, org.id, "user2@test.com", UserRole.EDITOR)

        token = _make_token(admin, is_admin=True)
        resp = await client.get(f"{PREFIX}/users", headers=_auth_headers(token))

        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        assert isinstance(data["users"], list)
        # Should see at least the 3 users we created
        assert len(data["users"]) >= 3

    @pytest.mark.asyncio
    async def test_admin_can_filter_users_by_tier(self, client: AsyncClient, db: AsyncSession):
        """Platform admin can filter users by tier."""
        org = await _create_org(db)
        admin = await _create_user(
            db, org.id, "admin@test.com", UserRole.OWNER, is_platform_admin=True
        )

        token = _make_token(admin, is_admin=True)
        resp = await client.get(
            f"{PREFIX}/users?tier=free&limit=10",
            headers=_auth_headers(token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data

    @pytest.mark.asyncio
    async def test_admin_can_search_users(self, client: AsyncClient, db: AsyncSession):
        """Platform admin can search users by email/name."""
        org = await _create_org(db)
        admin = await _create_user(
            db, org.id, "admin@test.com", UserRole.OWNER, is_platform_admin=True
        )
        await _create_user(db, org.id, "searchme@test.com", UserRole.VIEWER)

        token = _make_token(admin, is_admin=True)
        resp = await client.get(
            f"{PREFIX}/users?search=searchme",
            headers=_auth_headers(token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data

    @pytest.mark.asyncio
    async def test_admin_can_get_feature_flags(self, client: AsyncClient, db: AsyncSession):
        """Platform admin can retrieve all feature flags."""
        org = await _create_org(db)
        admin = await _create_user(
            db, org.id, "admin@test.com", UserRole.OWNER, is_platform_admin=True
        )

        token = _make_token(admin, is_admin=True)
        resp = await client.get(f"{PREFIX}/feature-flags", headers=_auth_headers(token))

        assert resp.status_code == 200
        data = resp.json()
        assert "flags" in data
        assert isinstance(data["flags"], list)

    @pytest.mark.asyncio
    async def test_admin_can_update_feature_flag(self, client: AsyncClient, db: AsyncSession):
        """Platform admin can update feature flags."""
        org = await _create_org(db)
        admin = await _create_user(
            db, org.id, "admin@test.com", UserRole.OWNER, is_platform_admin=True
        )

        token = _make_token(admin, is_admin=True)
        resp = await client.put(
            f"{PREFIX}/feature-flags/ai-generation",
            json={
                "enabled": True,
                "description": "Enable AI content generation",
            },
            headers=_auth_headers(token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["flag_key"] == "ai-generation"
        assert data["enabled"] is True

    @pytest.mark.asyncio
    async def test_admin_can_deactivate_user(self, client: AsyncClient, db: AsyncSession):
        """Platform admin can deactivate user accounts."""
        org = await _create_org(db)
        admin = await _create_user(
            db, org.id, "admin@test.com", UserRole.OWNER, is_platform_admin=True
        )
        target_user = await _create_user(db, org.id, "target@test.com", UserRole.VIEWER)

        token = _make_token(admin, is_admin=True)
        resp = await client.delete(
            f"{PREFIX}/users/{target_user.id}",
            headers=_auth_headers(token),
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert "deactivated" in data["message"].lower()


# ---------------------------------------------------------------------------
# Admin Operations Scope Tests
# ---------------------------------------------------------------------------

class TestAdminOperationsScope:
    """Verify admin operations work across organizations."""

    @pytest.mark.asyncio
    async def test_admin_can_see_users_from_all_orgs(self, client: AsyncClient, db: AsyncSession):
        """Platform admin can see users from all organizations."""
        org1 = await _create_org(db, "Org 1")
        org2 = await _create_org(db, "Org 2")

        admin = await _create_user(
            db, org1.id, "admin@test.com", UserRole.OWNER, is_platform_admin=True
        )
        await _create_user(db, org1.id, "user1@org1.com", UserRole.VIEWER)
        await _create_user(db, org2.id, "user2@org2.com", UserRole.VIEWER)

        token = _make_token(admin, is_admin=True)
        resp = await client.get(f"{PREFIX}/users", headers=_auth_headers(token))

        assert resp.status_code == 200
        data = resp.json()
        # Should see users from both organizations
        assert len(data["users"]) >= 3

    @pytest.mark.asyncio
    async def test_admin_can_deactivate_user_from_different_org(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Platform admin can deactivate users from any organization."""
        org1 = await _create_org(db, "Org 1")
        org2 = await _create_org(db, "Org 2")

        admin = await _create_user(
            db, org1.id, "admin@test.com", UserRole.OWNER, is_platform_admin=True
        )
        target_user = await _create_user(db, org2.id, "target@org2.com", UserRole.VIEWER)

        token = _make_token(admin, is_admin=True)
        resp = await client.delete(
            f"{PREFIX}/users/{target_user.id}",
            headers=_auth_headers(token),
        )

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.mark.asyncio
    async def test_deactivate_nonexistent_user(self, client: AsyncClient, db: AsyncSession):
        """Attempting to deactivate non-existent user returns 404."""
        org = await _create_org(db)
        admin = await _create_user(
            db, org.id, "admin@test.com", UserRole.OWNER, is_platform_admin=True
        )

        token = _make_token(admin, is_admin=True)
        fake_user_id = uuid.uuid4()
        resp = await client.delete(
            f"{PREFIX}/users/{fake_user_id}",
            headers=_auth_headers(token),
        )

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_nonexistent_feature_flag(self, client: AsyncClient, db: AsyncSession):
        """Updating non-existent feature flag returns 404."""
        org = await _create_org(db)
        admin = await _create_user(
            db, org.id, "admin@test.com", UserRole.OWNER, is_platform_admin=True
        )

        token = _make_token(admin, is_admin=True)
        resp = await client.put(
            f"{PREFIX}/feature-flags/nonexistent-flag",
            json={"enabled": True, "description": "Test"},
            headers=_auth_headers(token),
        )

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_users_with_pagination(self, client: AsyncClient, db: AsyncSession):
        """User list respects pagination parameters."""
        org = await _create_org(db)
        admin = await _create_user(
            db, org.id, "admin@test.com", UserRole.OWNER, is_platform_admin=True
        )

        # Create multiple users
        for i in range(5):
            await _create_user(db, org.id, f"user{i}@test.com", UserRole.VIEWER)

        token = _make_token(admin, is_admin=True)

        # Test limit
        resp = await client.get(
            f"{PREFIX}/users?limit=3",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["users"]) <= 3

        # Test offset
        resp = await client.get(
            f"{PREFIX}/users?offset=2&limit=2",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["users"]) <= 2
