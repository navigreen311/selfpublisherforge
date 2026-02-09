"""FastAPI router for Portfolio Economics, Audience DNA, and Seasonal Calendar endpoints."""
from datetime import date
from uuid import UUID, uuid4
from typing import Optional

from fastapi import APIRouter, Query, HTTPException, status

from shared.contracts.api import SuccessResponse, PaginatedResponse
from app.modules.portfolio_economics.schemas import (
    # Portfolio
    GreenlightRequest,
    GreenlightResult,
    KillScaleRequest,
    KillScaleDecision,
    BacklistProjection,
    PortfolioOverview,
    PortfolioRecommendation,
    ProjectionPeriod,
    # Audience
    AudienceAnalyzeRequest,
    AudiencePersona,
    AlsoBoughtIntelligence,
    AudienceGrowthResponse,
    ChurnPredictionRequest,
    ChurnPredictionResult,
    # Seasonal
    SeasonalCalendarResponse,
    NicheSeasonality,
    LaunchRecommendRequest,
    LaunchRecommendation,
    SeasonalEvent,
)
from app.modules.portfolio_economics.greenlight import calculate_greenlight
from app.modules.portfolio_economics.backlist import calculate_backlist_projection
from app.modules.portfolio_economics.portfolio_service import (
    calculate_kill_scale,
    build_portfolio_overview,
    generate_portfolio_recommendations,
)
from app.modules.portfolio_economics.audience_service import (
    build_audience_personas,
    build_also_bought_intelligence,
    get_audience_growth,
    predict_churn,
)
from app.modules.portfolio_economics.seasonal_service import (
    get_seasonal_calendar,
    get_niche_seasonality,
    recommend_launch_date,
    get_upcoming_events,
)


# ─── Routers ─────────────────────────────────────────────────────────────────

portfolio_router = APIRouter(prefix="/portfolio", tags=["portfolio"])
audience_router = APIRouter(prefix="/audience", tags=["audience"])
seasonal_router = APIRouter(prefix="/seasonal", tags=["seasonal"])


# ─── Portfolio Endpoints ─────────────────────────────────────────────────────

@portfolio_router.get(
    "",
    response_model=SuccessResponse[PortfolioOverview],
    summary="Portfolio overview",
    description="Get portfolio overview with total books, revenue, ROI, and projections.",
)
async def get_portfolio_overview(
    org_id: UUID = Query(..., description="Organization ID"),
):
    """Get portfolio overview for an organization.

    In production, this would query the database for all books and metrics.
    Here we return a representative overview.
    """
    # ASSUMPTION: In production, this queries portfolio_metrics and royalty_records tables
    sample_books = [
        {
            "book_id": uuid4(),
            "title": "Sample Book 1",
            "genre": "romance",
            "monthly_revenue": 450.0,
            "monthly_units": 90,
            "total_revenue": 5400.0,
            "total_investment": 800.0,
            "launch_date": date(2024, 1, 15),
            "status": "active",
        },
        {
            "book_id": uuid4(),
            "title": "Sample Book 2",
            "genre": "thriller",
            "monthly_revenue": 280.0,
            "monthly_units": 55,
            "total_revenue": 3360.0,
            "total_investment": 600.0,
            "launch_date": date(2024, 6, 1),
            "status": "active",
        },
    ]

    overview = build_portfolio_overview(org_id, sample_books)
    return SuccessResponse(data=overview)


@portfolio_router.post(
    "/greenlight",
    response_model=SuccessResponse[GreenlightResult],
    status_code=status.HTTP_200_OK,
    summary="Greenlight Gate",
    description="Pre-writing ROI forecast for a book idea.",
)
async def greenlight_gate(request: GreenlightRequest):
    """Evaluate a book idea's ROI potential before writing."""
    result = calculate_greenlight(request)
    return SuccessResponse(data=result)


@portfolio_router.post(
    "/kill-scale",
    response_model=SuccessResponse[KillScaleDecision],
    status_code=status.HTTP_200_OK,
    summary="Kill/Scale recommendation",
    description="Get kill/scale recommendation for an existing book.",
)
async def kill_scale_analysis(request: KillScaleRequest):
    """Analyze an existing book and recommend kill, scale, maintain, or revive."""
    decision = calculate_kill_scale(request)
    return SuccessResponse(data=decision)


@portfolio_router.get(
    "/backlist",
    response_model=SuccessResponse[BacklistProjection],
    summary="Backlist compounding planner",
    description="Revenue projections over 1/3/5 years with backlist compounding.",
)
async def backlist_projection(
    current_monthly_revenue: float = Query(500.0, ge=0.0, description="Current monthly gross revenue"),
    royalty_rate: float = Query(0.7, ge=0.0, le=1.0, description="Royalty rate"),
    period: ProjectionPeriod = Query(ProjectionPeriod.ONE_YEAR, description="Projection period"),
    num_books: int = Query(1, ge=1, description="Current number of books"),
    avg_price: float = Query(4.99, ge=0.99, description="Average book price"),
    is_series: bool = Query(False, description="Are books part of a series"),
    new_books_per_year: int = Query(0, ge=0, description="Expected new books per year"),
    new_book_monthly_revenue: float = Query(0.0, ge=0.0, description="Expected monthly revenue per new book"),
):
    """Calculate backlist compounding revenue projections."""
    projection = calculate_backlist_projection(
        current_monthly_revenue=current_monthly_revenue,
        royalty_rate=royalty_rate,
        period=period,
        num_books=num_books,
        avg_price=avg_price,
        is_series=is_series,
        new_books_per_year=new_books_per_year,
        new_book_monthly_revenue=new_book_monthly_revenue,
    )
    return SuccessResponse(data=projection)


