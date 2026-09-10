"""Unit tests for the organization service layer.

Tests organization CRUD operations, member management, and invitations
using mocked database calls.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.conftest import populate_server_defaults

from app.core.exceptions import AppException
from app.models.user import UserRole
from app.modules.organization import service
from shared.types.enums import PlanTier

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_org_row(
    org_id: uuid.UUID | None = None,
    name: str = "Test Org",
    description: str | None = None,
    tier: PlanTier = PlanTier.FREE,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> dict:
    """Build a dict that mimics a row from the organizations table."""
    now = datetime.now(UTC)
    return {
        "id": org_id or uuid.uuid4(),
        "name": name,
        "description": description,
        "plan_tier": tier,
        "created_at": created_at or now,
        "updated_at": updated_at or now,
    }


def _make_user_row(
    user_id: uuid.UUID | None = None,
    email: str = "user@test.com",
    name: str = "Test User",
    org_id: uuid.UUID | None = None,
    role: UserRole = UserRole.EDITOR,
    created_at: datetime | None = None,
) -> dict:
    """Build a dict that mimics a row from the users table."""
    return {
        "id": user_id or uuid.uuid4(),
        "email": email,
        "name": name,
        "org_id": org_id or uuid.uuid4(),
        "role": role,
        "created_at": created_at or datetime.now(UTC),
    }


def _mock_org_orm(row: dict) -> MagicMock:
    """Create a mock Organization ORM object from a row dict."""
    org = MagicMock()
    for key, value in row.items():
        setattr(org, key, value)
    return org


def _mock_user_orm(row: dict) -> MagicMock:
    """Create a mock User ORM object from a row dict."""
    user = MagicMock()
    for key, value in row.items():
        setattr(user, key, value)
    return user


def _mock_db_with_org(org_row: dict | None) -> AsyncMock:
    """Return a mock db session that returns the given org."""
    mock_db = AsyncMock()

    if org_row:
        org_mock = _mock_org_orm(org_row)
        result = MagicMock()
        result.scalar_one_or_none.return_value = org_mock
    else:
        result = MagicMock()
        result.scalar_one_or_none.return_value = None

    mock_db.execute = AsyncMock(return_value=result)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock(side_effect=populate_server_defaults)

    return mock_db


def _mock_db_with_users(user_rows: list[dict]) -> AsyncMock:
    """Return a mock db session that returns given users."""
    mock_db = AsyncMock()

    user_scalars = MagicMock()
    user_scalars.all.return_value = [_mock_user_orm(row) for row in user_rows]
    user_result = MagicMock()
    user_result.scalars.return_value = user_scalars

    mock_db.execute = AsyncMock(return_value=user_result)

    return mock_db


# ===========================================================================
# Organization Retrieval Tests
# ===========================================================================


class TestGetOrganization:
    """Tests for get_organization service function."""

    @pytest.mark.asyncio
    async def test_returns_organization(self):
        """Should return organization details when found."""
        org_id = uuid.uuid4()
        org_row = _make_org_row(
            org_id=org_id, name="Test Organization", description="A test organization", tier=PlanTier.PRO
        )
        mock_db = _mock_db_with_org(org_row)

        result = await service.get_organization(mock_db, org_id)

        assert result.id == org_id
        assert result.name == "Test Organization"
        assert result.description == "A test organization"
        assert result.tier == PlanTier.PRO

    @pytest.mark.asyncio
    async def test_organization_not_found_raises_404(self):
        """Should raise ORGANIZATION_NOT_FOUND when org doesn't exist."""
        org_id = uuid.uuid4()
        mock_db = _mock_db_with_org(None)

        with pytest.raises(AppException) as exc_info:
            await service.get_organization(mock_db, org_id)

        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "ORGANIZATION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_organization_without_description(self):
        """Should handle organization without description."""
        org_id = uuid.uuid4()
        org_row = _make_org_row(org_id=org_id, description=None)
        mock_db = _mock_db_with_org(org_row)

        result = await service.get_organization(mock_db, org_id)

        assert result.id == org_id
        assert result.description is None


# ===========================================================================
# Organization Update Tests
# ===========================================================================


class TestUpdateOrganization:
    """Tests for update_organization service function."""

    @pytest.mark.asyncio
    async def test_updates_name_and_description(self):
        """Should update both name and description."""
        org_id = uuid.uuid4()
        org_row = _make_org_row(org_id=org_id, name="Old Name", description="Old Desc")
        mock_db = _mock_db_with_org(org_row)

        result = await service.update_organization(mock_db, org_id, name="New Name", description="New Description")

        assert result.name == "New Name"
        assert result.description == "New Description"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_only_name(self):
        """Should update only the name when description is None."""
        org_id = uuid.uuid4()
        org_row = _make_org_row(org_id=org_id, name="Old Name", description="Existing Desc")
        mock_db = _mock_db_with_org(org_row)

        result = await service.update_organization(mock_db, org_id, name="New Name", description=None)

        assert result.name == "New Name"
        # Description should remain unchanged in the mock
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_only_description(self):
        """Should update only the description when name is None."""
        org_id = uuid.uuid4()
        org_row = _make_org_row(org_id=org_id, name="Existing Name", description="Old Desc")
        mock_db = _mock_db_with_org(org_row)

        result = await service.update_organization(mock_db, org_id, name=None, description="New Description")

        assert result.description == "New Description"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_organization_not_found_raises_404(self):
        """Should raise ORGANIZATION_NOT_FOUND when org doesn't exist."""
        org_id = uuid.uuid4()
        mock_db = _mock_db_with_org(None)

        with pytest.raises(AppException) as exc_info:
            await service.update_organization(mock_db, org_id, name="New Name")

        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "ORGANIZATION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_no_update_when_both_none(self):
        """Should still work when both name and description are None."""
        org_id = uuid.uuid4()
        org_row = _make_org_row(org_id=org_id)
        mock_db = _mock_db_with_org(org_row)

        result = await service.update_organization(mock_db, org_id, name=None, description=None)

        # Should still commit even if no changes
        mock_db.commit.assert_called_once()


