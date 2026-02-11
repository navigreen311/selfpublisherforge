"""Unit tests for tier-based module access control.

Tests the `require_module` dependency factory and tier gating logic.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone

from fastapi import HTTPException

from app.core.tier_guard import require_module, _get_org_tier
from app.models.organization import Organization, PlanTier
from shared.contracts.module_registry import get_module


# ---------------------------------------------------------------------------
# Test _get_org_tier helper
# ---------------------------------------------------------------------------


class TestGetOrgTier:
    """Tests for the _get_org_tier internal helper."""

    @pytest.mark.asyncio
    async def test_get_org_tier_success(self, db_session):
        """Should return the organization's plan tier."""
        org_id = uuid4()
        org = Organization(
            id=org_id,
            name="TestOrg",
            slug=f"testorg-{str(org_id)[:8]}",
            plan_tier=PlanTier.PRO,
        )
        db_session.add(org)
        await db_session.flush()

        tier = await _get_org_tier(db_session, org_id)
        assert tier == PlanTier.PRO

    @pytest.mark.asyncio
    async def test_get_org_tier_not_found(self, db_session):
        """Should raise 404 if organization not found."""
        fake_org_id = uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await _get_org_tier(db_session, fake_org_id)

        assert exc_info.value.status_code == 404
        assert "Organization not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_org_tier_soft_deleted(self, db_session):
        """Should raise 404 if organization is soft-deleted."""
        org_id = uuid4()
        org = Organization(
            id=org_id,
            name="DeletedOrg",
            slug=f"deletedorg-{str(org_id)[:8]}",
            plan_tier=PlanTier.FREE,
            deleted_at=datetime.now(timezone.utc),
        )
        db_session.add(org)
        await db_session.flush()

        with pytest.raises(HTTPException) as exc_info:
            await _get_org_tier(db_session, org_id)

        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Test require_module dependency factory
# ---------------------------------------------------------------------------


