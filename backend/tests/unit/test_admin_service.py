"""Unit tests for the admin service layer.

Tests platform administration functions including user listing, feature flags,
and user management operations using mocked database calls.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import AppException
from app.modules.admin import service
from app.modules.admin.schemas import UserListRequest
from shared.types.enums import PlanTier

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user_row(
    user_id: uuid.UUID | None = None,
    email: str = "user@test.com",
    name: str = "Test User",
    is_active: bool = True,
    org_id: uuid.UUID | None = None,
    created_at: datetime | None = None,
) -> dict:
    """Build a dict that mimics a row from the users table."""
    return {
        "id": user_id or uuid.uuid4(),
        "email": email,
        "name": name,
        "is_active": is_active,
        # The column is org_id — list_users reads user.org_id.
        "org_id": org_id or uuid.uuid4(),
        "created_at": created_at or datetime.now(UTC),
    }


def _make_org_row(
    org_id: uuid.UUID | None = None,
    tier: PlanTier = PlanTier.FREE,
) -> dict:
    """Build a dict that mimics a row from the organizations table."""
    return {
        "id": org_id or uuid.uuid4(),
        # The column is plan_tier — list_users reads org.plan_tier.
        "plan_tier": tier,
    }


def _mock_user_orm(row: dict) -> SimpleNamespace:
    """Create a stand-in User ORM object from a row dict."""
    return SimpleNamespace(**row)


def _mock_db_with_users(user_rows: list[dict], org_rows: list[dict]) -> AsyncMock:
    """Return a mock db session that returns given users and orgs."""
    mock_db = AsyncMock()

    # For the user query
    user_scalars = MagicMock()
    user_scalars.all.return_value = [_mock_user_orm(row) for row in user_rows]
    user_result = MagicMock()
    user_result.scalars.return_value = user_scalars

    # For org queries (one per user)
    org_results = []
    for org_row in org_rows:
        org_scalar = MagicMock()
        org_mock = SimpleNamespace(**org_row)
        org_scalar.scalar_one_or_none.return_value = org_mock
        org_results.append(org_scalar)

    # For count query
    count_scalar = 10  # Total count

    # Setup execute to return different results based on call order
    call_count = {"count": 0}

    def execute_side_effect(query):
        call_count["count"] += 1
        # list_users takes its total from db.scalar(count_query), so the first
        # execute() is the user query, not the count.
        if call_count["count"] == 1:
            return user_result
        # Subsequent calls: one org lookup per user
        idx = call_count["count"] - 2
        if idx < len(org_results):
            return org_results[idx]
        return org_results[-1] if org_results else MagicMock()

    mock_db.execute = AsyncMock(side_effect=execute_side_effect)
    mock_db.scalar = AsyncMock(return_value=count_scalar)
    mock_db.commit = AsyncMock()
    mock_db.flush = AsyncMock()

    return mock_db


def _mock_db_no_users() -> AsyncMock:
    """Return a mock db session that returns no users."""
    mock_db = AsyncMock()

    # For count query
    count_result = MagicMock()
    count_result.scalar.return_value = 0

    # For user query
    user_scalars = MagicMock()
    user_scalars.all.return_value = []
    user_result = MagicMock()
    user_result.scalars.return_value = user_scalars

    call_count = {"count": 0}

    def execute_side_effect(query):
        call_count["count"] += 1
        if call_count["count"] == 1:
            return count_result
        return user_result

    mock_db.execute = AsyncMock(side_effect=execute_side_effect)
    mock_db.scalar = AsyncMock(return_value=0)

    return mock_db


def _mock_db_with_user_for_deactivation(user_row: dict | None) -> AsyncMock:
    """Return a mock db for user deactivation tests."""
    mock_db = AsyncMock()

    if user_row:
        user_mock = _mock_user_orm(user_row)
        result = MagicMock()
        result.scalar_one_or_none.return_value = user_mock
    else:
        result = MagicMock()
        result.scalar_one_or_none.return_value = None

    mock_db.execute = AsyncMock(return_value=result)
    mock_db.commit = AsyncMock()

    return mock_db


# ===========================================================================
# User Listing Tests
# ===========================================================================


class TestListUsers:
    """Tests for list_users service function."""

    @pytest.mark.asyncio
    async def test_returns_users_with_pagination(self):
        """Should return users with total count."""
        user_id = uuid.uuid4()
        org_id = uuid.uuid4()
        user_rows = [
            _make_user_row(user_id=user_id, email="test1@test.com", org_id=org_id),
            _make_user_row(email="test2@test.com", org_id=org_id),
        ]
        org_rows = [
            _make_org_row(org_id=org_id, tier=PlanTier.PRO),
            _make_org_row(org_id=org_id, tier=PlanTier.PRO),
        ]

        mock_db = _mock_db_with_users(user_rows, org_rows)

        request = UserListRequest(limit=10, offset=0)
        result = await service.list_users(mock_db, request)

        assert result.total == 10
        assert len(result.users) == 2
        assert result.users[0].email == "test1@test.com"
        assert result.users[0].tier == PlanTier.PRO

    @pytest.mark.asyncio
    async def test_search_filters_users(self):
        """Should filter users by search term."""
        user_id = uuid.uuid4()
        org_id = uuid.uuid4()
        user_rows = [
            _make_user_row(user_id=user_id, email="alice@test.com", name="Alice", org_id=org_id),
        ]
        org_rows = [
            _make_org_row(org_id=org_id, tier=PlanTier.FREE),
        ]

        mock_db = _mock_db_with_users(user_rows, org_rows)

        request = UserListRequest(search="alice", limit=10, offset=0)
        result = await service.list_users(mock_db, request)

        assert len(result.users) == 1
        assert result.users[0].name == "Alice"

    @pytest.mark.asyncio
    async def test_tier_filter(self):
        """Should filter users by tier."""
        user_id = uuid.uuid4()
        org_id = uuid.uuid4()
        user_rows = [
            _make_user_row(user_id=user_id, email="pro@test.com", org_id=org_id),
        ]
        org_rows = [
            _make_org_row(org_id=org_id, tier=PlanTier.PRO),
        ]

        mock_db = _mock_db_with_users(user_rows, org_rows)

        request = UserListRequest(tier=PlanTier.PRO, limit=10, offset=0)
        result = await service.list_users(mock_db, request)

        assert len(result.users) == 1
        assert result.users[0].tier == PlanTier.PRO

    @pytest.mark.asyncio
    async def test_no_users_returns_empty(self):
        """Should return empty list when no users exist."""
        mock_db = _mock_db_no_users()

        request = UserListRequest(limit=10, offset=0)
        result = await service.list_users(mock_db, request)

        assert result.total == 0
        assert len(result.users) == 0

    @pytest.mark.asyncio
    async def test_user_without_org_defaults_to_free(self):
        """Should default to FREE tier when user has no org."""
        user_id = uuid.uuid4()
        org_id = uuid.uuid4()
        user_rows = [
            _make_user_row(user_id=user_id, email="noorg@test.com", org_id=org_id),
        ]
        # Return None for org query
        org_rows = []

        mock_db = AsyncMock()

        # User query
        user_scalars = MagicMock()
        user_scalars.all.return_value = [_mock_user_orm(user_rows[0])]
        user_result = MagicMock()
        user_result.scalars.return_value = user_scalars

        # Org query returns None
        org_result = MagicMock()
        org_result.scalar_one_or_none.return_value = None

        call_count = {"count": 0}

        def execute_side_effect(query):
            call_count["count"] += 1
            # The total comes from db.scalar, so execute() starts with the
            # user query.
            if call_count["count"] == 1:
                return user_result
            return org_result

        mock_db.execute = AsyncMock(side_effect=execute_side_effect)
        mock_db.scalar = AsyncMock(return_value=1)

        request = UserListRequest(limit=10, offset=0)
        result = await service.list_users(mock_db, request)

        assert len(result.users) == 1
        assert result.users[0].tier == PlanTier.FREE


# ===========================================================================
# Feature Flags Tests
# ===========================================================================


class TestFeatureFlags:
    """Tests for feature flag management."""

    @pytest.mark.asyncio
    async def test_get_feature_flags_returns_empty(self):
        """Should return empty flags list (stub implementation)."""
        mock_db = AsyncMock()
        result = await service.get_feature_flags(mock_db)
        assert result.flags == []

    @pytest.mark.asyncio
    async def test_update_feature_flag_returns_flag(self):
        """Should return the updated flag (stub implementation)."""
        mock_db = AsyncMock()
        result = await service.update_feature_flag(
            mock_db, flag_key="test_feature", enabled=True, description="Test feature flag"
        )
        assert result.key == "test_feature"
        assert result.enabled is True
        assert result.description == "Test feature flag"

    @pytest.mark.asyncio
    async def test_update_feature_flag_without_description(self):
        """Should update flag without description."""
        mock_db = AsyncMock()
        result = await service.update_feature_flag(mock_db, flag_key="another_feature", enabled=False)
        assert result.key == "another_feature"
        assert result.enabled is False
        assert result.description is None


# ===========================================================================
# User Deactivation Tests
# ===========================================================================


class TestDeactivateUser:
    """Tests for deactivate_user service function."""

    @pytest.mark.asyncio
    async def test_deactivate_existing_user(self):
        """Should deactivate an active user."""
        user_id = uuid.uuid4()
        user_row = _make_user_row(user_id=user_id, is_active=True)
        mock_db = _mock_db_with_user_for_deactivation(user_row)

        await service.deactivate_user(mock_db, user_id)

        # Verify commit was called
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_deactivate_nonexistent_user_raises_404(self):
        """Should raise USER_NOT_FOUND when user doesn't exist."""
        user_id = uuid.uuid4()
        mock_db = _mock_db_with_user_for_deactivation(None)

        with pytest.raises(AppException) as exc_info:
            await service.deactivate_user(mock_db, user_id)

        assert exc_info.value.status_code == 404
        assert exc_info.value.code == "USER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_deactivate_already_inactive_user(self):
        """Should still work when user is already inactive."""
        user_id = uuid.uuid4()
        user_row = _make_user_row(user_id=user_id, is_active=False)
        mock_db = _mock_db_with_user_for_deactivation(user_row)

        await service.deactivate_user(mock_db, user_id)

        mock_db.commit.assert_called_once()
