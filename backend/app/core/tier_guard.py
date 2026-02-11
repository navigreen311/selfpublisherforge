"""Tier-based access control middleware for module gating.

Provides FastAPI dependencies that verify an organization's subscription tier
has access to a requested module based on the module registry.

Usage::

    from app.core.tier_guard import require_module

    @router.get("/competitors/analyze")
    async def analyze(user=Depends(require_module("competitor-finder"))):
        ...
"""

from __future__ import annotations

from typing import Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.organization import Organization
from shared.contracts.module_registry import get_module, modules_for_tier
from shared.types.enums import PlanTier


async def _get_org_tier(
    db: AsyncSession,
    org_id: UUID,
) -> PlanTier:
    """Fetch the organization's current plan tier.

    Args:
        db: Database session
        org_id: Organization ID

    Returns:
        The organization's plan tier

    Raises:
        HTTPException(404): If organization not found
    """
    result = await db.execute(
        select(Organization.plan_tier)
        .where(Organization.id == org_id, Organization.deleted_at.is_(None))
    )
    tier = result.scalar_one_or_none()

    if tier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return tier


def require_module(module_slug: str) -> Callable:
    """Create a FastAPI dependency that enforces module access based on tier.

    Verifies that the user's organization has a subscription tier that includes
    access to the specified module. Returns 403 if access is denied.

    Args:
        module_slug: The module slug from the module registry (e.g., "competitor-finder")

    Returns:
        A FastAPI dependency function that can be used with Depends()

    Raises:
        KeyError: If module_slug is not found in the registry (at startup)

    Usage::

        @router.post("/analyze")
        async def endpoint(user=Depends(require_module("competitor-finder"))):
            org_id = user["org_id"]
            ...
    """
    # Validate module exists at dependency creation time (startup)
    try:
        module = get_module(module_slug)
    except KeyError:
        raise ValueError(f"Unknown module slug: {module_slug}")

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

        # Fetch org's current tier
        org_tier = await _get_org_tier(db, org_id)

        # Get all modules available to this tier
        available_modules = modules_for_tier(org_tier)
        available_slugs = {m.slug for m in available_modules}

        # Check if the requested module is in the available set
        if module_slug not in available_slugs:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Module '{module.name}' requires {module.tier.value} tier or higher. "
                    f"Current tier: {org_tier.value}"
                ),
            )

        return current_user

    return _tier_checker