class TestRequireModule:
    """Tests for the require_module dependency factory."""

    def test_require_module_invalid_slug(self):
        """Should raise ValueError if module slug doesn't exist in registry."""
        with pytest.raises(ValueError) as exc_info:
            require_module("nonexistent-module")

        assert "Unknown module slug: nonexistent-module" in str(exc_info.value)

    def test_require_module_valid_slug(self):
        """Should successfully create a dependency for a valid module slug."""
        # All of these should exist in the module registry
        dep = require_module("competitor-finder")
        assert callable(dep)

        dep = require_module("ai-cover")
        assert callable(dep)

        dep = require_module("review-intelligence")
        assert callable(dep)

    @pytest.mark.asyncio
    async def test_tier_access_granted_exact_tier(self, db_session):
        """Should allow access when org tier matches module tier exactly."""
        org_id = uuid4()
        org = Organization(
            id=org_id,
            name="StarterOrg",
            slug=f"starterorg-{str(org_id)[:8]}",
            plan_tier=PlanTier.STARTER,
        )
        db_session.add(org)
        await db_session.flush()

        # competitor-finder requires STARTER tier
        dep = require_module("competitor-finder")
        current_user = {"user_id": uuid4(), "org_id": org_id}

        # Should not raise
        result = await dep(current_user=current_user, db=db_session)
        assert result == current_user

    @pytest.mark.asyncio
    async def test_tier_access_granted_higher_tier(self, db_session):
        """Should allow access when org tier is higher than module tier."""
        org_id = uuid4()
        org = Organization(
            id=org_id,
            name="ProOrg",
            slug=f"proorg-{str(org_id)[:8]}",
            plan_tier=PlanTier.PRO,
        )
        db_session.add(org)
        await db_session.flush()

        # competitor-finder requires STARTER tier, but PRO is higher
        dep = require_module("competitor-finder")
        current_user = {"user_id": uuid4(), "org_id": org_id}

        # Should not raise
        result = await dep(current_user=current_user, db=db_session)
        assert result == current_user

    @pytest.mark.asyncio
    async def test_tier_access_denied_lower_tier(self, db_session):
        """Should deny access when org tier is lower than module tier."""
        org_id = uuid4()
        org = Organization(
            id=org_id,
            name="FreeOrg",
            slug=f"freeorg-{str(org_id)[:8]}",
            plan_tier=PlanTier.FREE,
        )
        db_session.add(org)
        await db_session.flush()

        # competitor-finder requires STARTER tier
        dep = require_module("competitor-finder")
        current_user = {"user_id": uuid4(), "org_id": org_id}

        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=current_user, db=db_session)

        assert exc_info.value.status_code == 403
        assert "requires starter tier or higher" in exc_info.value.detail.lower()
        assert "current tier: free" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_tier_access_denied_no_org(self, db_session):
        """Should deny access when user has no organization."""
        dep = require_module("competitor-finder")
        current_user = {"user_id": uuid4(), "org_id": None}

        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=current_user, db=db_session)

        assert exc_info.value.status_code == 403
        assert "must belong to an organization" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_free_tier_module_access(self, db_session):
        """Should allow access to FREE tier modules for all users."""
        org_id = uuid4()
        org = Organization(
            id=org_id,
            name="FreeOrg",
            slug=f"freeorg-{str(org_id)[:8]}",
            plan_tier=PlanTier.FREE,
        )
        db_session.add(org)
        await db_session.flush()

        # notifications is a FREE tier module
        dep = require_module("notifications")
        current_user = {"user_id": uuid4(), "org_id": org_id}

        # Should not raise
        result = await dep(current_user=current_user, db=db_session)
        assert result == current_user

    @pytest.mark.asyncio
    async def test_pro_tier_module_access_denied(self, db_session):
        """Should deny access to PRO modules for STARTER tier orgs."""
        org_id = uuid4()
        org = Organization(
            id=org_id,
            name="StarterOrg",
            slug=f"starterorg-{str(org_id)[:8]}",
            plan_tier=PlanTier.STARTER,
        )
        db_session.add(org)
        await db_session.flush()

        # ai-cover requires PRO tier
        dep = require_module("ai-cover")
        current_user = {"user_id": uuid4(), "org_id": org_id}

        with pytest.raises(HTTPException) as exc_info:
            await dep(current_user=current_user, db=db_session)

        assert exc_info.value.status_code == 403
        assert "requires pro tier or higher" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_enterprise_tier_access_all(self, db_session):
        """ENTERPRISE tier should have access to all modules."""
        org_id = uuid4()
        org = Organization(
            id=org_id,
            name="EnterpriseOrg",
            slug=f"enterpriseorg-{str(org_id)[:8]}",
            plan_tier=PlanTier.ENTERPRISE,
        )
        db_session.add(org)
        await db_session.flush()

        current_user = {"user_id": uuid4(), "org_id": org_id}

        # Test a few modules across different tiers
        for module_slug in ["notifications", "competitor-finder", "ai-cover", "admin"]:
            dep = require_module(module_slug)
            result = await dep(current_user=current_user, db=db_session)
            assert result == current_user


# ---------------------------------------------------------------------------
# Module registry validation
# ---------------------------------------------------------------------------


class TestModuleRegistryCompleteness:
    """Verify all required modules exist in the registry."""

    def test_required_modules_exist(self):
        """All task-specified modules should exist in the registry."""
        required_modules = [
            ("ai-cover", PlanTier.PRO),  # cover-design
            ("review-intelligence", PlanTier.STARTER),
            ("competitor-finder", PlanTier.STARTER),
            ("style-profiles", PlanTier.FREE),
            ("pricing-automation", PlanTier.STARTER),
            ("portfolio-economics", PlanTier.PRO),
            ("notifications", PlanTier.FREE),
            ("publishing-validation", PlanTier.STARTER),  # kdp-validation
        ]

        for slug, expected_tier in required_modules:
            module = get_module(slug)
            assert module.slug == slug
            assert module.tier == expected_tier
