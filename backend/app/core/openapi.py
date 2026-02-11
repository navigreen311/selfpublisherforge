"""Custom OpenAPI schema generation for SelfPublisherForge.

Provides a factory function that returns a tailored OpenAPI schema with:
- Descriptive title, version, and overview
- Tag metadata for every API module (grouped by tier)
- Bearer JWT security scheme applied globally

Usage from ``main.py``::

    from app.core.openapi import custom_openapi_schema

    app = FastAPI(...)
    app.openapi = custom_openapi_schema(app)
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from fastapi.openapi.utils import get_openapi

if TYPE_CHECKING:
    from fastapi import FastAPI

# ---------------------------------------------------------------------------
# API metadata
# ---------------------------------------------------------------------------

API_TITLE = "SelfPublisherForge API"
API_VERSION = "1.0.0"
API_DESCRIPTION = """\
**SelfPublisherForge** is an AI-powered self-publishing platform that covers \
the entire book lifecycle -- from market research and writing through \
production, launch, advertising, and long-term growth analytics.

## Module overview

| Tier | Modules | Purpose |
|------|---------|---------|
| **0 -- Foundation** | auth, users, billing, storage, notifications, realtime | Identity, \
payments, file storage, real-time events |
| **1-2 -- Data & Creation** | llm, market, knowledge, writing, style | LLM orchestration, \
market intelligence, knowledge vault, AI writing studio, style cloning |
| **3 -- Production** | pipelines, publishing, kdp-validation | Manuscript production \
pipeline, multi-platform publishing, KDP validation |
| **4 -- Optimization** | product-page, pricing, competitors | A/B product-page \
testing, dynamic pricing, competitor tracking |
| **5 -- Growth** | marketing, advertising, reviews, analytics | Launch campaigns, \
ad management, review monitoring, revenue analytics |
| **6-8 -- Intelligence & Scale** | agents, portfolio, audience, seasonal, covers, chrome-extension | \
Autonomous agents, portfolio economics, audience building, seasonal planning, cover design, browser extension |

## Authentication

