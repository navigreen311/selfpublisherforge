"""Re-exports for analytics models.

Canonical model definitions live in their respective module packages:
- app.modules.analytics.models  (AnalyticsEvent, RoyaltyRecord, PortfolioMetricSnapshot, Report)
- app.modules.product_page_lab.models  (ABTest)

This file re-exports them so that existing ``from app.models.analytics import …``
statements continue to work without duplicating SQLAlchemy mapper registrations.
"""

import enum

# ── Enums (defined here — not duplicated in module models) ────────────
class ABTestStatus(str, enum.Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELED = "canceled"


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


# ── Re-exports from canonical module models ───────────────────────────
from app.modules.analytics.models import (  # noqa: E402
    AnalyticsEvent,
    RoyaltyRecord,
    PortfolioMetricSnapshot,
    Report,
)
from app.modules.product_page_lab.models import ABTest  # noqa: E402

# Backward-compatible alias — legacy code references "PortfolioMetric"
PortfolioMetric = PortfolioMetricSnapshot

__all__ = [
    "ABTestStatus",
    "ReportStatus",
    "AnalyticsEvent",
    "RoyaltyRecord",
    "PortfolioMetricSnapshot",
    "PortfolioMetric",
    "Report",
    "ABTest",
]
