import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db

logger = logging.getLogger(__name__)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

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

    # Health check
    @app.get("/health")
    @app.get(f"{settings.API_V1_PREFIX}/health")
    async def health():
        return {"status": "healthy", "version": settings.APP_VERSION}

    # Register module routers
    _register_routers(app)

    return app

def _safe_include(app: FastAPI, import_fn, prefix: str, tags: list[str]):
    """Import and register a router, logging a warning on failure."""
    try:
        routers = import_fn()
        if isinstance(routers, list):
            for r, t in routers:
                app.include_router(r, prefix=prefix, tags=[t])
        else:
            app.include_router(routers, prefix=prefix, tags=tags)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Skipping router %s: %s", tags, exc)


def _register_routers(app: FastAPI):
    """Register all module API routers."""
    prefix = settings.API_V1_PREFIX

    # Tier 0: Foundation
    _safe_include(app,
        lambda: __import__("app.modules.auth.router", fromlist=["router"]).router,
        f"{prefix}/auth", ["auth"])

    _safe_include(app,
        lambda: __import__("app.modules.users.router", fromlist=["router"]).router,
        prefix, ["users"])

    _safe_include(app,
        lambda: __import__("app.modules.billing.router", fromlist=["router"]).router,
        prefix, ["billing"])

    _safe_include(app,
        lambda: __import__("app.modules.storage.router", fromlist=["router"]).router,
        prefix, ["storage"])

    _safe_include(app,
        lambda: __import__("app.modules.notifications.router", fromlist=["router"]).router,
        prefix, ["notifications"])

    _safe_include(app,
        lambda: __import__("app.modules.realtime.router", fromlist=["router"]).router,
        prefix, ["realtime"])

    # Tier 1-2: Data & Creation
    # llm_orchestration has no router module; skip until it is created
    _safe_include(app,
        lambda: __import__("app.modules.llm_orchestration.router", fromlist=["router"]).router,
        f"{prefix}/llm", ["llm"])

    _safe_include(app,
        lambda: __import__("app.modules.market_intelligence.router", fromlist=["router"]).router,
        f"{prefix}/market", ["market"])

    _safe_include(app,
        lambda: __import__("app.modules.knowledge_vault.router", fromlist=["router"]).router,
        f"{prefix}/knowledge", ["knowledge"])

    _safe_include(app,
        lambda: __import__("app.modules.ai_writing.router", fromlist=["router"]).router,
        prefix, ["writing"])

    _safe_include(app,
        lambda: __import__("app.modules.style_cloning.router", fromlist=["router"]).router,
        prefix, ["style"])

    # Tier 3: Production
    _safe_include(app,
        lambda: __import__("app.modules.production_pipeline.router", fromlist=["router"]).router,
        f"{prefix}/pipelines", ["pipelines"])

    _safe_include(app,
        lambda: __import__("app.modules.publishing_ops.router", fromlist=["router"]).router,
        f"{prefix}/publishing", ["publishing"])

    from app.modules.kdp_validation.router import router as kdp_router
    app.include_router(kdp_router, prefix=prefix, tags=["kdp-validation"])

    # Tier 4: Optimization
    _safe_include(app,
        lambda: __import__("app.modules.product_page_lab.router", fromlist=["router"]).router,
        prefix, ["product-page"])

    _safe_include(app,
        lambda: __import__("app.modules.pricing_automation.router", fromlist=["router"]).router,
        prefix, ["pricing"])

    _safe_include(app,
        lambda: __import__("app.modules.competitor_finder.router", fromlist=["router"]).router,
        prefix, ["competitors"])

    # Tier 5: Growth
    _safe_include(app,
        lambda: __import__("app.modules.marketing.router", fromlist=["router"]).router,
        f"{prefix}/marketing", ["marketing"])

    _safe_include(app,
        lambda: __import__("app.modules.advertising.router", fromlist=["router"]).router,
        f"{prefix}/ads", ["advertising"])

    _safe_include(app,
        lambda: __import__("app.modules.review_intelligence.router", fromlist=["router"]).router,
        prefix, ["reviews"])

    _safe_include(app,
        lambda: __import__("app.modules.analytics.router", fromlist=["router"]).router,
        f"{prefix}/analytics", ["analytics"])

    # Tier 6-8: Intelligence & Scale
    _safe_include(app,
        lambda: __import__("app.modules.agent_system.router", fromlist=["router"]).router,
        f"{prefix}/agents", ["agents"])

    def _load_portfolio_routers():
        mod = __import__("app.modules.portfolio_economics.router", fromlist=["portfolio_router", "audience_router", "seasonal_router"])
        return [(mod.portfolio_router, "portfolio"), (mod.audience_router, "audience"), (mod.seasonal_router, "seasonal")]
    _safe_include(app, _load_portfolio_routers, prefix, ["portfolio"])

    _safe_include(app,
        lambda: __import__("app.modules.cover_design.router", fromlist=["router"]).router,
        prefix, ["covers"])

    _safe_include(app,
        lambda: __import__("app.modules.chrome_extension.router", fromlist=["router"]).router,
        prefix, ["chrome-extension"])

app = create_app()
