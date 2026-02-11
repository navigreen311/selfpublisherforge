"""Unit tests for tier-based module access control.

Tests the tier_guard module which enforces subscription tier requirements
for accessing different platform modules.
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tier_guard import require_module, _get_org_tier
from app.models.organization import Organization, PlanTier
from shared.types.enums import PlanTier as SharedPlanTier


# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def mock_org(db_session: AsyncSession):
    """Create a test organization with FREE tier."""
    org_id = uuid4()
    org = Organization(
        id=org_id,
        name="TestOrg",
        slug=f"testorg-{str(org_id)[:8]}",
        plan_tier=PlanTier.FREE,
    )
    db_session.add(org)
    await db_session.flush()
    return org


@pytest_asyncio.fixture
async def mock_org_starter(db_session: AsyncSession):
    """Create a test organization with STARTER tier."""
    org_id = uuid4()
    org = Organization(
        id=org_id,
        name="StarterOrg",
        slug=f"starterorg-{str(org_id)[:8]}",
        plan_tier=PlanTier.STARTER,
    )
    db_session.add(org)
    await db_session.flush()
    return org


@pytest_asyncio.fixture
async def mock_org_pro(db_session: AsyncSession):
    """Create a test organization with PRO tier."""
    org_id = uuid4()
    org = Organization(
        id=org_id,
        name="ProOrg",
        slug=f"proorg-{str(org_id)[:8]}",
        plan_tier=PlanTier.PRO,
    )
    db_session.add(org)
    await db_session.flush()
    return org


# ---------------------------------------------------------------------------
# Test _get_org_tier helper
# ---------------------------------------------------------------------------


class TestGetOrgTier:
    """Test the internal _get_org_tier function."""

    @pytest.mark.asyncio
    async def test_get_org_tier_success(self, db_session: AsyncSession, mock_org):
        """Should return the organization's tier."""
        tier = await _get_org_tier(db_session, mock_org.id)
        assert tier == PlanTier.FREE

    @pytest.mark.asyncio
    async def test_get_org_tier_not_found(self, db_session: AsyncSession):
        """Should raise 404 for non-existent organization."""
        fake_org_id = uuid4()
        with pytest.raises(HTTPException) as exc_info:
            await _get_org_tier(db_session, fake_org_id)
        assert exc_info.value.status_code == 404
        assert "Organization not found" in exc_info.value.detail


# ---------------------------------------------------------------------------
# Test require_module dependency factory
# ---------------------------------------------------------------------------


class TestRequireModule:
    """Test the require_module dependency factory."""

    def test_invalid_module_slug_raises_at_startup(self):
        """Should raise ValueError for unknown module slug at dependency creation."""
        with pytest.raises(ValueError) as exc_info:
            require_module("non-existent-module")
        assert "Unknown module slug" in str(exc_info.value)

    def test_valid_module_slug_creates_dependency(self):
        """Should successfully create a dependency for a valid module slug."""
        dependency = require_module("notifications")
        assert callable(dependency)


# ---------------------------------------------------------------------------
# Test tier access enforcement
# ---------------------------------------------------------------------------


