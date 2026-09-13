"""Seed demo users and organizations."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.organization import Organization, PlanTier, SubscriptionStatus
from app.models.user import User, UserRole


async def seed_users(db: AsyncSession) -> dict[str, uuid.UUID]:
    """Seed demo users with organizations and subscriptions.

    Returns a dict mapping email -> user_id for use in other seed scripts.
    """
    users_data = [
        {
            "email": "admin@selfpublisherforge.com",
            "password": "admin123",
            "name": "Admin User",
            "role": UserRole.OWNER,
            "org_name": "SelfPublisherForge Admin",
            "org_slug": "spf-admin",
            "plan_tier": PlanTier.ENTERPRISE,
        },
        {
            "email": "jane@example.com",
            "password": "demo123",
            "name": "Jane Doe",
            "role": UserRole.OWNER,
            "org_name": "Jane's Publishing House",
            "org_slug": "janes-publishing",
            "plan_tier": PlanTier.PRO,
        },
        {
            "email": "bob@example.com",
            "password": "demo123",
            "name": "Bob Smith",
            "role": UserRole.OWNER,
            "org_name": "Bob's Books",
            "org_slug": "bobs-books",
            "plan_tier": PlanTier.STARTER,
        },
        {
            "email": "alice@example.com",
            "password": "demo123",
            "name": "Alice Johnson",
            "role": UserRole.OWNER,
            "org_name": "Alice's Adventures",
            "org_slug": "alices-adventures",
            "plan_tier": PlanTier.FREE,
        },
    ]

    user_map = {}
    org_map = {}

    for user_data in users_data:
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == user_data["email"]))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            user_map[user_data["email"]] = existing_user.id
            org_map[user_data["email"]] = existing_user.org_id
            continue

        # Create organization first
        org = Organization(
            name=user_data["org_name"],
            slug=user_data["org_slug"],
            plan_tier=user_data["plan_tier"],
            subscription_status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.now(UTC),
            current_period_end=datetime.now(UTC) + timedelta(days=30),
            settings={
                "notifications_enabled": True,
                "ai_features_enabled": True,
            },
            limits={
                "max_projects": 100 if user_data["plan_tier"] == PlanTier.PRO else 10,
                "max_books": 500 if user_data["plan_tier"] == PlanTier.PRO else 50,
                "ai_credits_monthly": 10000 if user_data["plan_tier"] == PlanTier.PRO else 1000,
            },
        )
        db.add(org)
        await db.flush()

        # Create user
        user = User(
            org_id=org.id,
            email=user_data["email"],
            password_hash=hash_password(user_data["password"]),
            name=user_data["name"],
            role=user_data["role"],
            is_active=True,
            email_verified=True,
            email_verified_at=datetime.now(UTC),
            preferences={
                "theme": "light",
                "notifications": {
                    "email": True,
                    "in_app": True,
                },
            },
        )
        db.add(user)
        await db.flush()

        user_map[user_data["email"]] = user.id
        org_map[user_data["email"]] = org.id

    await db.commit()

    print(f"✓ Seeded {len(user_map)} users and organizations")

    return {"users": user_map, "orgs": org_map}
