"""Admin service -- platform administration and user management."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.organization import Organization
from app.models.user import User
from app.modules.admin.schemas import (
    FeatureFlag,
    FeatureFlagsResponse,
    UserListItem,
    UserListRequest,
    UserListResponse,
)
from shared.types.enums import PlanTier

logger = logging.getLogger(__name__)


async def list_users(
    db: AsyncSession,
    request: UserListRequest,
) -> UserListResponse:
    """List all users with optional filtering.

    Args:
        db: Database session
        request: Filter and pagination parameters

    Returns:
        UserListResponse containing users and total count
    """
    query = select(User)

    if request.search:
        search_term = f"%{request.search}%"
        query = query.where(
            (User.email.ilike(search_term)) | (User.name.ilike(search_term))
        )

    if request.tier:
        # Join with organization to filter by tier
        query = query.join(Organization).where(Organization.tier == request.tier)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Apply pagination
    query = query.limit(request.limit).offset(request.offset).order_by(User.created_at.desc())

    result = await db.execute(query)
    users = result.scalars().all()

    # Build response
    user_items = []
    for user in users:
        # Get user's organization to determine tier
        org_query = select(Organization).where(Organization.id == user.organization_id)
        org_result = await db.execute(org_query)
        org = org_result.scalar_one_or_none()

        user_items.append(
            UserListItem(
                id=user.id,
                email=user.email,
                name=user.name,
                created_at=user.created_at,
                tier=org.tier if org else PlanTier.FREE,
                is_active=user.is_active,
            )
        )

    return UserListResponse(users=user_items, total=total)


async def get_feature_flags(db: AsyncSession) -> FeatureFlagsResponse:
    """Get all feature flags.

    Args:
        db: Database session

    Returns:
        FeatureFlagsResponse containing all flags

    Note:
        This is a stub implementation. Feature flags would typically be stored
        in the database or a dedicated feature flag service.
    """
    # Placeholder: return empty list
    return FeatureFlagsResponse(flags=[])


async def update_feature_flag(
    db: AsyncSession,
    flag_key: str,
    enabled: bool,
    description: str | None = None,
) -> FeatureFlag:
    """Update a feature flag.

    Args:
        db: Database session
        flag_key: Flag identifier
        enabled: Whether flag is enabled
        description: Optional description

    Returns:
        Updated FeatureFlag

    Note:
        This is a stub implementation. Feature flags would typically be stored
        in the database or a dedicated feature flag service.
    """
    # Placeholder: return the flag as-is
    return FeatureFlag(key=flag_key, enabled=enabled, description=description)


async def deactivate_user(db: AsyncSession, user_id: UUID) -> None:
    """Deactivate a user account.

    Args:
        db: Database session
        user_id: User ID to deactivate

    Raises:
        AppException: If user not found
    """
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise AppException(status_code=404, code="USER_NOT_FOUND", message="User not found")

    user.is_active = False
    await db.commit()
    logger.info(f"Deactivated user {user_id}")
