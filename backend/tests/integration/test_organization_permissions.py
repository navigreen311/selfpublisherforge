"""Integration tests for organization router permission enforcement.

These tests verify that permission checks are properly enforced on organization endpoints.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import create_access_token, hash_password
from app.models.organization import Organization
from app.models.user import User, UserRole

settings = get_settings()
PREFIX = f"{settings.API_V1_PREFIX}/orgs"


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
) -> User:
    """Create a test user with a specific role."""
    user = User(
        org_id=org_id,
        email=email,
        password_hash=hash_password("TestPassword123!"),
        name="Test User",
        role=role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _make_token(user: User) -> str:
    """Generate an access token for a user."""
    return create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "org_id": str(user.org_id),
            "role": user.role.value,
        }
    )


def _auth_headers(token: str) -> dict:
    """Build authorization headers."""
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Unauthenticated Access Tests
# ---------------------------------------------------------------------------


class TestUnauthenticatedAccess:
    """Verify unauthenticated users cannot access organization endpoints."""

    @pytest.mark.asyncio
    async def test_get_org_requires_auth(self, client: AsyncClient, db: AsyncSession):
        """Unauthenticated user cannot get organization details."""
        org = await _create_org(db)
        resp = await client.get(f"{PREFIX}/{org.id}")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_update_org_requires_auth(self, client: AsyncClient, db: AsyncSession):
        """Unauthenticated user cannot update organization."""
        org = await _create_org(db)
        resp = await client.put(
            f"{PREFIX}/{org.id}",
            json={"name": "Updated Name", "description": "Test"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_list_members_requires_auth(self, client: AsyncClient, db: AsyncSession):
        """Unauthenticated user cannot list organization members."""
        org = await _create_org(db)
        resp = await client.get(f"{PREFIX}/{org.id}/members")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_create_invitation_requires_auth(self, client: AsyncClient, db: AsyncSession):
        """Unauthenticated user cannot create invitations."""
        org = await _create_org(db)
        resp = await client.post(
            f"{PREFIX}/{org.id}/invitations",
            json={"email": "invite@test.com", "role": "viewer"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_list_invitations_requires_auth(self, client: AsyncClient, db: AsyncSession):
        """Unauthenticated user cannot list invitations."""
        org = await _create_org(db)
        resp = await client.get(f"{PREFIX}/{org.id}/invitations")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_remove_member_requires_auth(self, client: AsyncClient, db: AsyncSession):
        """Unauthenticated user cannot remove members."""
        org = await _create_org(db)
        user_id = uuid.uuid4()
        resp = await client.delete(f"{PREFIX}/{org.id}/members/{user_id}")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Cross-Organization Access Tests
# ---------------------------------------------------------------------------


class TestCrossOrganizationAccess:
    """Verify users cannot access data from other organizations."""

    @pytest.mark.asyncio
    async def test_cannot_get_other_org(self, client: AsyncClient, db: AsyncSession):
        """User cannot get another organization's details."""
        org1 = await _create_org(db, "Org 1")
        org2 = await _create_org(db, "Org 2")
        user = await _create_user(db, org1.id, "user@org1.com", UserRole.ADMIN)
        token = _make_token(user)

        resp = await client.get(f"{PREFIX}/{org2.id}", headers=_auth_headers(token))
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_cannot_update_other_org(self, client: AsyncClient, db: AsyncSession):
        """User cannot update another organization."""
        org1 = await _create_org(db, "Org 1")
        org2 = await _create_org(db, "Org 2")
        user = await _create_user(db, org1.id, "admin@org1.com", UserRole.ADMIN)
        token = _make_token(user)

        resp = await client.put(
            f"{PREFIX}/{org2.id}",
            json={"name": "Hacked Name", "description": "Unauthorized"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_cannot_list_other_org_members(self, client: AsyncClient, db: AsyncSession):
        """User cannot list members from another organization."""
        org1 = await _create_org(db, "Org 1")
        org2 = await _create_org(db, "Org 2")
        user = await _create_user(db, org1.id, "user@org1.com", UserRole.VIEWER)
        token = _make_token(user)

        resp = await client.get(
            f"{PREFIX}/{org2.id}/members",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Role-Based Access Control Tests
# ---------------------------------------------------------------------------


class TestRoleBasedAccess:
    """Verify role-based access control on organization endpoints."""

    @pytest.mark.asyncio
    async def test_viewer_cannot_update_org(self, client: AsyncClient, db: AsyncSession):
        """Viewer cannot update organization."""
        org = await _create_org(db)
        user = await _create_user(db, org.id, "viewer@test.com", UserRole.VIEWER)
        token = _make_token(user)

        resp = await client.put(
            f"{PREFIX}/{org.id}",
            json={"name": "New Name", "description": "Test"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_viewer_cannot_create_invitation(self, client: AsyncClient, db: AsyncSession):
        """Viewer cannot create invitations."""
        org = await _create_org(db)
        user = await _create_user(db, org.id, "viewer@test.com", UserRole.VIEWER)
        token = _make_token(user)

        resp = await client.post(
            f"{PREFIX}/{org.id}/invitations",
            json={"email": "newuser@test.com", "role": "viewer"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_viewer_cannot_remove_member(self, client: AsyncClient, db: AsyncSession):
        """Viewer cannot remove organization members."""
        org = await _create_org(db)
        viewer = await _create_user(db, org.id, "viewer@test.com", UserRole.VIEWER)
        member = await _create_user(db, org.id, "member@test.com", UserRole.EDITOR)
        token = _make_token(viewer)

        resp = await client.delete(
            f"{PREFIX}/{org.id}/members/{member.id}",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_update_org(self, client: AsyncClient, db: AsyncSession):
        """Admin can update organization."""
        org = await _create_org(db)
        admin = await _create_user(db, org.id, "admin@test.com", UserRole.ADMIN)
        token = _make_token(admin)

        resp = await client.put(
            f"{PREFIX}/{org.id}",
            json={"name": "Updated Name", "description": "Admin update"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_admin_can_create_invitation(self, client: AsyncClient, db: AsyncSession):
        """Admin can create invitations."""
        org = await _create_org(db)
        admin = await _create_user(db, org.id, "admin@test.com", UserRole.ADMIN)
        token = _make_token(admin)

        resp = await client.post(
            f"{PREFIX}/{org.id}/invitations",
            json={"email": "newuser@test.com", "role": "viewer"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "newuser@test.com"

    @pytest.mark.asyncio
    async def test_owner_can_remove_member(self, client: AsyncClient, db: AsyncSession):
        """Owner can remove organization members."""
        org = await _create_org(db)
        owner = await _create_user(db, org.id, "owner@test.com", UserRole.OWNER)
        member = await _create_user(db, org.id, "member@test.com", UserRole.VIEWER)
        token = _make_token(owner)

        resp = await client.delete(
            f"{PREFIX}/{org.id}/members/{member.id}",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Authorized Access Tests
# ---------------------------------------------------------------------------


class TestAuthorizedAccess:
    """Verify authorized users can access their organization's data."""

    @pytest.mark.asyncio
    async def test_user_can_get_own_org(self, client: AsyncClient, db: AsyncSession):
        """User can get their own organization details."""
        org = await _create_org(db)
        user = await _create_user(db, org.id, "user@test.com", UserRole.VIEWER)
        token = _make_token(user)

        resp = await client.get(f"{PREFIX}/{org.id}", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(org.id)
        assert data["name"] == org.name

    @pytest.mark.asyncio
    async def test_user_can_list_own_org_members(self, client: AsyncClient, db: AsyncSession):
        """User can list members from their own organization."""
        org = await _create_org(db)
        user = await _create_user(db, org.id, "user@test.com", UserRole.VIEWER)
        token = _make_token(user)

        resp = await client.get(
            f"{PREFIX}/{org.id}/members",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_user_can_list_invitations(self, client: AsyncClient, db: AsyncSession):
        """User can list invitations for their organization."""
        org = await _create_org(db)
        user = await _create_user(db, org.id, "user@test.com", UserRole.ADMIN)
        token = _make_token(user)

        resp = await client.get(
            f"{PREFIX}/{org.id}/invitations",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
