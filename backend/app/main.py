import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.error_handler import register_error_handlers
from app.core.openapi import custom_openapi_schema
from app.database import init_db

logger = logging.getLogger(__name__)

settings = get_settings()

def _log_startup_config_warnings() -> None:
    """Log warnings/info about service configuration at startup."""
    s = get_settings()

    # --- Critical service credentials still using placeholders ---
    if s.AWS_ACCESS_KEY_ID == "YOUR_AWS_ACCESS_KEY_HERE" or s.AWS_SECRET_ACCESS_KEY == "YOUR_AWS_SECRET_KEY_HERE":
        logger.warning("S3/AWS credentials are still using placeholder values — file storage will not work")

    if s.STRIPE_SECRET_KEY == "YOUR_STRIPE_SECRET_KEY_HERE":
        logger.warning("Stripe secret key is a placeholder — billing will not work")

    if s.STRIPE_WEBHOOK_SECRET == "YOUR_STRIPE_WEBHOOK_SECRET_HERE":
        logger.warning("Stripe webhook secret is a placeholder — webhook verification will fail")

    # --- Email provider ---
    sendgrid_configured = s.SENDGRID_API_KEY != "YOUR_SENDGRID_API_KEY_HERE"
    smtp_configured = bool(s.SMTP_HOST and s.SMTP_USER)
    if not sendgrid_configured and not smtp_configured:
        logger.warning(
            "No email provider configured (neither SendGrid nor SMTP) — "
            "transactional emails will not be sent"
        )
    elif sendgrid_configured:
        logger.info("Email provider: SendGrid")
    else:
        logger.info("Email provider: SMTP (%s)", s.SMTP_HOST)

    # --- Optional integrations: configured vs not ---
    integrations = {
        "Google OAuth": bool(s.GOOGLE_CLIENT_ID and s.GOOGLE_CLIENT_SECRET),
        "GitHub OAuth": bool(s.GITHUB_CLIENT_ID and s.GITHUB_CLIENT_SECRET),
        "Stripe billing tiers": all([
            s.STRIPE_PRICE_STARTER, s.STRIPE_PRICE_PRO,
            s.STRIPE_PRICE_BUSINESS, s.STRIPE_PRICE_ENTERPRISE,
        ]),
        "Amazon Ads": bool(s.AMAZON_ADS_CLIENT_ID and s.AMAZON_ADS_CLIENT_SECRET),
        "Anthropic LLM": s.ANTHROPIC_API_KEY != "YOUR_ANTHROPIC_API_KEY_HERE",
        "OpenAI LLM": s.OPENAI_API_KEY != "YOUR_OPENAI_API_KEY_HERE",
    }

    configured = [name for name, ready in integrations.items() if ready]
    not_configured = [name for name, ready in integrations.items() if not ready]

    if configured:
        logger.info("Integrations configured: %s", ", ".join(configured))
    if not_configured:
        logger.info("Integrations NOT configured: %s", ", ".join(not_configured))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    _log_startup_config_warnings()
    yield
    # Shut down the WebSocket connection manager (cancels background tasks, closes Redis).
    from app.modules.realtime.router import manager as ws_manager
    await ws_manager.shutdown()

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="AI-powered self-publishing platform API for market research, writing, production, and growth.",
        version=settings.APP_VERSION,
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Error handlers
    register_error_handlers(app)

    # Health check
    @app.get("/health", summary="Health check", tags=["health"])
    @app.get(f"{settings.API_V1_PREFIX}/health", summary="Health check (prefixed)", tags=["health"])
    async def health():
        """Return service health status and version."""
        return {"status": "healthy", "version": settings.APP_VERSION}

    # Register module routers
    _register_routers(app)

    # Custom OpenAPI schema -- provides enhanced API documentation with:
    #   - Structured tag descriptions for all 22 module groups
    #   - BearerAuth security scheme applied globally
    #   - Rich API overview with tier-based module table
    app.openapi = custom_openapi_schema(app)

    return app