@portfolio_router.get(
    "/recommendations",
    response_model=SuccessResponse[list[PortfolioRecommendation]],
    summary="Portfolio recommendations",
    description="AI recommendations for portfolio optimization.",
)
async def get_recommendations(
    org_id: UUID = Query(..., description="Organization ID"),
):
    """Get AI-powered portfolio optimization recommendations."""
    # Build overview first (in production, from DB)
    sample_books = [
        {
            "book_id": uuid4(),
            "title": "Sample Book 1",
            "genre": "romance",
            "monthly_revenue": 450.0,
            "monthly_units": 90,
            "total_revenue": 5400.0,
            "total_investment": 800.0,
            "status": "active",
        },
    ]
    overview = build_portfolio_overview(org_id, sample_books)
    recommendations = generate_portfolio_recommendations(overview)
    return SuccessResponse(data=recommendations)


# ─── Audience DNA Endpoints ──────────────────────────────────────────────────

@audience_router.post(
    "/analyze",
    response_model=SuccessResponse[list[AudiencePersona]],
    status_code=status.HTTP_200_OK,
    summary="Build audience profile",
    description="Build audience profile from book data and market research.",
)
async def analyze_audience(request: AudienceAnalyzeRequest):
    """Build audience personas from genre and book data."""
    personas = build_audience_personas(request)
    return SuccessResponse(data=personas)


@audience_router.get(
    "/personas/{book_id}",
    response_model=SuccessResponse[list[AudiencePersona]],
    summary="Reader personas",
    description="Get reader personas for a book.",
)
async def get_personas(
    book_id: UUID,
    genre: str = Query("romance", description="Book genre for persona generation"),
):
    """Get reader personas for a specific book."""
    request = AudienceAnalyzeRequest(book_id=book_id, genre=genre)
    personas = build_audience_personas(request)
    return SuccessResponse(data=personas)


@audience_router.get(
    "/also-bought/{book_id}",
    response_model=SuccessResponse[AlsoBoughtIntelligence],
    summary="Also-bought intelligence",
    description="Get also-bought analysis for a book.",
)
async def get_also_bought(
    book_id: UUID,
    genre: str = Query("romance", description="Book genre"),
):
    """Get also-bought intelligence for a book."""
    result = build_also_bought_intelligence(book_id, genre)
    return SuccessResponse(data=result)


@audience_router.get(
    "/growth",
    response_model=SuccessResponse[AudienceGrowthResponse],
    summary="Audience growth tracking",
    description="Track audience growth over time.",
)
async def audience_growth(
    org_id: UUID = Query(..., description="Organization ID"),
    days: int = Query(90, ge=7, le=365, description="Number of days to track"),
):
    """Get audience growth tracking data."""
    result = get_audience_growth(org_id, days)
    return SuccessResponse(data=result)


@audience_router.post(
    "/churn-prediction",
    response_model=SuccessResponse[ChurnPredictionResult],
    status_code=status.HTTP_200_OK,
    summary="Churn prediction",
    description="Predict churn risk for reader engagement.",
)
async def churn_prediction(request: ChurnPredictionRequest):
    """Predict churn risk for a reader segment."""
    result = predict_churn(request)
    return SuccessResponse(data=result)


# ─── Seasonal Calendar Endpoints ─────────────────────────────────────────────

@seasonal_router.get(
    "/calendar",
    response_model=SuccessResponse[SeasonalCalendarResponse],
    summary="Seasonal calendar",
    description="Full seasonal calendar with niche-specific events.",
)
async def seasonal_calendar(
    year: int = Query(default=None, description="Calendar year (defaults to current year)"),
    genres: Optional[str] = Query(None, description="Comma-separated list of genres"),
):
    """Get full seasonal calendar with genre-specific events."""
    target_year = year or date.today().year
    genre_list = [g.strip() for g in genres.split(",")] if genres else None
    result = get_seasonal_calendar(target_year, genre_list)
    return SuccessResponse(data=result)


@seasonal_router.get(
    "/niche/{genre}",
    response_model=SuccessResponse[NicheSeasonality],
    summary="Niche seasonality",
    description="Seasonality data for a specific niche/genre.",
)
async def niche_seasonality(
    genre: str,
    year: Optional[int] = Query(None, description="Year for events"),
):
    """Get seasonality data for a specific genre."""
    result = get_niche_seasonality(genre, year)
    return SuccessResponse(data=result)


@seasonal_router.post(
    "/recommend-launch",
    response_model=SuccessResponse[LaunchRecommendation],
    status_code=status.HTTP_200_OK,
    summary="Launch date recommendation",
    description="AI recommend optimal launch date.",
)
async def recommend_launch(request: LaunchRecommendRequest):
    """Get AI-recommended launch date based on genre seasonality and events."""
    result = recommend_launch_date(request)
    return SuccessResponse(data=result)


@seasonal_router.get(
    "/events",
    response_model=SuccessResponse[list[SeasonalEvent]],
    summary="Upcoming events",
    description="Upcoming events and triggers relevant to user's genres.",
)
async def upcoming_events(
    genres: Optional[str] = Query(None, description="Comma-separated list of genres"),
    days_ahead: int = Query(90, ge=7, le=365, description="Days to look ahead"),
):
    """Get upcoming events relevant to the user's genres."""
    genre_list = [g.strip() for g in genres.split(",")] if genres else []
    result = get_upcoming_events(genre_list, days_ahead)
    return SuccessResponse(data=result)
