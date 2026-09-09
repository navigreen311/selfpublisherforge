"""Smoke tests for SelfPublisherForge module imports.

These tests verify that every module's router, schemas, service, and model
classes can be imported without errors. This catches missing dependencies,
circular imports, and syntax errors across the entire codebase.
"""

from __future__ import annotations

import importlib

# ---------------------------------------------------------------------------
# 1. Router imports — every module that registers a router in main.py
# ---------------------------------------------------------------------------


class TestRouterImports:
    """Verify all module routers are importable."""

    def test_import_auth_router(self):
        mod = importlib.import_module("app.modules.auth.router")
        assert hasattr(mod, "router")

    def test_import_users_router(self):
        mod = importlib.import_module("app.modules.users.router")
        assert hasattr(mod, "router")

    def test_import_billing_router(self):
        mod = importlib.import_module("app.modules.billing.router")
        assert hasattr(mod, "router")

    def test_import_storage_router(self):
        mod = importlib.import_module("app.modules.storage.router")
        assert hasattr(mod, "router")

    def test_import_notifications_router(self):
        mod = importlib.import_module("app.modules.notifications.router")
        assert hasattr(mod, "router")

    def test_import_realtime_router(self):
        mod = importlib.import_module("app.modules.realtime.router")
        assert hasattr(mod, "router")

    def test_import_market_intelligence_router(self):
        mod = importlib.import_module("app.modules.market_intelligence.router")
        assert hasattr(mod, "router")

    def test_import_knowledge_vault_router(self):
        mod = importlib.import_module("app.modules.knowledge_vault.router")
        assert hasattr(mod, "router")

    def test_import_ai_writing_router(self):
        mod = importlib.import_module("app.modules.ai_writing.router")
        assert hasattr(mod, "router")

    def test_import_style_cloning_router(self):
        mod = importlib.import_module("app.modules.style_cloning.router")
        assert hasattr(mod, "router")

    def test_import_production_pipeline_router(self):
        mod = importlib.import_module("app.modules.production_pipeline.router")
        assert hasattr(mod, "router")

    def test_import_publishing_ops_router(self):
        mod = importlib.import_module("app.modules.publishing_ops.router")
        assert hasattr(mod, "router")

    def test_import_kdp_validation_router(self):
        mod = importlib.import_module("app.modules.kdp_validation.router")
        assert hasattr(mod, "router")

    def test_import_product_page_lab_router(self):
        mod = importlib.import_module("app.modules.product_page_lab.router")
        assert hasattr(mod, "router")

    def test_import_pricing_automation_router(self):
        mod = importlib.import_module("app.modules.pricing_automation.router")
        assert hasattr(mod, "router")

    def test_import_competitor_finder_router(self):
        mod = importlib.import_module("app.modules.competitor_finder.router")
        assert hasattr(mod, "router")

    def test_import_marketing_router(self):
        mod = importlib.import_module("app.modules.marketing.router")
        assert hasattr(mod, "router")

    def test_import_advertising_router(self):
        mod = importlib.import_module("app.modules.advertising.router")
        assert hasattr(mod, "router")

    def test_import_review_intelligence_router(self):
        mod = importlib.import_module("app.modules.review_intelligence.router")
        assert hasattr(mod, "router")

    def test_import_analytics_router(self):
        mod = importlib.import_module("app.modules.analytics.router")
        assert hasattr(mod, "router")

    def test_import_agent_system_router(self):
        mod = importlib.import_module("app.modules.agent_system.router")
        assert hasattr(mod, "router")

    def test_import_portfolio_economics_router(self):
        mod = importlib.import_module("app.modules.portfolio_economics.router")
        assert hasattr(mod, "portfolio_router")
        assert hasattr(mod, "audience_router")
        assert hasattr(mod, "seasonal_router")

    def test_import_cover_design_router(self):
        mod = importlib.import_module("app.modules.cover_design.router")
        assert hasattr(mod, "router")

    def test_import_chrome_extension_router(self):
        mod = importlib.import_module("app.modules.chrome_extension.router")
        assert hasattr(mod, "router")


# ---------------------------------------------------------------------------
# 2. Model class imports — from app.models and module-specific models
# ---------------------------------------------------------------------------