def _register_routers(app: FastAPI):
    """Register all module API routers."""
    prefix = settings.API_V1_PREFIX

    # Tier 0: Foundation
    from app.modules.auth.router import router as auth_router
    app.include_router(auth_router, prefix=f"{prefix}/auth", tags=["auth"])

    from app.modules.users.router import router as users_router
    app.include_router(users_router, prefix=prefix, tags=["users"])

    from app.modules.organization.router import router as organization_router
    app.include_router(organization_router, prefix=f"{prefix}/orgs", tags=["organization"])

    from app.modules.projects.router import router as projects_router
    app.include_router(projects_router, prefix=f"{prefix}/projects", tags=["projects"])

    from app.modules.billing.router import router as billing_router
    app.include_router(billing_router, prefix=f"{prefix}/billing", tags=["billing"])

    from app.modules.storage.router import router as storage_router
    app.include_router(storage_router, prefix=f"{prefix}/storage", tags=["storage"])

    from app.modules.notifications.router import router as notifications_router
    app.include_router(notifications_router, prefix=f"{prefix}/notifications", tags=["notifications"])

    from app.modules.realtime.router import router as realtime_router
    app.include_router(realtime_router, tags=["realtime"])

    from app.modules.admin.router import router as admin_router
    app.include_router(admin_router, prefix=f"{prefix}/admin", tags=["admin"])

    from app.modules.settings.router import router as settings_router
    app.include_router(settings_router, prefix=f"{prefix}/settings", tags=["settings"])

    # Tier 1-2: Data & Creation
    from app.modules.llm_orchestration import router as llm_router
    app.include_router(llm_router, prefix=f"{prefix}/llm", tags=["llm"])

    from app.modules.market_intelligence.router import router as market_router
    app.include_router(market_router, prefix=f"{prefix}/market", tags=["market"])

    from app.modules.knowledge_vault.router import router as knowledge_router
    app.include_router(knowledge_router, prefix=f"{prefix}/knowledge", tags=["knowledge"])

    from app.modules.ai_writing.router import router as writing_router
    app.include_router(writing_router, prefix=prefix, tags=["writing"])

    from app.modules.style_cloning.router import router as style_router
    app.include_router(style_router, prefix=f"{prefix}/style-profiles", tags=["style"])

    # Tier 3: Production
    from app.modules.production_pipeline.router import router as pipeline_router
    app.include_router(pipeline_router, prefix=f"{prefix}/pipelines", tags=["pipelines"])

    from app.modules.publishing_ops.router import metadata_router as publishing_metadata_router
    from app.modules.publishing_ops.router import router as publishing_router
    app.include_router(publishing_router, prefix=f"{prefix}/publishing", tags=["publishing"])
    app.include_router(publishing_metadata_router, prefix=prefix, tags=["publishing"])

    from app.modules.kdp_validation.router import router as kdp_router
    app.include_router(kdp_router, prefix=prefix, tags=["kdp-validation"])

    # Tier 4: Optimization
    from app.modules.product_page_lab.router import router as product_page_router
    app.include_router(product_page_router, prefix=f"{prefix}/product-page", tags=["product-page"])

    from app.modules.pricing_automation.router import router as pricing_router
    app.include_router(pricing_router, prefix=prefix, tags=["pricing"])

    from app.modules.competitor_finder.router import router as competitor_router
    app.include_router(competitor_router, prefix=f"{prefix}/competitors", tags=["competitors"])

    # Tier 5: Growth
    from app.modules.marketing.router import router as marketing_router
    app.include_router(marketing_router, prefix=f"{prefix}/marketing", tags=["marketing"])

    from app.modules.advertising.router import router as advertising_router
    app.include_router(advertising_router, prefix=f"{prefix}/ads", tags=["advertising"])

    from app.modules.review_intelligence.router import router as review_router
    app.include_router(review_router, prefix=f"{prefix}/reviews", tags=["reviews"])

    from app.modules.analytics.router import router as analytics_router
    app.include_router(analytics_router, prefix=f"{prefix}/analytics", tags=["analytics"])

    # Tier 6-8: Intelligence & Scale
    from app.modules.agent_system.router import router as agent_router
    app.include_router(agent_router, prefix=f"{prefix}/agents", tags=["agents"])

    from app.modules.portfolio_economics.router import audience_router, portfolio_router, seasonal_router
    app.include_router(portfolio_router, prefix=prefix, tags=["portfolio"])
    app.include_router(audience_router, prefix=prefix, tags=["audience"])
    app.include_router(seasonal_router, prefix=prefix, tags=["seasonal"])

    from app.modules.cover_design.router import router as cover_router
    app.include_router(cover_router, prefix=prefix, tags=["covers"])

    from app.modules.chrome_extension.router import router as extension_router
    app.include_router(extension_router, prefix=prefix, tags=["chrome-extension"])

    # VoiceForge Integration
    from app.modules.audiobook.router import router as audiobook_router
    app.include_router(audiobook_router, prefix=f"{prefix}/audiobooks", tags=["audiobooks"])

    from app.modules.audiobook.router_generation import router as audiobook_gen_router
    app.include_router(audiobook_gen_router, prefix=f"{prefix}/audiobooks", tags=["audiobooks"])

    from app.modules.audiobook.router_crud import router as audiobook_crud_router
    app.include_router(audiobook_crud_router, prefix=f"{prefix}/audiobooks/projects", tags=["audiobooks"])

    from app.modules.audiobook.router_voices import router as audiobook_voices_router
    app.include_router(audiobook_voices_router, prefix=f"{prefix}/audiobooks", tags=["audiobooks"])

    from app.modules.audiobook.router_mastering import router as audiobook_mastering_router
    app.include_router(audiobook_mastering_router, prefix=f"{prefix}/audiobooks/projects", tags=["audiobooks"])

    from app.modules.audiobook.router_export import router as audiobook_export_router
    app.include_router(audiobook_export_router, prefix=f"{prefix}/audiobooks/projects", tags=["audiobooks"])

    from app.modules.audiobook.websocket import router as audiobook_ws_router
    app.include_router(audiobook_ws_router, prefix=f"{prefix}", tags=["audiobooks-ws"])

    from app.modules.dictation.router import router as dictation_router
    app.include_router(dictation_router, prefix=f"{prefix}/dictation", tags=["dictation"])

    from app.modules.dictation.websocket import router as dictation_ws_router
    app.include_router(dictation_ws_router, prefix=f"{prefix}", tags=["dictation-ws"])

    # --- Specialty Books Module ---
    from app.modules.specialty.childrens.router import router as childrens_router
    app.include_router(childrens_router, prefix=prefix, tags=["specialty-childrens"])

    from app.modules.specialty.coloring.router import router as coloring_router
    app.include_router(coloring_router, prefix=prefix, tags=["specialty-coloring"])

    from app.modules.specialty.puzzles.router import router as puzzles_router
    app.include_router(puzzles_router, prefix=prefix, tags=["specialty-puzzles"])

    from app.modules.specialty.shared.router import router as specialty_shared_router
    app.include_router(specialty_shared_router, prefix=prefix, tags=["specialty-shared"])

    from app.modules.specialty.style_clone.router import router as style_clone_router
    app.include_router(style_clone_router, prefix=prefix, tags=["specialty-style-clone"])

    from app.modules.specialty.comic.router import router as comic_router
    app.include_router(comic_router, prefix=prefix, tags=["specialty-comic"])

app = create_app()