All endpoints (except health checks and billing plan listings) require a \
**Bearer JWT** token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Obtain tokens via `POST /api/v1/auth/login` or `POST /api/v1/auth/register`. \
Refresh with `POST /api/v1/auth/refresh`.
"""

# ---------------------------------------------------------------------------
# Tag metadata -- order here controls display order in Swagger UI / ReDoc
# ---------------------------------------------------------------------------

TAGS_METADATA: list[dict[str, Any]] = [
    # Health
    {
        "name": "health",
        "description": "Service health and readiness probes.",
    },
    # Tier 0: Foundation
    {
        "name": "auth",
        "description": "Authentication -- registration, login, logout, password reset, email verification, MFA, and OAuth (Google / GitHub).",
    },
    {
        "name": "users",
        "description": "User profile and organization management.",
    },
    {
        "name": "billing",
        "description": "Billing plans, Stripe checkout, subscription management, invoices, and usage stats.",
    },
    {
        "name": "storage",
        "description": "File storage -- pre-signed S3 upload/download URLs and asset management.",
    },
    {
        "name": "notifications",
        "description": "In-app and email notification management.",
    },
    {
        "name": "realtime",
        "description": "WebSocket real-time event streaming.",
    },
    # Tier 1-2: Data & Creation
    {
        "name": "llm",
        "description": "LLM orchestration -- model selection, prompt execution, and token-usage tracking.",
    },
    {
        "name": "market",
        "description": "Market Intelligence Engine -- category browsing, keyword research, niche analysis, competitor tracking, and trend data.",
    },
    {
        "name": "knowledge",
        "description": "Knowledge Vault -- CRUD, semantic search, import, tags, and AI summaries for research notes and references.",
    },
    {
        "name": "writing",
        "description": "AI Writing Studio -- AI content generation (streaming), manuscript/chapter CRUD, outlines, readability analysis, and writing sessions.",
    },
    {
        "name": "style",
        "description": "Style Cloning -- author voice profiles for consistent AI-generated prose.",
    },
    # Tier 3: Production
    {
        "name": "pipelines",
        "description": "Production Pipeline -- manuscript formatting, EPUB/PDF export orchestration, and stage tracking.",
    },
    {
        "name": "publishing",
        "description": "Publishing Operations Center -- platform account connections, listing management, book metadata, and export to EPUB/PDF.",
    },
    {
        "name": "kdp-validation",
        "description": "KDP Validation -- pre-flight checks for Amazon Kindle Direct Publishing compliance.",
    },
    # Tier 4: Optimization
    {
        "name": "product-page",
        "description": "Product Page Lab -- A/B test titles, descriptions, and keywords for marketplace listings.",
    },
    {
        "name": "pricing",
        "description": "Pricing Automation -- dynamic price recommendations and rule-based adjustments.",
    },
    {
        "name": "competitors",
        "description": "Competitor Finder -- discover and track competing titles by ASIN, category, or keyword.",
    },
    # Tier 5: Growth
    {
        "name": "marketing",
        "description": "Marketing & Launch Command -- launch plans, email sequences, social media content, and ARC campaigns.",
    },
    {
        "name": "advertising",
        "description": "Advertising Intelligence -- Amazon Ads and Facebook Ads campaign management, bid optimization, creative generation, and performance dashboards.",
    },
    {
        "name": "reviews",
        "description": "Review Intelligence -- monitor, analyze, and respond to reader reviews across platforms.",
    },
    {
        "name": "analytics",
        "description": "Analytics & BI -- revenue dashboards, royalty imports, portfolio metrics, report generation, event tracking, and trend analysis.",
    },
    # Tier 6-8: Intelligence & Scale
    {
        "name": "agents",
        "description": "AI Agent System -- autonomous task execution with governance, budgets, approvals, and audit logs.",
    },
    {
        "name": "portfolio",
        "description": "Portfolio Economics -- cross-book financial modeling, ROI tracking, and investment analysis.",
    },
    {
        "name": "audience",
        "description": "Audience Building -- reader segmentation, mailing-list analytics, and engagement scoring.",
    },
    {
        "name": "seasonal",
        "description": "Seasonal Planning -- calendar-driven promotion scheduling and seasonal trend forecasts.",
    },
    {
        "name": "covers",
        "description": "Cover Design -- AI-assisted cover generation and design brief management.",
    },
    {
        "name": "chrome-extension",
        "description": "Chrome Extension -- browser-extension API for on-page market research and data capture.",
    },
]

# ---------------------------------------------------------------------------
# Security scheme
# ---------------------------------------------------------------------------

_SECURITY_SCHEMES: dict[str, Any] = {
    "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": (
            "JWT access token obtained from `POST /api/v1/auth/login` or "
            "`POST /api/v1/auth/register`.  Pass as: "
            "`Authorization: Bearer <token>`"
        ),
    },
}


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def custom_openapi_schema(app: FastAPI) -> Callable[[], dict[str, Any]]:
    """Return a zero-arg callable that lazily builds and caches the OpenAPI schema.

    Assign the return value directly to ``app.openapi``::

        app.openapi = custom_openapi_schema(app)

    The first call generates the schema; subsequent calls return the cached
    version (standard FastAPI behaviour).
    """

    def openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=API_TITLE,
            version=API_VERSION,
            description=API_DESCRIPTION,
            routes=app.routes,
            tags=TAGS_METADATA,
        )

        # Inject security schemes into components
        components = schema.setdefault("components", {})
        components.setdefault("securitySchemes", {}).update(_SECURITY_SCHEMES)

        # Apply BearerAuth globally (individual routes can override)
        schema["security"] = [{"BearerAuth": []}]

        app.openapi_schema = schema
        return app.openapi_schema

    return openapi