class TestModelImports:
    """Verify all model classes are importable."""

    def test_import_organization_model(self):
        from app.models.organization import Organization

        assert Organization is not None

    def test_import_user_model(self):
        from app.models.user import ApiKey, User, UserSession

        assert User is not None
        assert ApiKey is not None
        assert UserSession is not None

    def test_import_project_model(self):
        from app.models.project import Book, Project

        assert Project is not None
        assert Book is not None

    def test_import_content_model(self):
        from app.models.content import Manuscript

        assert Manuscript is not None

    def test_import_market_model(self):
        from app.models.market import MarketCategory

        assert MarketCategory is not None

    def test_import_publishing_model(self):
        from app.models.publishing import PublishingAccount

        assert PublishingAccount is not None

    def test_import_marketing_model(self):
        from app.models.marketing import Campaign

        assert Campaign is not None

    def test_import_agent_model(self):
        from app.models.agent import Agent

        assert Agent is not None

    def test_import_analytics_model(self):
        from app.models.analytics import AnalyticsEvent

        assert AnalyticsEvent is not None

    def test_import_notification_models(self):
        from app.modules.notifications.models import Notification, NotificationPreference

        assert Notification is not None
        assert NotificationPreference is not None

    def test_import_knowledge_vault_models(self):
        from app.modules.knowledge_vault.models import KnowledgeEntry

        assert KnowledgeEntry is not None

    def test_import_production_pipeline_models(self):
        from app.modules.production_pipeline.models import Pipeline

        assert Pipeline is not None

    def test_import_pricing_automation_models(self):
        from app.modules.pricing_automation.models import PricingRule

        assert PricingRule is not None

    def test_import_product_page_lab_models(self):
        from app.modules.product_page_lab.models import ABTest

        assert ABTest is not None

    def test_import_cover_design_models(self):
        from app.modules.cover_design.models import Cover

        assert Cover is not None

    def test_import_advertising_models(self):
        from app.modules.advertising.models import Campaign

        assert Campaign is not None

    def test_import_agent_system_models(self):
        from app.modules.agent_system.models import Agent

        assert Agent is not None

    def test_import_analytics_module_models(self):
        from app.modules.analytics.models import AnalyticsEvent

        assert AnalyticsEvent is not None

    def test_import_review_intelligence_models(self):
        from app.modules.review_intelligence.models import BookReview

        assert BookReview is not None

    def test_import_competitor_finder_models(self):
        from app.modules.competitor_finder.models import CompetitorAnalysis

        assert CompetitorAnalysis is not None


# ---------------------------------------------------------------------------
# 3. Schema class imports
# ---------------------------------------------------------------------------


class TestSchemaImports:
    """Verify all schema classes are importable."""

    def test_import_common_schemas(self):
        from app.schemas.common import HealthResponse, MessageResponse

        assert MessageResponse is not None
        assert HealthResponse is not None

    def test_import_auth_schemas(self):
        from app.modules.auth.schemas import (
            RegisterRequest,
            TokenResponse,
        )

        assert RegisterRequest is not None
        assert TokenResponse is not None

    def test_import_users_schemas(self):
        from app.modules.users.schemas import UserProfile

        assert UserProfile is not None

    def test_import_billing_schemas(self):
        mod = importlib.import_module("app.modules.billing.schemas")
        assert mod is not None

    def test_import_storage_schemas(self):
        mod = importlib.import_module("app.modules.storage.schemas")
        assert mod is not None

    def test_import_notifications_schemas(self):
        mod = importlib.import_module("app.modules.notifications.schemas")
        assert mod is not None

    def test_import_realtime_schemas(self):
        mod = importlib.import_module("app.modules.realtime.schemas")
        assert mod is not None

    def test_import_market_intelligence_schemas(self):
        mod = importlib.import_module("app.modules.market_intelligence.schemas")
        assert mod is not None

    def test_import_knowledge_vault_schemas(self):
        mod = importlib.import_module("app.modules.knowledge_vault.schemas")
        assert mod is not None

    def test_import_ai_writing_schemas(self):
        mod = importlib.import_module("app.modules.ai_writing.schemas")
        assert mod is not None

    def test_import_style_cloning_schemas(self):
        mod = importlib.import_module("app.modules.style_cloning.schemas")
        assert mod is not None

    def test_import_production_pipeline_schemas(self):
        mod = importlib.import_module("app.modules.production_pipeline.schemas")
        assert mod is not None

    def test_import_publishing_ops_schemas(self):
        mod = importlib.import_module("app.modules.publishing_ops.schemas")
        assert mod is not None

    def test_import_kdp_validation_schemas(self):
        mod = importlib.import_module("app.modules.kdp_validation.schemas")
        assert mod is not None

    def test_import_product_page_lab_schemas(self):
        mod = importlib.import_module("app.modules.product_page_lab.schemas")
        assert mod is not None

    def test_import_pricing_automation_schemas(self):
        mod = importlib.import_module("app.modules.pricing_automation.schemas")
        assert mod is not None

    def test_import_competitor_finder_schemas(self):
        mod = importlib.import_module("app.modules.competitor_finder.schemas")
        assert mod is not None

    def test_import_marketing_schemas(self):
        mod = importlib.import_module("app.modules.marketing.schemas")
        assert mod is not None

    def test_import_advertising_schemas(self):
        mod = importlib.import_module("app.modules.advertising.schemas")
        assert mod is not None

    def test_import_review_intelligence_schemas(self):
        mod = importlib.import_module("app.modules.review_intelligence.schemas")
        assert mod is not None

    def test_import_analytics_schemas(self):
        mod = importlib.import_module("app.modules.analytics.schemas")
        assert mod is not None

    def test_import_agent_system_schemas(self):
        mod = importlib.import_module("app.modules.agent_system.schemas")
        assert mod is not None

    def test_import_portfolio_economics_schemas(self):
        mod = importlib.import_module("app.modules.portfolio_economics.schemas")
        assert mod is not None

    def test_import_cover_design_schemas(self):
        mod = importlib.import_module("app.modules.cover_design.schemas")
        assert mod is not None

    def test_import_chrome_extension_schemas(self):
        mod = importlib.import_module("app.modules.chrome_extension.schemas")
        assert mod is not None


