"""Registry of all 35 platform modules with metadata.

Each entry captures:
* **name** -- human-readable module name
* **slug** -- URL/package slug (kebab-case)
* **tier** -- minimum ``PlanTier`` required
* **api_prefix** -- REST API route prefix under ``/api/v1``
* **dependencies** -- slugs of other modules this one depends on
* **description** -- one-liner about the module's responsibility

Usage::

    from shared.contracts.module_registry import MODULE_REGISTRY, get_module

    auth = get_module("auth")
    print(auth.api_prefix)  # "/auth"

    for mod in modules_for_tier("free"):
        print(mod.name)

NOTE: This registry declares 33 logical modules, but not all are implemented as
standalone backend modules. Some entries represent sub-features or endpoints that
are covered by other implementations. See inline comments for the actual module
mappings.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.types.enums import PlanTier


@dataclass(frozen=True)
class ModuleInfo:
    """Immutable descriptor for a platform module."""

    id: int
    slug: str
    name: str
    description: str
    tier: PlanTier
    api_prefix: str
    dependencies: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# The master list (ordered by numeric module ID)
# ---------------------------------------------------------------------------

MODULE_REGISTRY: tuple[ModuleInfo, ...] = (
    ModuleInfo(
        id=1,
        slug="auth",
        name="Authentication",
        description="User registration, login, JWT management, password reset.",
        tier=PlanTier.FREE,
        api_prefix="/auth",
        dependencies=(),
    ),
    ModuleInfo(
        id=2,
        slug="org",
        name="Organization & Teams",
        description="Multi-tenant org management, invitations, role assignment.",
        tier=PlanTier.FREE,
        api_prefix="/orgs",
        dependencies=("auth",),
    ),
    ModuleInfo(
        id=3,
        slug="projects",
        name="Projects",
        description="Create and manage book / series / course projects.",
        tier=PlanTier.FREE,
        api_prefix="/projects",
        dependencies=("auth", "org"),
    ),
    # Covered by ai_writing module in backend
    ModuleInfo(
        id=4,
        slug="books",
        name="Books & Manuscripts",
        description="Book metadata, chapters, manuscript content management.",
        tier=PlanTier.FREE,
        api_prefix="/books",
        dependencies=("auth", "org", "projects"),
    ),
    ModuleInfo(
        id=5,
        slug="market-research",
        name="Market Research",
        description="Category analysis, BSR tracking, demand/competition scoring.",
        tier=PlanTier.STARTER,
        api_prefix="/market-research",
        dependencies=("auth", "org"),
    ),
    # Covered by market_intelligence module in backend
    ModuleInfo(
        id=6,
        slug="keyword-research",
        name="Keyword Research",
        description="Keyword discovery, search volume estimation, relevance scoring.",
        tier=PlanTier.STARTER,
        api_prefix="/keywords",
        dependencies=("auth", "org", "market-research"),
    ),
    ModuleInfo(
        id=7,
        slug="style-profiles",
        name="Style Profiles",
        description="Writing tone, voice, audience, and genre style definitions.",
        tier=PlanTier.FREE,
        api_prefix="/style-profiles",
        dependencies=("auth", "org"),
    ),
    # Covered by style_cloning module in backend
    ModuleInfo(
        id=8,
        slug="brand-kits",
        name="Brand Kits",
        description="Visual identity: colors, fonts, logos for book branding.",
        tier=PlanTier.STARTER,
        api_prefix="/brand-kits",
        dependencies=("auth", "org"),
    ),
    # Covered by ai_writing module in backend
    ModuleInfo(
        id=9,
        slug="ai-outline",
        name="AI Outline Generator",
        description="Generate book outlines using LLM prompts and templates.",
        tier=PlanTier.STARTER,
        api_prefix="/ai/outlines",
        dependencies=("auth", "org", "books", "style-profiles"),
    ),
    ModuleInfo(
        id=10,
        slug="ai-writing",
        name="AI Writing Assistant",
        description="Chapter-level content generation and rewriting.",
        tier=PlanTier.PRO,
        api_prefix="/ai/writing",
        dependencies=("auth", "org", "books", "style-profiles"),
    ),
    # Covered by ai_writing module in backend
    ModuleInfo(
        id=11,
        slug="ai-editing",
        name="AI Editing & Proofreading",
        description="Grammar, style, and consistency checks powered by LLMs.",
        tier=PlanTier.PRO,
        api_prefix="/ai/editing",
        dependencies=("auth", "org", "books"),
    ),
    # Covered by cover_design module in backend
    ModuleInfo(
        id=12,
        slug="ai-cover",
        name="AI Cover Design",
        description="Generate book cover concepts and variations with AI.",
        tier=PlanTier.PRO,
        api_prefix="/ai/covers",
        dependencies=("auth", "org", "books", "brand-kits"),
    ),
    # Covered by publishing_ops module in backend
    ModuleInfo(
        id=13,
        slug="formatting",
        name="Book Formatting",
        description="Convert manuscripts to ebook, print-ready PDF, and audio.",
        tier=PlanTier.STARTER,
        api_prefix="/formatting",
        dependencies=("auth", "org", "books"),
    ),
    ModuleInfo(
        id=14,
        slug="publishing-validation",
        name="Publishing Validation",
        description="Pre-upload checks for KDP, IngramSpark, etc.",
        tier=PlanTier.STARTER,
        api_prefix="/publishing/validation",
        dependencies=("auth", "org", "books", "formatting"),
    ),
    ModuleInfo(
        id=15,
        slug="publishing-distribution",
        name="Publishing & Distribution",
        description="Upload to platforms, sync listings, manage accounts.",
        tier=PlanTier.PRO,
        api_prefix="/publishing/distribution",
        dependencies=("auth", "org", "books", "publishing-validation"),
    ),
    # Covered by marketing module in backend
    ModuleInfo(
        id=16,
        slug="email-marketing",
        name="Email Marketing",
        description="Email campaigns, newsletters, subscriber management.",
        tier=PlanTier.PRO,
        api_prefix="/marketing/email",
        dependencies=("auth", "org"),
    ),
    # Covered by marketing module in backend
    ModuleInfo(
        id=17,
        slug="social-marketing",
        name="Social Media Marketing",
        description="Social post scheduling, content calendar, engagement tracking.",
        tier=PlanTier.PRO,
        api_prefix="/marketing/social",
        dependencies=("auth", "org"),
    ),
    ModuleInfo(
        id=18,
        slug="ad-campaigns",
        name="Advertising Campaigns",
        description="Amazon Ads / Facebook Ads integration and management.",
        tier=PlanTier.BUSINESS,
        api_prefix="/marketing/ads",
        dependencies=("auth", "org", "books"),
    ),
    ModuleInfo(
        id=19,
        slug="agent-framework",
        name="Agent Framework",
        description="Core autonomous-agent runtime: task queue, budget, execution.",
        tier=PlanTier.PRO,
        api_prefix="/agents",
        dependencies=("auth", "org"),
    ),
    # Covered by agent_system module in backend
    ModuleInfo(
        id=20,
        slug="agent-marketplace",
        name="Agent Marketplace",
        description="Browse, install, and configure pre-built agent templates.",
        tier=PlanTier.PRO,
        api_prefix="/agents/marketplace",
        dependencies=("auth", "org", "agent-framework"),
    ),
    # Covered by agent_system module in backend
    ModuleInfo(
        id=21,
        slug="agent-builder",
        name="Agent Builder",
        description="Visual / low-code agent creation and customisation.",
        tier=PlanTier.BUSINESS,
        api_prefix="/agents/builder",
        dependencies=("auth", "org", "agent-framework"),
    ),
    # Covered by analytics module in backend
    ModuleInfo(
        id=22,
        slug="sales-analytics",
        name="Sales Analytics",
        description="Sales, royalties, and revenue dashboards per book/platform.",
        tier=PlanTier.STARTER,
        api_prefix="/analytics/sales",
        dependencies=("auth", "org", "books"),
    ),
    # Covered by analytics module in backend
    ModuleInfo(
        id=23,
        slug="marketing-analytics",
        name="Marketing Analytics",
        description="Campaign ROI, conversion funnels, A/B test results.",
        tier=PlanTier.PRO,
        api_prefix="/analytics/marketing",
        dependencies=("auth", "org", "email-marketing", "social-marketing"),
    ),
    # Covered by analytics module in backend
    ModuleInfo(
        id=24,
        slug="reports",
        name="Report Generator",
        description="Custom report builder with PDF/CSV export.",
        tier=PlanTier.PRO,
        api_prefix="/reports",
        dependencies=("auth", "org", "sales-analytics"),
    ),
    ModuleInfo(
        id=25,
        slug="notifications",
        name="Notifications",
        description="In-app, email, and push notification delivery.",
        tier=PlanTier.FREE,
        api_prefix="/notifications",
        dependencies=("auth",),
    ),
    # Covered by users module in backend
    ModuleInfo(
        id=26,
        slug="user-settings",
        name="User Settings",
        description="Preferences, theme, timezone, notification settings.",
        tier=PlanTier.FREE,
        api_prefix="/settings",
        dependencies=("auth",),
    ),
    ModuleInfo(
        id=27,
        slug="admin",
        name="Admin Panel",
        description="Platform administration: user management, feature flags.",
        tier=PlanTier.ENTERPRISE,
        api_prefix="/admin",
        dependencies=("auth", "org"),
    ),
    ModuleInfo(
        id=28,
        slug="billing",
        name="Billing & Subscriptions",
        description="Stripe integration, plan management, invoices.",
        tier=PlanTier.FREE,
        api_prefix="/billing",
        dependencies=("auth", "org"),
    ),
    # Covered by billing module in backend
    ModuleInfo(
        id=29,
        slug="usage-tracking",
        name="Usage Tracking",
        description="Metered usage: AI tokens, storage, API calls, agent tasks.",
        tier=PlanTier.FREE,
        api_prefix="/usage",
        dependencies=("auth", "org", "billing"),
    ),
    ModuleInfo(
        id=30,
        slug="review-intelligence",
        name="Review Intelligence",
        description="Amazon review analysis, sentiment tracking, weakness detection.",
        tier=PlanTier.STARTER,
        api_prefix="/review-intelligence",
        dependencies=("auth", "org", "books"),
    ),
    ModuleInfo(
        id=31,
        slug="competitor-finder",
        name="Competitor Weakness Finder",
        description="Identify competitor gaps, weaknesses, and market opportunities.",
        tier=PlanTier.STARTER,
        api_prefix="/competitors",
        dependencies=("auth", "org", "market-research"),
    ),
    ModuleInfo(
        id=32,
        slug="pricing-automation",
        name="Pricing Automation",
        description="Dynamic pricing strategies, A/B testing, competitor price tracking.",
        tier=PlanTier.STARTER,
        api_prefix="/pricing",
        dependencies=("auth", "org", "books", "market-research"),
    ),
    ModuleInfo(
        id=33,
        slug="portfolio-economics",
        name="Portfolio Economics",
        description="Multi-book portfolio analysis, ROI tracking, revenue projections.",
        tier=PlanTier.PRO,
        api_prefix="/portfolio",
        dependencies=("auth", "org", "books", "sales-analytics"),
    ),
    # VoiceForge Integration
    ModuleInfo(
        id=34,
        slug="audiobook",
        name="AI Audiobook Production Studio",
        description="Full audiobook creation pipeline with multi-provider TTS, SSML generation, ACX validation, and mastering.",
        tier=PlanTier.PRO,
        api_prefix="/audiobooks",
        dependencies=("auth", "org", "books"),
    ),
    ModuleInfo(
        id=35,
        slug="dictation",
        name="Voice-Driven Writing (Dictation)",
        description="Real-time speech-to-text dictation with punctuation restoration, filler removal, and style refinement.",
        tier=PlanTier.STARTER,
        api_prefix="/dictation",
        dependencies=("auth", "org", "style-profiles"),
    ),
)


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

_SLUG_INDEX: dict[str, ModuleInfo] = {m.slug: m for m in MODULE_REGISTRY}
_ID_INDEX: dict[int, ModuleInfo] = {m.id: m for m in MODULE_REGISTRY}


def get_module(slug: str) -> ModuleInfo:
    """Return a module by slug. Raises ``KeyError`` if not found."""
    return _SLUG_INDEX[slug]


def get_module_by_id(module_id: int) -> ModuleInfo:
    """Return a module by numeric ID. Raises ``KeyError`` if not found."""
    return _ID_INDEX[module_id]


def modules_for_tier(tier: PlanTier | str) -> list[ModuleInfo]:
    """Return all modules available to a given plan tier (inclusive).

    Higher tiers include all modules from lower tiers.
    """
    tier_value = PlanTier(tier) if isinstance(tier, str) else tier
    tier_order = list(PlanTier)
    max_index = tier_order.index(tier_value)
    allowed = set(tier_order[: max_index + 1])
    return [m for m in MODULE_REGISTRY if m.tier in allowed]


def module_dependency_graph() -> dict[str, list[str]]:
    """Return {slug: [dependency_slugs]} for all modules."""
    return {m.slug: list(m.dependencies) for m in MODULE_REGISTRY}
