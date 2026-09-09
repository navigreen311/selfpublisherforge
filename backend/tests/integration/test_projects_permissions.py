"""Integration tests for projects router permission enforcement.

These tests verify that permission checks are properly enforced on project endpoints.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import create_access_token, hash_password
from app.models.organization import Organization
from app.models.project import Project, ProjectStatus, ProjectType
from app.models.user import User, UserRole

settings = get_settings()
PREFIX = f"{settings.API_V1_PREFIX}/projects"


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


async def _create_project(
    db: AsyncSession,
    org_id: uuid.UUID,
    title: str = "Test Project",
    project_type: ProjectType = ProjectType.BOOK,
) -> Project:
    """Create a test project."""
    project = Project(
        org_id=org_id,
        title=title,
        type=project_type,
        status=ProjectStatus.DRAFT,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


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
    """Verify unauthenticated users cannot access project endpoints."""

    @pytest.mark.asyncio
    async def test_create_project_requires_auth(self, client: AsyncClient):
        """Unauthenticated user cannot create projects."""
        resp = await client.post(
            f"{PREFIX}/",
            json={
                "title": "Unauthorized Project",
                "description": "Test",
                "project_type": "book",
            },
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_list_projects_requires_auth(self, client: AsyncClient):
        """Unauthenticated user cannot list projects."""
        resp = await client.get(f"{PREFIX}/")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_get_project_requires_auth(self, client: AsyncClient, db: AsyncSession):
        """Unauthenticated user cannot get project details."""
        org = await _create_org(db)
        project = await _create_project(db, org.id)

        resp = await client.get(f"{PREFIX}/{project.id}")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_update_project_requires_auth(self, client: AsyncClient, db: AsyncSession):
        """Unauthenticated user cannot update projects."""
        org = await _create_org(db)
        project = await _create_project(db, org.id)

        resp = await client.put(
            f"{PREFIX}/{project.id}",
            json={"title": "Hacked Title"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_project_requires_auth(self, client: AsyncClient, db: AsyncSession):
        """Unauthenticated user cannot delete projects."""
        org = await _create_org(db)
        project = await _create_project(db, org.id)

        resp = await client.delete(f"{PREFIX}/{project.id}")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Cross-Organization Access Tests
# ---------------------------------------------------------------------------


class TestCrossOrganizationAccess:
    """Verify users cannot access projects from other organizations."""

    @pytest.mark.asyncio
    async def test_cannot_see_other_org_projects_in_list(self, client: AsyncClient, db: AsyncSession):
        """User cannot see projects from another organization in list."""
        org1 = await _create_org(db, "Org 1")
        org2 = await _create_org(db, "Org 2")
        user = await _create_user(db, org1.id, "user@org1.com", UserRole.VIEWER)

        # Create projects in both orgs
        await _create_project(db, org1.id, "Org1 Project")
        await _create_project(db, org2.id, "Org2 Project")

        token = _make_token(user)
        resp = await client.get(f"{PREFIX}/", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()

        # Should only see org1's project
        assert len(data) == 1
        assert data[0]["title"] == "Org1 Project"

    @pytest.mark.asyncio
    async def test_cannot_get_other_org_project(self, client: AsyncClient, db: AsyncSession):
        """User cannot get project details from another organization."""
        org1 = await _create_org(db, "Org 1")
        org2 = await _create_org(db, "Org 2")
        user = await _create_user(db, org1.id, "user@org1.com", UserRole.VIEWER)
        project = await _create_project(db, org2.id, "Other Org Project")

        token = _make_token(user)
        resp = await client.get(f"{PREFIX}/{project.id}", headers=_auth_headers(token))

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_cannot_update_other_org_project(self, client: AsyncClient, db: AsyncSession):
        """User cannot update projects from another organization."""
        org1 = await _create_org(db, "Org 1")
        org2 = await _create_org(db, "Org 2")
        user = await _create_user(db, org1.id, "admin@org1.com", UserRole.ADMIN)
        project = await _create_project(db, org2.id, "Other Org Project")

        token = _make_token(user)
        resp = await client.put(
            f"{PREFIX}/{project.id}",
            json={"title": "Hacked Title"},
            headers=_auth_headers(token),
        )

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_cannot_delete_other_org_project(self, client: AsyncClient, db: AsyncSession):
        """User cannot delete projects from another organization."""
        org1 = await _create_org(db, "Org 1")
        org2 = await _create_org(db, "Org 2")
        user = await _create_user(db, org1.id, "admin@org1.com", UserRole.ADMIN)
        project = await _create_project(db, org2.id, "Other Org Project")

        token = _make_token(user)
        resp = await client.delete(
            f"{PREFIX}/{project.id}",
            headers=_auth_headers(token),
        )

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Role-Based Access Control Tests
# ---------------------------------------------------------------------------


class TestRoleBasedAccess:
    """Verify role-based access control on project endpoints."""

    @pytest.mark.asyncio
    async def test_viewer_can_list_projects(self, client: AsyncClient, db: AsyncSession):
        """Viewer can list projects in their organization."""
        org = await _create_org(db)
        user = await _create_user(db, org.id, "viewer@test.com", UserRole.VIEWER)
        await _create_project(db, org.id, "Test Project")

        token = _make_token(user)
        resp = await client.get(f"{PREFIX}/", headers=_auth_headers(token))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_viewer_can_get_project(self, client: AsyncClient, db: AsyncSession):
        """Viewer can get project details."""
        org = await _create_org(db)
        user = await _create_user(db, org.id, "viewer@test.com", UserRole.VIEWER)
        project = await _create_project(db, org.id, "Test Project")

        token = _make_token(user)
        resp = await client.get(f"{PREFIX}/{project.id}", headers=_auth_headers(token))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_viewer_cannot_update_project(self, client: AsyncClient, db: AsyncSession):
        """Viewer cannot update projects."""
        org = await _create_org(db)
        user = await _create_user(db, org.id, "viewer@test.com", UserRole.VIEWER)
        project = await _create_project(db, org.id, "Test Project")

        token = _make_token(user)
        resp = await client.put(
            f"{PREFIX}/{project.id}",
            json={"title": "Updated Title"},
            headers=_auth_headers(token),
        )

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_viewer_cannot_delete_project(self, client: AsyncClient, db: AsyncSession):
        """Viewer cannot delete projects."""
        org = await _create_org(db)
        user = await _create_user(db, org.id, "viewer@test.com", UserRole.VIEWER)
        project = await _create_project(db, org.id, "Test Project")

        token = _make_token(user)
        resp = await client.delete(
            f"{PREFIX}/{project.id}",
            headers=_auth_headers(token),
        )

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_editor_can_create_project(self, client: AsyncClient, db: AsyncSession):
        """Editor can create projects."""
        org = await _create_org(db)
        user = await _create_user(db, org.id, "editor@test.com", UserRole.EDITOR)

        token = _make_token(user)
        resp = await client.post(
            f"{PREFIX}/",
            json={
                "title": "New Project",
                "description": "Editor's project",
                "project_type": "book",
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_editor_can_update_project(self, client: AsyncClient, db: AsyncSession):
        """Editor can update projects."""
        org = await _create_org(db)
        user = await _create_user(db, org.id, "editor@test.com", UserRole.EDITOR)
        project = await _create_project(db, org.id, "Test Project")

        token = _make_token(user)
        resp = await client.put(
            f"{PREFIX}/{project.id}",
            json={"title": "Updated by Editor"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_admin_can_delete_project(self, client: AsyncClient, db: AsyncSession):
        """Admin can delete projects."""
        org = await _create_org(db)
        admin = await _create_user(db, org.id, "admin@test.com", UserRole.ADMIN)
        project = await _create_project(db, org.id, "Test Project")

        token = _make_token(admin)
        resp = await client.delete(
            f"{PREFIX}/{project.id}",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Soft Delete Tests
# ---------------------------------------------------------------------------


class TestSoftDeletedProjects:
    """Verify soft-deleted projects don't appear in lists."""

    @pytest.mark.asyncio
    async def test_deleted_projects_not_in_list(self, client: AsyncClient, db: AsyncSession):
        """Soft-deleted projects should not appear in project list."""
        org = await _create_org(db)
        admin = await _create_user(db, org.id, "admin@test.com", UserRole.ADMIN)

        # Create two projects
        project1 = await _create_project(db, org.id, "Active Project")
        project2 = await _create_project(db, org.id, "To Be Deleted")

        token = _make_token(admin)

        # List before deletion
        resp = await client.get(f"{PREFIX}/", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

        # Delete one project
        resp = await client.delete(
            f"{PREFIX}/{project2.id}",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200

        # List after deletion - should only see active project
        resp = await client.get(f"{PREFIX}/", headers=_auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Active Project"

    @pytest.mark.asyncio
    async def test_deleted_project_not_accessible(self, client: AsyncClient, db: AsyncSession):
        """Soft-deleted project should not be accessible via GET."""
        org = await _create_org(db)
        admin = await _create_user(db, org.id, "admin@test.com", UserRole.ADMIN)
        project = await _create_project(db, org.id, "To Be Deleted")

        token = _make_token(admin)

        # Delete the project
        resp = await client.delete(
            f"{PREFIX}/{project.id}",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200

        # Try to get the deleted project
        resp = await client.get(
            f"{PREFIX}/{project.id}",
            headers=_auth_headers(token),
        )

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Project Filtering Tests
# ---------------------------------------------------------------------------


class TestProjectFiltering:
    """Verify project filtering by type and status."""

    @pytest.mark.asyncio
    async def test_filter_by_project_type(self, client: AsyncClient, db: AsyncSession):
        """Can filter projects by type."""
        org = await _create_org(db)
        user = await _create_user(db, org.id, "user@test.com", UserRole.VIEWER)

        await _create_project(db, org.id, "Book Project", ProjectType.BOOK)
        await _create_project(db, org.id, "Series Project", ProjectType.SERIES)
        await _create_project(db, org.id, "Course Project", ProjectType.COURSE)

        token = _make_token(user)

        # Filter for books only
        resp = await client.get(
            f"{PREFIX}/?project_type=book",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Book Project"

    @pytest.mark.asyncio
    async def test_filter_by_status(self, client: AsyncClient, db: AsyncSession):
        """Can filter projects by status."""
        org = await _create_org(db)
        user = await _create_user(db, org.id, "user@test.com", UserRole.VIEWER)

        project1 = await _create_project(db, org.id, "Draft Project")
        project2 = await _create_project(db, org.id, "Active Project")
        project2.status = ProjectStatus.ACTIVE
        await db.commit()

        token = _make_token(user)

        # Filter for active projects
        resp = await client.get(
            f"{PREFIX}/?status=active",
            headers=_auth_headers(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Active Project"