# ---------------------------------------------------------------------------
# 4. Service class imports
# ---------------------------------------------------------------------------


class TestServiceImports:
    """Verify all service modules are importable."""

    def test_import_auth_service(self):
        mod = importlib.import_module("app.modules.auth.service")
        assert hasattr(mod, "register_user")
        assert hasattr(mod, "authenticate")

    def test_import_users_service(self):
        mod = importlib.import_module("app.modules.users.service")
        assert hasattr(mod, "UserService")

    def test_import_billing_service(self):
        mod = importlib.import_module("app.modules.billing.service")
        assert mod is not None

    def test_import_storage_service(self):
        mod = importlib.import_module("app.modules.storage.service")
        assert mod is not None

    def test_import_notifications_service(self):
        mod = importlib.import_module("app.modules.notifications.service")
        assert mod is not None

    def test_import_market_intelligence_service(self):
        mod = importlib.import_module("app.modules.market_intelligence.service")
        assert mod is not None

    def test_import_knowledge_vault_service(self):
        mod = importlib.import_module("app.modules.knowledge_vault.service")
        assert mod is not None

    def test_import_ai_writing_service(self):
        mod = importlib.import_module("app.modules.ai_writing.service")
        assert mod is not None

    def test_import_style_cloning_service(self):
        mod = importlib.import_module("app.modules.style_cloning.service")
        assert mod is not None

    def test_import_production_pipeline_service(self):
        mod = importlib.import_module("app.modules.production_pipeline.service")
        assert mod is not None

    def test_import_publishing_ops_service(self):
        mod = importlib.import_module("app.modules.publishing_ops.service")
        assert mod is not None

    def test_import_kdp_validation_service(self):
        mod = importlib.import_module("app.modules.kdp_validation.service")
        assert mod is not None

    def test_import_product_page_lab_service(self):
        mod = importlib.import_module("app.modules.product_page_lab.service")
        assert mod is not None

    def test_import_pricing_automation_service(self):
        mod = importlib.import_module("app.modules.pricing_automation.service")
        assert mod is not None

    def test_import_competitor_finder_service(self):
        mod = importlib.import_module("app.modules.competitor_finder.service")
        assert mod is not None

    def test_import_marketing_service(self):
        mod = importlib.import_module("app.modules.marketing.service")
        assert mod is not None

    def test_import_advertising_service(self):
        mod = importlib.import_module("app.modules.advertising.service")
        assert mod is not None

    def test_import_review_intelligence_service(self):
        mod = importlib.import_module("app.modules.review_intelligence.service")
        assert mod is not None

    def test_import_analytics_service(self):
        mod = importlib.import_module("app.modules.analytics.service")
        assert mod is not None

    def test_import_agent_system_service(self):
        mod = importlib.import_module("app.modules.agent_system.service")
        assert mod is not None

    def test_import_portfolio_economics_services(self):
        mod_portfolio = importlib.import_module("app.modules.portfolio_economics.portfolio_service")
        mod_audience = importlib.import_module("app.modules.portfolio_economics.audience_service")
        mod_seasonal = importlib.import_module("app.modules.portfolio_economics.seasonal_service")
        assert mod_portfolio is not None
        assert mod_audience is not None
        assert mod_seasonal is not None

    def test_import_cover_design_service(self):
        mod = importlib.import_module("app.modules.cover_design.service")
        assert mod is not None

    def test_import_chrome_extension_service(self):
        mod = importlib.import_module("app.modules.chrome_extension.service")
        assert mod is not None


# ---------------------------------------------------------------------------
# 5. Core module imports
# ---------------------------------------------------------------------------


class TestCoreImports:
    """Verify core infrastructure modules are importable."""

    def test_import_config(self):
        from app.config import Settings, get_settings

        assert get_settings is not None
        assert Settings is not None

    def test_import_database(self):
        from app.database import Base, BaseModel

        assert Base is not None
        assert BaseModel is not None

    def test_import_core_security(self):
        from app.core.security import (
            hash_password,
        )

        assert hash_password is not None

    def test_import_core_dependencies(self):
        from app.core.dependencies import get_current_user

        assert get_current_user is not None

    def test_import_core_exceptions(self):
        from app.core.exceptions import AppException

        assert AppException is not None

    def test_import_llm_orchestration(self):
        from app.modules.llm_orchestration import (
            LLMOrchestrator,
            TaskType,
        )

        assert LLMOrchestrator is not None
        assert TaskType is not None
