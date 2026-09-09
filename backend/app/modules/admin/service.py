"""Admin service -- platform administration and user management."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.organization import Organization
from app.models.project import Book
from app.models.user import User
from app.modules.admin.schemas import (
    ActivityLogFilters,
    ActivityLogResponse,
    AdminOrgDetail,
    AdminUserDetail,
    BillingOverview,
    FeatureFlag,
    FeatureFlagsResponse,
    InviteUserRequest,
    PlatformStatsResponse,
    UpdateOrgRequest,
    UpdateUserRequest,
    UserListItem,
    UserListRequest,
    UserListResponse,
)
from app.schemas.common import PlanTier

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


async def deactivate_user(db: AsyncSession, user_id: UUID) -> dict:
    """Deactivate a user account.

    Args:
        db: Database session
        user_id: User ID to deactivate

    Returns:
        Success message dict

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

    return {"message": f"User {user_id} deactivated successfully"}


# ---------------------------------------------------------------------------
# Platform Statistics
# ---------------------------------------------------------------------------

async def get_platform_stats(db: AsyncSession) -> PlatformStatsResponse:
    """Get platform-wide statistics.

    Args:
        db: Database session

    Returns:
        PlatformStatsResponse with aggregated statistics
    """
    # Count users
    users_total_query = select(func.count()).select_from(User)
    users_total = await db.scalar(users_total_query) or 0

    # Count active users (simplified - would need last_active tracking)
    users_active_query = select(func.count()).select_from(User).where(User.is_active == True)
    users_active_week = await db.scalar(users_active_query) or 0

    # Count organizations
    orgs_query = select(func.count()).select_from(Organization)
    organizations = await db.scalar(orgs_query) or 0

    # Count books
    books_query = select(func.count()).select_from(Book)
    books = await db.scalar(books_query) or 0

    # Mock data for AI tasks and tokens (would need dedicated tracking tables)
    ai_tasks_month = 0
    tokens_month = 0
    storage_used_bytes = 0
    monthly_revenue = 0.0

    return PlatformStatsResponse(
        users_total=users_total,
        users_active_week=users_active_week,
        organizations=organizations,
        books=books,
        ai_tasks_month=ai_tasks_month,
        tokens_month=tokens_month,
        storage_used_bytes=storage_used_bytes,
        monthly_revenue=monthly_revenue,
    )


# ---------------------------------------------------------------------------
# Activity Log
# ---------------------------------------------------------------------------

async def get_activity_log(
    db: AsyncSession,
    filters: ActivityLogFilters,
) -> ActivityLogResponse:
    """Get activity log with filtering.

    Args:
        db: Database session
        filters: Filter parameters

    Returns:
        ActivityLogResponse with filtered activities

    Note:
        This is a stub implementation. Activity logging would typically use
        a dedicated activity_log table or audit system.
    """
    # Return mock data for now
    activities = []
    total = 0

    return ActivityLogResponse(activities=activities, total=total)


# ---------------------------------------------------------------------------
# User Management
# ---------------------------------------------------------------------------

async def get_user_detail(db: AsyncSession, user_id: UUID) -> AdminUserDetail:
    """Get detailed user information.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        AdminUserDetail with user information and activity counts

    Raises:
        AppException: If user not found
    """
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise AppException(status_code=404, code="USER_NOT_FOUND", message="User not found")

    # Get organization
    org_query = select(Organization).where(Organization.id == user.organization_id)
    org_result = await db.execute(org_query)
    org = org_result.scalar_one_or_none()

    # Count user's books (via organization projects)
    books_count = 0
    manuscripts_count = 0

    return AdminUserDetail(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        status="active" if user.is_active else "inactive",
        org_id=user.organization_id,
        org_name=org.name if org else "Unknown",
        last_active=None,  # Would need tracking
        books_count=books_count,
        manuscripts_count=manuscripts_count,
        ai_tasks_count=0,  # Would need tracking
        permissions=[],  # Would need permission system
    )


async def invite_user(
    db: AsyncSession,
    org_id: UUID,
    data: InviteUserRequest,
) -> dict:
    """Invite a new user to an organization.

    Args:
        db: Database session
        org_id: Organization ID
        data: Invite request data

    Returns:
        Success message dict

    Note:
        This is a stub implementation. Real implementation would create
        an invitation record and send an email.
    """
    # Verify organization exists
    org_query = select(Organization).where(Organization.id == org_id)
    org_result = await db.execute(org_query)
    org = org_result.scalar_one_or_none()

    if not org:
        raise AppException(status_code=404, code="ORG_NOT_FOUND", message="Organization not found")

    logger.info(f"Creating invite for {data.email} to org {org_id} as {data.role}")

    return {"message": f"Invitation sent to {data.email}"}


async def update_user(
    db: AsyncSession,
    user_id: UUID,
    data: UpdateUserRequest,
) -> dict:
    """Update user settings.

    Args:
        db: Database session
        user_id: User ID
        data: Update request data

    Returns:
        Updated user data dict

    Raises:
        AppException: If user not found
    """
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise AppException(status_code=404, code="USER_NOT_FOUND", message="User not found")

    # Update fields
    if data.role is not None:
        user.role = data.role
    if data.status is not None:
        user.is_active = data.status == "active"

    await db.commit()
    await db.refresh(user)

    logger.info(f"Updated user {user_id}")

    return {"message": f"User {user_id} updated successfully"}


async def reset_user_password(db: AsyncSession, user_id: UUID) -> dict:
    """Reset a user's password.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Success message dict

    Raises:
        AppException: If user not found

    Note:
        This is a stub implementation. Real implementation would generate
        a password reset token and send an email.
    """
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise AppException(status_code=404, code="USER_NOT_FOUND", message="User not found")

    logger.info(f"Password reset initiated for user {user_id}")

    return {"message": f"Password reset email sent to {user.email}"}