# ===========================================================================
# Member Listing Tests
# ===========================================================================


class TestListMembers:
    """Tests for list_members service function."""

    @pytest.mark.asyncio
    async def test_returns_members(self):
        """Should return all members of the organization."""
        org_id = uuid.uuid4()
        user_rows = [
            _make_user_row(
                user_id=uuid.uuid4(), email="user1@test.com", name="User One", org_id=org_id, role=UserRole.OWNER
            ),
            _make_user_row(
                user_id=uuid.uuid4(), email="user2@test.com", name="User Two", org_id=org_id, role=UserRole.EDITOR
            ),
        ]
        mock_db = _mock_db_with_users(user_rows)

        result = await service.list_members(mock_db, org_id)

        assert result.total == 2
        assert len(result.members) == 2
        assert result.members[0].email == "user1@test.com"
        assert result.members[0].role == "owner"
        assert result.members[1].email == "user2@test.com"
        assert result.members[1].role == "editor"

    @pytest.mark.asyncio
    async def test_empty_organization(self):
        """Should return empty list when org has no members."""
        org_id = uuid.uuid4()
        mock_db = _mock_db_with_users([])

        result = await service.list_members(mock_db, org_id)

        assert result.total == 0
        assert len(result.members) == 0

    @pytest.mark.asyncio
    async def test_members_ordered_by_join_date(self):
        """Should order members by created_at."""
        org_id = uuid.uuid4()
        now = datetime.now(UTC)
        user_rows = [
            _make_user_row(email="older@test.com", org_id=org_id, created_at=now),
            _make_user_row(email="newer@test.com", org_id=org_id, created_at=now),
        ]
        mock_db = _mock_db_with_users(user_rows)

        result = await service.list_members(mock_db, org_id)

        assert len(result.members) == 2


# ===========================================================================
# Invitation Tests
# ===========================================================================


class TestCreateInvitation:
    """Tests for create_invitation service function."""

    @pytest.mark.asyncio
    async def test_creates_invitation(self):
        """Should create an invitation with correct details (stub)."""
        mock_db = AsyncMock()
        org_id = uuid.uuid4()

        result = await service.create_invitation(mock_db, org_id, email="newuser@test.com", role="member")

        assert result.email == "newuser@test.com"
        assert result.role == "member"
        assert result.status == "pending"
        assert result.id is not None
        assert result.invited_at is not None
        assert result.expires_at is not None

    @pytest.mark.asyncio
    async def test_invitation_expiry_is_7_days(self):
        """Should set invitation to expire in 7 days."""
        mock_db = AsyncMock()
        org_id = uuid.uuid4()

        result = await service.create_invitation(mock_db, org_id, email="test@test.com", role="viewer")

        # Check that expires_at is approximately 7 days from invited_at
        delta = result.expires_at - result.invited_at
        assert 6 <= delta.days <= 7

    @pytest.mark.asyncio
    async def test_creates_admin_invitation(self):
        """Should create invitation with admin role."""
        mock_db = AsyncMock()
        org_id = uuid.uuid4()

        result = await service.create_invitation(mock_db, org_id, email="admin@test.com", role="admin")

        assert result.role == "admin"


class TestListInvitations:
    """Tests for list_invitations service function."""

    @pytest.mark.asyncio
    async def test_returns_empty_list(self):
        """Should return empty invitations list (stub implementation)."""
        mock_db = AsyncMock()
        org_id = uuid.uuid4()

        result = await service.list_invitations(mock_db, org_id)

        assert result.total == 0
        assert len(result.invitations) == 0


# ===========================================================================
# Member Removal Tests
# ===========================================================================


class TestRemoveMember:
    """Tests for remove_member service function."""

    @pytest.mark.asyncio
    async def test_removes_member(self):
        """Should remove an existing member."""
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()

        user_row = _make_user_row(user_id=user_id, org_id=org_id)
        mock_db = AsyncMock()

        user_mock = _mock_user_orm(user_row)
        result = MagicMock()
        result.scalar_one_or_none.return_value = user_mock
        mock_db.execute = AsyncMock(return_value=result)

        # Should not raise
        await service.remove_member(mock_db, org_id, user_id)

    @pytest.mark.asyncio
    async def test_member_not_found_raises_404(self):
        """Should raise MEMBER_NOT_FOUND when user doesn't exist."""
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        with pytest.raises(AppException) as exc_info:
            await service.remove_member(mock_db, org_id, user_id)

        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "MEMBER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_member_from_different_org_raises_404(self):
        """Should raise MEMBER_NOT_FOUND when user belongs to different org."""
        org_id = uuid.uuid4()
        different_org_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # User exists but belongs to different org
        mock_db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None  # Query filters by org_id
        mock_db.execute = AsyncMock(return_value=result)

        with pytest.raises(AppException) as exc_info:
            await service.remove_member(mock_db, org_id, user_id)

        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "MEMBER_NOT_FOUND"
