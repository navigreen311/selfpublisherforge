from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.error_handler import register_error_handlers
from app.database import init_db

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    # Shut down the WebSocket connection manager (cancels background tasks, closes Redis).
    from app.modules.realtime.router import manager as ws_manager
    await ws_manager.shutdown()

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
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
    @app.get("/health")
    @app.get(f"{settings.API_V1_PREFIX}/health")
    async def health():
        return {"status": "healthy", "version": settings.APP_VERSION}

    # Register module routers
    _register_routers(app)

    return app

def _register_routers(app: FastAPI):
    """Register all module API routers."""
    prefix = settings.API_V1_PREFIX

    # Tier 0: Foundation
    from app.modules.auth.router import router as auth_router
    app.include_router(auth_router, prefix=f"{prefix}/auth", tags=["auth"])

    from app.modules.users.router import router as users_router
    app.include_router(users_router, prefix=prefix, tags=["users"])

    from app.modules.billing.router import router as billing_router
    app.include_router(billing_router, prefix=prefix, tags=["billing"])

    from app.modules.storage.router import router as storage_router
    app.include_router(storage_router, prefix=f"{prefix}/storage", tags=["storage"])

    from app.modules.notifications.router import router as notifications_router
    app.include_router(notifications_router, prefix=f"{prefix}/notifications", tags=["notifications"])

    from app.modules.realtime.router import router as realtime_router
    app.include_router(realtime_router, tags=["realtime"])

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

    from app.modules.publishing_ops.router import router as publishing_router, metadata_router as publishing_metadata_router
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
    app.include_router(competitor_router, prefix=prefix, tags=["competitors"])

    # Tier 5: Growth
    from app.modules.marketing.router import router as marketing_router
    app.include_router(marketing_router, prefix=f"{prefix}/marketing", tags=["marketing"])

    from app.modules.advertising.router import router as advertising_router
    app.include_router(advertising_router, prefix=f"{prefix}/ads", tags=["advertising"])

    from app.modules.review_intelligence.router import router as review_router
    app.include_router(review_router, prefix=prefix, tags=["reviews"])

    from app.modules.analytics.router import router as analytics_router
    app.include_router(analytics_router, prefix=f"{prefix}/analytics", tags=["analytics"])

    # Tier 6-8: Intelligence & Scale
    from app.modules.agent_system.router import router as agent_router
    app.include_router(agent_router, prefix=f"{prefix}/agents", tags=["agents"])

    from app.modules.portfolio_economics.router import portfolio_router, audience_router, seasonal_router
    app.include_router(portfolio_router, prefix=prefix, tags=["portfolio"])
    app.include_router(audience_router, prefix=prefix, tags=["audience"])
    app.include_router(seasonal_router, prefix=prefix, tags=["seasonal"])

    from app.modules.cover_design.router import router as cover_router
    app.include_router(cover_router, prefix=prefix, tags=["covers"])

    from app.modules.chrome_extension.router import router as extension_router
    app.include_router(extension_router, prefix=prefix, tags=["chrome-extension"])

app = create_app()
