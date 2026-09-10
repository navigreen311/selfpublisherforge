"""Tier-based access control middleware for module gating.

Provides FastAPI dependencies that verify an organization's subscription tier
has access to a requested module based on module tier requirements.

Usage::

    from app.core.tier_guard import require_module

    @router.get("/competitors/analyze")
    async def analyze(user=Depends(require_module("competitor-finder"))):
        ...
"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.organization import Organization
from app.schemas.common import PlanTier

# ---- Simple module tier registry ----
# Maps module slugs to the minimum tier required.
_TIER_ORDER = [PlanTier.FREE, PlanTier.STARTER, PlanTier.PRO, PlanTier.BUSINESS, PlanTier.ENTERPRISE]

MODULE_TIERS: dict[str, PlanTier] = {
    "admin": PlanTier.FREE,  # all tiers can reach admin (role check happens inside)
    "settings": PlanTier.FREE,
    "agents": PlanTier.FREE,
    "notifications": PlanTier.FREE,
    "market-intelligence": PlanTier.FREE,
    "knowledge-vault": PlanTier.FREE,
    "ai-writing": PlanTier.FREE,
    "style-cloning": PlanTier.STARTER,
    "production-pipeline": PlanTier.STARTER,
    "publishing-ops": PlanTier.STARTER,
    "kdp-validation": PlanTier.STARTER,
    "product-page": PlanTier.PRO,
    "pricing-automation": PlanTier.PRO,
    "competitor-finder": PlanTier.PRO,
    "marketing": PlanTier.PRO,
    "advertising": PlanTier.PRO,
    "review-intelligence": PlanTier.PRO,
    "analytics": PlanTier.BUSINESS,
    "portfolio-economics": PlanTier.BUSINESS,
    "cover-design": PlanTier.BUSINESS,
    "chrome-extension": PlanTier.ENTERPRISE,
}


def _tier_includes(org_tier: PlanTier, required_tier: PlanTier) -> bool:
    """Return True if org_tier >= required_tier in the tier hierarchy."""
    try:
        return _TIER_ORDER.index(org_tier) >= _TIER_ORDER.index(required_tier)
    except ValueError:
        return False


async def _get_org_tier(
    db: AsyncSession,
    org_id: UUID,
) -> PlanTier:
    """Fetch the organization's current plan tier."""
    result = await db.execute(
        select(Organization.plan_tier).where(Organization.id == org_id, Organization.deleted_at.is_(None))
    )
    tier = result.scalar_one_or_none()

    if tier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    # Convert string to PlanTier if needed
    if isinstance(tier, str):
        try:
            return PlanTier(tier)
        except ValueError:
            return PlanTier.FREE
    return tier


def require_module(module_slug: str) -> Callable:
    """Create a FastAPI dependency that enforces module access based on tier.

    Args:
        module_slug: The module slug (e.g., "competitor-finder")

    Returns:
        A FastAPI dependency function

    Raises:
        ValueError: If the slug is not in MODULE_TIERS. Defaulting an unknown
            slug to FREE would let a typo in a router quietly open a paid
            module to every tier, so this fails loudly at import time.
    """
    if module_slug not in MODULE_TIERS:
        raise ValueError(f"Unknown module slug: {module_slug}")
    required_tier = MODULE_TIERS[module_slug]

    async def _tier_checker(
        current_user: dict = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> dict:
        """Inner dependency that checks tier access."""
        org_id = current_user.get("org_id")

        if org_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must belong to an organization to access this module",
            )

        org_tier = await _get_org_tier(db, org_id)

        if not _tier_includes(org_tier, required_tier):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Module '{module_slug}' requires {required_tier.value} tier or higher. "
                    f"Current tier: {org_tier.value}"
                ),
            )

        return current_user

    return _tier_checker