class TestTierAccessEnforcement:
    """Test that the tier guard correctly allows/denies access based on tier."""

    @pytest.mark.asyncio
    async def test_free_tier_can_access_free_module(
        self, db_session: AsyncSession, mock_org
    ):
        """FREE tier should access FREE modules (notifications)."""
        current_user = {
            "user_id": uuid4(),
            "org_id": mock_org.id,
            "role": "owner",
        }

        # Create dependency and call it
        dependency = require_module("notifications")
        result = await dependency(current_user=current_user, db=db_session)

        assert result == current_user

    @pytest.mark.asyncio
    async def test_free_tier_denied_starter_module(
        self, db_session: AsyncSession, mock_org
    ):
        """FREE tier should be denied access to STARTER modules."""
        current_user = {
            "user_id": uuid4(),
            "org_id": mock_org.id,
            "role": "owner",
        }

        dependency = require_module("competitor-finder")
        with pytest.raises(HTTPException) as exc_info:
            await dependency(current_user=current_user, db=db_session)

        assert exc_info.value.status_code == 403
        assert "competitor-finder" in exc_info.value.detail.lower() or "Competitor Weakness Finder" in exc_info.value.detail
        assert "starter" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_starter_tier_can_access_free_module(
        self, db_session: AsyncSession, mock_org_starter
    ):
        """STARTER tier should access FREE modules (inheritance)."""
        current_user = {
            "user_id": uuid4(),
            "org_id": mock_org_starter.id,
            "role": "owner",
        }

        dependency = require_module("style-profiles")
        result = await dependency(current_user=current_user, db=db_session)

        assert result == current_user

    @pytest.mark.asyncio
    async def test_starter_tier_can_access_starter_module(
        self, db_session: AsyncSession, mock_org_starter
    ):
        """STARTER tier should access STARTER modules."""
        current_user = {
            "user_id": uuid4(),
            "org_id": mock_org_starter.id,
            "role": "owner",
        }

        dependency = require_module("review-intelligence")
        result = await dependency(current_user=current_user, db=db_session)

        assert result == current_user

    @pytest.mark.asyncio
    async def test_starter_tier_denied_pro_module(
        self, db_session: AsyncSession, mock_org_starter
    ):
        """STARTER tier should be denied access to PRO modules."""
        current_user = {
            "user_id": uuid4(),
            "org_id": mock_org_starter.id,
            "role": "owner",
        }

        dependency = require_module("ai-cover")
        with pytest.raises(HTTPException) as exc_info:
            await dependency(current_user=current_user, db=db_session)

        assert exc_info.value.status_code == 403
        assert "pro" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_pro_tier_can_access_all_lower_tiers(
        self, db_session: AsyncSession, mock_org_pro
    ):
        """PRO tier should access FREE, STARTER, and PRO modules."""
        current_user = {
            "user_id": uuid4(),
            "org_id": mock_org_pro.id,
            "role": "owner",
        }

        # Test FREE module
        dep_free = require_module("notifications")
        result = await dep_free(current_user=current_user, db=db_session)
        assert result == current_user

        # Test STARTER module
        dep_starter = require_module("pricing-automation")
        result = await dep_starter(current_user=current_user, db=db_session)
        assert result == current_user

        # Test PRO module
        dep_pro = require_module("portfolio-economics")
        result = await dep_pro(current_user=current_user, db=db_session)
        assert result == current_user

    @pytest.mark.asyncio
    async def test_user_without_org_denied(self, db_session: AsyncSession):
        """User without org_id should be denied access."""
        current_user = {
            "user_id": uuid4(),
            "org_id": None,
            "role": "viewer",
        }

        dependency = require_module("notifications")
        with pytest.raises(HTTPException) as exc_info:
            await dependency(current_user=current_user, db=db_session)

        assert exc_info.value.status_code == 403
        assert "belong to an organization" in exc_info.value.detail


# ---------------------------------------------------------------------------
# Test module registry integration
# ---------------------------------------------------------------------------


class TestModuleRegistryIntegration:
    """Test that tier guard properly integrates with the module registry."""

    @pytest.mark.asyncio
    async def test_all_new_modules_accessible_at_correct_tier(
        self, db_session: AsyncSession
    ):
        """Verify that all newly added modules are accessible at their declared tiers."""
        # Test review-intelligence (STARTER)
        org_starter_id = uuid4()
        org_starter = Organization(
            id=org_starter_id,
            name="StarterOrg",
            slug=f"starter-{str(org_starter_id)[:8]}",
            plan_tier=PlanTier.STARTER,
        )
        db_session.add(org_starter)
        await db_session.flush()

        current_user = {
            "user_id": uuid4(),
            "org_id": org_starter_id,
            "role": "owner",
        }

        # review-intelligence should work with STARTER
        dep = require_module("review-intelligence")
        result = await dep(current_user=current_user, db=db_session)
        assert result == current_user

        # Test portfolio-economics (PRO)
        org_pro_id = uuid4()
        org_pro = Organization(
            id=org_pro_id,
            name="ProOrg",
            slug=f"pro-{str(org_pro_id)[:8]}",
            plan_tier=PlanTier.PRO,
        )
        db_session.add(org_pro)
        await db_session.flush()

        current_user_pro = {
            "user_id": uuid4(),
            "org_id": org_pro_id,
            "role": "owner",
        }

        # portfolio-economics should work with PRO
        dep_pro = require_module("portfolio-economics")
        result = await dep_pro(current_user=current_user_pro, db=db_session)
        assert result == current_user_pro

    @pytest.mark.asyncio
    async def test_module_detail_in_error_message(
        self, db_session: AsyncSession, mock_org
    ):
        """Error message should include helpful module and tier information."""
        current_user = {
            "user_id": uuid4(),
            "org_id": mock_org.id,
            "role": "owner",
        }

        dependency = require_module("portfolio-economics")
        with pytest.raises(HTTPException) as exc_info:
            await dependency(current_user=current_user, db=db_session)

        # Should mention the module name or slug
        assert "portfolio" in exc_info.value.detail.lower() or "Portfolio Economics" in exc_info.value.detail
        # Should mention the required tier
        assert "pro" in exc_info.value.detail.lower()
        # Should mention the current tier
        assert "free" in exc_info.value.detail.lower()
