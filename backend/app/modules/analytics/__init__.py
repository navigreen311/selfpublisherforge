"""Analytics & Business Intelligence module.

Provides revenue dashboards, royalty import pipelines, portfolio metrics,
custom report builder, and data export capabilities.
"""

from app.modules.analytics.router import router

__all__ = ["router"]