# ---------------------------------------------------------------------------
# Organization Management
# ---------------------------------------------------------------------------

async def get_organizations(db: AsyncSession) -> list[AdminOrgDetail]:
    """Get all organizations with details.

    Args:
        db: Database session

    Returns:
        List of AdminOrgDetail
    """
    query = select(Organization).order_by(Organization.created_at.desc())
    result = await db.execute(query)
    orgs = result.scalars().all()

    org_details = []
    for org in orgs:
        # Count members
        members_query = select(func.count()).select_from(User).where(User.organization_id == org.id)
        member_count = await db.scalar(members_query) or 0

        # Count books
        books_count = 0

        # Get owner
        owner_query = select(User).where(
            User.organization_id == org.id,
            User.role.in_(["owner", "admin"])
        ).limit(1)
        owner_result = await db.execute(owner_query)
        owner = owner_result.scalar_one_or_none()

        org_details.append(
            AdminOrgDetail(
                id=org.id,
                name=org.name,
                slug=org.slug,
                plan_tier=org.tier.value if hasattr(org, 'tier') else "free",
                owner_name=owner.name if owner else "Unknown",
                member_count=member_count,
                books_count=books_count,
                storage_used_bytes=0,
                storage_limit_bytes=1073741824,  # 1GB default
                feature_toggles={},
                created_at=org.created_at,
            )
        )

    return org_details


async def get_org_detail(db: AsyncSession, org_id: UUID) -> AdminOrgDetail:
    """Get detailed organization information.

    Args:
        db: Database session
        org_id: Organization ID

    Returns:
        AdminOrgDetail with organization details

    Raises:
        AppException: If organization not found
    """
    query = select(Organization).where(Organization.id == org_id)
    result = await db.execute(query)
    org = result.scalar_one_or_none()

    if not org:
        raise AppException(status_code=404, code="ORG_NOT_FOUND", message="Organization not found")

    # Count members
    members_query = select(func.count()).select_from(User).where(User.organization_id == org.id)
    member_count = await db.scalar(members_query) or 0

    # Count books
    books_count = 0

    # Get owner
    owner_query = select(User).where(
        User.organization_id == org.id,
        User.role.in_(["owner", "admin"])
    ).limit(1)
    owner_result = await db.execute(owner_query)
    owner = owner_result.scalar_one_or_none()

    return AdminOrgDetail(
        id=org.id,
        name=org.name,
        slug=org.slug,
        plan_tier=org.tier.value if hasattr(org, 'tier') else "free",
        owner_name=owner.name if owner else "Unknown",
        member_count=member_count,
        books_count=books_count,
        storage_used_bytes=0,
        storage_limit_bytes=1073741824,  # 1GB default
        feature_toggles={},
        created_at=org.created_at,
    )


async def update_org(
    db: AsyncSession,
    org_id: UUID,
    data: UpdateOrgRequest,
) -> dict:
    """Update organization settings.

    Args:
        db: Database session
        org_id: Organization ID
        data: Update request data

    Returns:
        Success message dict

    Raises:
        AppException: If organization not found
    """
    query = select(Organization).where(Organization.id == org_id)
    result = await db.execute(query)
    org = result.scalar_one_or_none()

    if not org:
        raise AppException(status_code=404, code="ORG_NOT_FOUND", message="Organization not found")

    # Update fields
    if data.name is not None:
        org.name = data.name

    await db.commit()
    await db.refresh(org)

    logger.info(f"Updated organization {org_id}")

    return {"message": f"Organization {org_id} updated successfully"}


# ---------------------------------------------------------------------------
# Billing
# ---------------------------------------------------------------------------

async def get_billing_overview(db: AsyncSession, org_id: UUID) -> BillingOverview:
    """Get billing overview for an organization.

    Args:
        db: Database session
        org_id: Organization ID

    Returns:
        BillingOverview with plan and invoice information

    Raises:
        AppException: If organization not found

    Note:
        This is a stub implementation. Real implementation would integrate
        with a billing service like Stripe.
    """
    query = select(Organization).where(Organization.id == org_id)
    result = await db.execute(query)
    org = result.scalar_one_or_none()

    if not org:
        raise AppException(status_code=404, code="ORG_NOT_FOUND", message="Organization not found")

    plan_tier = org.tier.value if hasattr(org, 'tier') else "free"
    plan_prices = {
        "free": 0.0,
        "starter": 29.0,
        "professional": 99.0,
        "enterprise": 299.0,
    }

    return BillingOverview(
        plan_name=plan_tier.capitalize(),
        plan_price=plan_prices.get(plan_tier, 0.0),
        next_billing=None,
        usage={},
        invoices=[],
    )


async def get_billing_usage(db: AsyncSession, org_id: UUID) -> dict:
    """Get billing usage for an organization.

    Args:
        db: Database session
        org_id: Organization ID

    Returns:
        Usage information dict

    Raises:
        AppException: If organization not found

    Note:
        This is a stub implementation. Real implementation would track
        actual resource usage.
    """
    query = select(Organization).where(Organization.id == org_id)
    result = await db.execute(query)
    org = result.scalar_one_or_none()

    if not org:
        raise AppException(status_code=404, code="ORG_NOT_FOUND", message="Organization not found")

    return {
        "storage": {"used": 0, "limit": 1073741824, "percentage": 0},
        "api_calls": {"used": 0, "limit": 10000, "percentage": 0},
        "ai_tokens": {"used": 0, "limit": 1000000, "percentage": 0},
    }
