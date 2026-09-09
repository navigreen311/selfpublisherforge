"""Portfolio Economics unified service module.

This module provides a unified interface to the portfolio economics services:
- Audience service: audience personas, growth tracking, churn prediction
- Portfolio service: portfolio overview, kill/scale decisions, recommendations
- Seasonal service: seasonal calendar, niche seasonality, launch recommendations

This service.py aggregates and re-exports functionality from the specialized
sub-services for easier imports and maintainability.
"""

# Re-export audience service functions
from app.modules.portfolio_economics.audience_service import (
    build_also_bought_intelligence,
    build_audience_personas,
    get_audience_growth,
    predict_churn,
)

# Re-export backlist and greenlight utilities
from app.modules.portfolio_economics.backlist import calculate_backlist_projection
from app.modules.portfolio_economics.greenlight import calculate_greenlight

# Re-export portfolio service functions
from app.modules.portfolio_economics.portfolio_service import (
    build_portfolio_overview,
    calculate_kill_scale,
    generate_portfolio_recommendations,
)

# Re-export seasonal service functions
from app.modules.portfolio_economics.seasonal_service import (
    get_niche_seasonality,
    get_seasonal_calendar,
    recommend_launch_date,
)

__all__ = [
    # Audience
    "build_also_bought_intelligence",
    "build_audience_personas",
    "get_audience_growth",
    "predict_churn",
    # Portfolio
    "build_portfolio_overview",
    "calculate_kill_scale",
    "generate_portfolio_recommendations",
    # Seasonal
    "get_niche_seasonality",
    "get_seasonal_calendar",
    "recommend_launch_date",
    # Utilities
    "calculate_backlist_projection",
    "calculate_greenlight",
]
