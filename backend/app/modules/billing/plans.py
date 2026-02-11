"""
Plan definitions with limits for each pricing tier.

Pricing Tiers:
- Free: $0/mo -- 1 project, 5 AI generations/day
- Starter: $29/mo -- 5 projects, 50 AI generations/day
- Pro: $79/mo -- 25 projects, 200 AI generations/day
- Business: $199/mo -- unlimited projects, 500 AI generations/day
- Enterprise: $499+/mo -- custom
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.common import PlanTier


@dataclass(frozen=True)
class PlanLimits:
    """Resource limits for a given plan tier."""

    max_projects: int | None  # None means unlimited
    ai_generations_per_day: int
    features: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PlanDefinition:
    """Full definition of a billing plan."""

    tier: PlanTier
    name: str
    price_monthly: int  # cents
    description: str
    limits: PlanLimits
    stripe_price_env_key: str | None = None
    highlight: bool = False  # whether to highlight in the UI


PLAN_DEFINITIONS: dict[PlanTier, PlanDefinition] = {
    PlanTier.FREE: PlanDefinition(
        tier=PlanTier.FREE,
        name="Free",
        price_monthly=0,
        description="Get started with the basics",
        limits=PlanLimits(
            max_projects=1,
            ai_generations_per_day=5,
            features=[
                "1 project",
                "5 AI generations per day",
                "Community support",
                "Basic templates",
            ],
        ),
        stripe_price_env_key=None,
    ),
    PlanTier.STARTER: PlanDefinition(
        tier=PlanTier.STARTER,
        name="Starter",
        price_monthly=2900,
        description="Perfect for new authors",
        limits=PlanLimits(
            max_projects=5,
            ai_generations_per_day=50,
            features=[
                "5 projects",
                "50 AI generations per day",
                "Email support",
                "All templates",
                "KDP validation",
                "Basic analytics",
            ],
        ),
        stripe_price_env_key="STRIPE_PRICE_STARTER",
    ),
    PlanTier.PRO: PlanDefinition(
        tier=PlanTier.PRO,
        name="Pro",
        price_monthly=7900,
        description="For serious self-publishers",
        limits=PlanLimits(
            max_projects=25,
            ai_generations_per_day=200,
            features=[
                "25 projects",
                "200 AI generations per day",
                "Priority support",
                "All templates",
                "KDP validation",
                "Advanced analytics",
                "Competitor analysis",
                "Cover design AI",
                "Market intelligence",
            ],
        ),
        stripe_price_env_key="STRIPE_PRICE_PRO",
        highlight=True,
    ),
    PlanTier.BUSINESS: PlanDefinition(
        tier=PlanTier.BUSINESS,
        name="Business",
        price_monthly=19900,
        description="Scale your publishing business",
        limits=PlanLimits(
            max_projects=None,
            ai_generations_per_day=500,
            features=[
                "Unlimited projects",
                "500 AI generations per day",
                "Dedicated support",
                "All Pro features",
                "Team collaboration",
                "Custom branding",
                "API access",
                "Bulk operations",
            ],
        ),
        stripe_price_env_key="STRIPE_PRICE_BUSINESS",
    ),
    PlanTier.ENTERPRISE: PlanDefinition(
        tier=PlanTier.ENTERPRISE,
        name="Enterprise",
        price_monthly=49900,
        description="Custom solutions for large publishers",
        limits=PlanLimits(
            max_projects=None,
            ai_generations_per_day=9999,
            features=[
                "Unlimited projects",
                "Custom AI generation limits",
                "24/7 dedicated support",
                "All Business features",
                "SSO & SAML",
                "Custom integrations",
                "SLA guarantee",
                "On-premise option",
            ],
        ),
        stripe_price_env_key="STRIPE_PRICE_ENTERPRISE",
    ),
}


def get_plan(tier: PlanTier) -> PlanDefinition:
    """Get the plan definition for a given tier."""
    return PLAN_DEFINITIONS[tier]


def get_plan_limits(tier: PlanTier) -> PlanLimits:
    """Get the resource limits for a given tier."""
    return PLAN_DEFINITIONS[tier].limits


def get_all_plans() -> list[PlanDefinition]:
    """Return all plan definitions ordered by price."""
    return sorted(PLAN_DEFINITIONS.values(), key=lambda p: p.price_monthly)


def is_upgrade(current: PlanTier, target: PlanTier) -> bool:
    """Check whether moving from current to target is an upgrade."""
    order = [PlanTier.FREE, PlanTier.STARTER, PlanTier.PRO, PlanTier.BUSINESS, PlanTier.ENTERPRISE]
    return order.index(target) > order.index(current)
