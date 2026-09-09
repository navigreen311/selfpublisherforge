"""FastAPI router for the Pricing Automation module.

Endpoints:
  GET    /api/v1/pricing/rules                  — List pricing rules for org
  POST   /api/v1/pricing/rules                  — Create pricing rule
  PATCH  /api/v1/pricing/rules/{id}             — Update rule
  DELETE /api/v1/pricing/rules/{id}             — Delete rule
  POST   /api/v1/pricing/simulate               — Simulate price change impact
  GET    /api/v1/pricing/competitors/{book_id}  — Competitor pricing data
  POST   /api/v1/pricing/ab-test                — Create pricing A/B test
  GET    /api/v1/pricing/promotions             — Get promotional calendar
  POST   /api/v1/pricing/promotions             — Schedule promotion
  POST   /api/v1/pricing/ku-calculator          — KU vs. wide revenue calculator
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.contracts import SuccessResponse
from app.core.dependencies import get_current_user
from app.core.pagination import PaginatedResponse
from app.database import get_db
from app.modules.pricing_automation import (
    price_history_service,
    royalty_analyzer,
    scheduled_changes_service,
    strategy_manager,
)
from app.modules.pricing_automation.schemas import (
    ABTestCreate,
    ABTestResponse,
    BookFormat,
    CompetitorPriceSummary,
    EnhancedSimulationResponse,
    KUCalculatorRequest,
    KUCalculatorResponse,
    PriceHistoryResponse,
    PriceSimulationRequest,
    PriceSimulationResponse,
    PricingRuleCreate,
    PricingRuleResponse,
    PricingRuleUpdate,
    PromotionCreate,
    PromotionResponse,
    PromotionStatus,
    RoyaltyAnalysisResponse,
    RuleStatus,
    ScheduledChangeCreate,
    ScheduledChangeResponse,
    StrategyCreateRequest,
    StrategyResponse,
    StrategyUpdateRequest,
)
from app.modules.pricing_automation.service import PricingAutomationService

router = APIRouter(prefix="/pricing", tags=["pricing"])


def _get_service(db: AsyncSession = Depends(get_db)) -> PricingAutomationService:
    return PricingAutomationService(db)


# ──────────────────── Pricing Rules ────────────────────


@router.get(
    "/rules",
    response_model=PaginatedResponse[PricingRuleResponse],
    summary="List pricing rules",
    description="List all pricing rules for the current organization with optional filters.",
)
async def list_pricing_rules(
    status: RuleStatus | None = Query(default=None),
    book_id: UUID | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    service: PricingAutomationService = Depends(_get_service),
):
    """List all pricing rules for the current organization."""
    org_id = current_user["org_id"]
    rules, total = await service.list_rules(org_id=org_id, status=status, book_id=book_id, limit=limit, offset=offset)
    return PaginatedResponse(
        items=rules,
        total_count=total,
        has_more=(offset + limit) < total,
    )


@router.post(
    "/rules",
    response_model=PricingRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create pricing rule",
    description="Create a new automated pricing rule for a book.",
)
async def create_pricing_rule(
    data: PricingRuleCreate,
    current_user: dict = Depends(get_current_user),
    service: PricingAutomationService = Depends(_get_service),
):
    """Create a new pricing rule."""
    org_id = current_user["org_id"]
    return await service.create_rule(org_id, data)


@router.patch(
    "/rules/{rule_id}",
    response_model=PricingRuleResponse,
    summary="Update pricing rule",
    description="Update an existing pricing rule's conditions or target price.",
)
async def update_pricing_rule(
    rule_id: UUID,
    data: PricingRuleUpdate,
    current_user: dict = Depends(get_current_user),
    service: PricingAutomationService = Depends(_get_service),
):
    """Update an existing pricing rule."""
    org_id = current_user["org_id"]
    rule = await service.update_rule(org_id, rule_id, data)
    if rule is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing rule not found",
        )
    return rule


@router.delete(
    "/rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete pricing rule",
    description="Soft-delete a pricing rule.",
)
async def delete_pricing_rule(
    rule_id: UUID,
    current_user: dict = Depends(get_current_user),
    service: PricingAutomationService = Depends(_get_service),
):
    """Soft-delete a pricing rule."""
    org_id = current_user["org_id"]
    deleted = await service.delete_rule(org_id, rule_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing rule not found",
        )
    return


# ──────────────────── Price Simulation ────────────────────


@router.post(
    "/simulate",
    response_model=PriceSimulationResponse,
    summary="Simulate price change",
    description="Simulate the revenue impact of a price change before applying it.",
)
async def simulate_price_change(
    data: PriceSimulationRequest,
    current_user: dict = Depends(get_current_user),
    service: PricingAutomationService = Depends(_get_service),
):
    """Simulate the revenue impact of a price change."""
    return await service.simulate_price(data)


# ──────────────────── Competitor Prices ────────────────────


@router.get(
    "/competitors/{book_id}",
    response_model=CompetitorPriceSummary,
    summary="Get competitor prices",
    description="Get competitor pricing data and summary for a specific book.",
)
async def get_competitor_prices(
    book_id: UUID,
    book_format: BookFormat | None = Query(default=None),
    current_user: dict = Depends(get_current_user),
    service: PricingAutomationService = Depends(_get_service),
):
    """Get competitor pricing data and summary for a specific book."""
    org_id = current_user["org_id"]
    return await service.get_competitor_prices(org_id, book_id, book_format)


# ──────────────────── A/B Tests ────────────────────


@router.post(
    "/ab-test",
    response_model=ABTestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create pricing A/B test",
    description="Create a pricing A/B test to compare two price points.",
)
async def create_ab_test(
    data: ABTestCreate,
    current_user: dict = Depends(get_current_user),
    service: PricingAutomationService = Depends(_get_service),
):
    """Create a pricing A/B test."""
    org_id = current_user["org_id"]
    return await service.create_ab_test(org_id, data)


# ──────────────────── Promotions ────────────────────


@router.get(
    "/promotions",
    response_model=PaginatedResponse[PromotionResponse],
    summary="List promotions",
    description="Get the promotional calendar with optional book and status filters.",
)
async def list_promotions(
    book_id: UUID | None = Query(default=None),
    status: PromotionStatus | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
    service: PricingAutomationService = Depends(_get_service),
):
    """Get the promotional calendar (list of promotions)."""
    org_id = current_user["org_id"]
    promotions, total = await service.list_promotions(
        org_id=org_id, book_id=book_id, status=status, limit=limit, offset=offset
    )
    return PaginatedResponse(
        items=promotions,
        total_count=total,
        has_more=(offset + limit) < total,
    )


@router.post(
    "/promotions",
    response_model=PromotionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule promotion",
    description="Schedule a new promotional price change for a book.",
)
async def create_promotion(
    data: PromotionCreate,
    current_user: dict = Depends(get_current_user),
    service: PricingAutomationService = Depends(_get_service),
):
    """Schedule a new promotion."""
    org_id = current_user["org_id"]
    return await service.create_promotion(org_id, data)


# ──────────────────── KU Calculator ────────────────────


@router.post(
    "/ku-calculator",
    response_model=KUCalculatorResponse,
    summary="KU vs. wide calculator",
    description="Calculate Kindle Unlimited vs. wide distribution revenue projections.",
)
async def ku_calculator(
    data: KUCalculatorRequest,
    current_user: dict = Depends(get_current_user),
    service: PricingAutomationService = Depends(_get_service),
):
    """Calculate KU (Kindle Unlimited) vs. wide distribution revenue."""
    return await service.calculate_ku_revenue(data)


# ──────────────────── Pricing Strategies ────────────────────


@router.post(
    "/strategies",
    response_model=SuccessResponse[StrategyResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create pricing strategy",
    description="Create a new pricing strategy with associated books and configuration.",
)
async def create_strategy(
    data: StrategyCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new pricing strategy."""
    org_id = current_user["org_id"]
    result = await strategy_manager.create_strategy(db, org_id, data.model_dump())
    return SuccessResponse(data=result)


@router.get(
    "/strategies",
    response_model=SuccessResponse[list[StrategyResponse]],
    summary="List pricing strategies",
    description="List all pricing strategies for the current organization.",
)
async def list_strategies(
    status_filter: str | None = Query(default=None, alias="status"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List pricing strategies."""
    org_id = current_user["org_id"]
    result = await strategy_manager.list_strategies(db, org_id, status=status_filter)
    return SuccessResponse(data=result)


@router.get(
    "/strategies/{strategy_id}",
    response_model=SuccessResponse[StrategyResponse],
    summary="Get pricing strategy",
    description="Get a single pricing strategy by ID.",
)
async def get_strategy(
    strategy_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a pricing strategy."""
    org_id = current_user["org_id"]
    result = await strategy_manager.get_strategy(db, org_id, strategy_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing strategy not found",
        )
    return SuccessResponse(data=result)


@router.patch(
    "/strategies/{strategy_id}",
    response_model=SuccessResponse[StrategyResponse],
    summary="Update pricing strategy",
    description="Update an existing pricing strategy.",
)
async def update_strategy(
    strategy_id: UUID,
    data: StrategyUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a pricing strategy."""
    org_id = current_user["org_id"]
    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    result = await strategy_manager.update_strategy(db, org_id, strategy_id, update_data)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing strategy not found",
        )
    return SuccessResponse(data=result)


@router.delete(
    "/strategies/{strategy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete pricing strategy",
    description="Soft-delete a pricing strategy.",
)
async def delete_strategy(
    strategy_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a pricing strategy."""
    org_id = current_user["org_id"]
    deleted = await strategy_manager.delete_strategy(db, org_id, strategy_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing strategy not found",
        )
    return


@router.post(
    "/strategies/{strategy_id}/run",
    response_model=SuccessResponse[dict],
    summary="Run pricing strategy",
    description="Execute a strategy check against associated books.",
)
async def run_strategy(
    strategy_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run a pricing strategy check."""
    org_id = current_user["org_id"]
    result = await strategy_manager.run_strategy(db, org_id, strategy_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing strategy not found",
        )
    return SuccessResponse(data=result)


# ──────────────────── Scheduled Price Changes ────────────────────


@router.post(
    "/scheduled-changes",
    response_model=SuccessResponse[ScheduledChangeResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create scheduled price change",
    description="Schedule a future price change for a book.",
)
async def create_scheduled_change(
    data: ScheduledChangeCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a scheduled price change."""
    org_id = current_user["org_id"]
    result = await scheduled_changes_service.create_scheduled_change(db, org_id, data.model_dump())
    return SuccessResponse(data=result)


@router.get(
    "/scheduled-changes",
    response_model=SuccessResponse[list[ScheduledChangeResponse]],
    summary="List scheduled price changes",
    description="List scheduled price changes with optional filters.",
)
async def list_scheduled_changes(
    book_id: UUID | None = Query(default=None),
    change_status: str = Query(default="pending", alias="status"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List scheduled price changes."""
    org_id = current_user["org_id"]
    result = await scheduled_changes_service.list_scheduled_changes(db, org_id, book_id=book_id, status=change_status)
    return SuccessResponse(data=result)


@router.delete(
    "/scheduled-changes/{change_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel scheduled price change",
    description="Cancel a pending scheduled price change.",
)
async def cancel_scheduled_change(
    change_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a scheduled price change."""
    org_id = current_user["org_id"]
    cancelled = await scheduled_changes_service.cancel_scheduled_change(db, org_id, change_id)
    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled change not found or already executed",
        )
    return


# ──────────────────── Price History ────────────────────


@router.get(
    "/history",
    response_model=SuccessResponse[PriceHistoryResponse],
    summary="Get price change history",
    description="Get price change history with optional book and period filters.",
)
async def get_price_history(
    book_id: UUID | None = Query(default=None),
    period: str = Query(default="90d"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get price change history."""
    org_id = current_user["org_id"]
    entries = await price_history_service.get_price_history(db, org_id, book_id=book_id, period=period)
    return SuccessResponse(
        data=PriceHistoryResponse(
            entries=entries,
            book_filter=str(book_id) if book_id else None,
        )
    )


# ──────────────────── Royalty Analysis ────────────────────


@router.get(
    "/royalty-analysis",
    response_model=SuccessResponse[RoyaltyAnalysisResponse],
    summary="Get royalty analysis",
    description="Get per-book royalty breakdown with optimization tips.",
)
async def get_royalty_analysis(
    period: str = Query(default="30d"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get royalty analysis with optimization tips."""
    org_id = current_user["org_id"]
    result = await royalty_analyzer.get_royalty_analysis(db, org_id, period=period)
    return SuccessResponse(data=result)


# ──────────────────── Enhanced Simulation ────────────────────


@router.post(
    "/simulate/enhanced",
    response_model=SuccessResponse[EnhancedSimulationResponse],
    summary="Enhanced price simulation",
    description="Run an enhanced price simulation with revenue curve and optimal price calculation.",
)
async def simulate_enhanced(
    data: PriceSimulationRequest,
    current_user: dict = Depends(get_current_user),
    service: PricingAutomationService = Depends(_get_service),
):
    """Enhanced simulation with revenue curve and optimal price."""
    # Run base simulation
    base_result = await service.simulate_price(data)

    # Generate revenue curve across multiple price points
    from app.modules.pricing_automation.simulator import (
        _build_price_point,
        _estimate_sales_change,
    )

    curve_prices = [
        round(data.current_price * mult, 2) for mult in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5, 1.75, 2.0]
    ]
    # Ensure proposed price is included
    if data.proposed_price not in curve_prices:
        curve_prices.append(data.proposed_price)
    curve_prices = sorted(set(p for p in curve_prices if p > 0))

    revenue_curve: list[dict] = []
    best_royalty = 0.0
    optimal_price = data.current_price

    for price in curve_prices:
        est_sales = _estimate_sales_change(data.current_price, price, data.current_daily_sales, data.elasticity)
        point = _build_price_point(price, est_sales, data.book_format, data.royalty_rate)
        monthly_royalty = point.estimated_monthly_royalties

        revenue_curve.append(
            {
                "price": price,
                "estimated_daily_sales": point.estimated_daily_sales,
                "estimated_monthly_revenue": point.estimated_monthly_revenue,
                "estimated_monthly_royalties": monthly_royalty,
                "royalty_rate": point.royalty_rate,
            }
        )

        if monthly_royalty > best_royalty:
            best_royalty = monthly_royalty
            optimal_price = price

    # Build recommendation text
    if optimal_price == data.current_price:
        recommendation = (
            f"Your current price of ${data.current_price:.2f} is already optimal "
            f"for maximizing royalties at ${best_royalty:.2f}/month."
        )
    elif optimal_price == data.proposed_price:
        recommendation = (
            f"Your proposed price of ${data.proposed_price:.2f} is the optimal price, "
            f"projected to earn ${best_royalty:.2f}/month in royalties."
        )
    else:
        recommendation = (
            f"The optimal price is ${optimal_price:.2f} (${best_royalty:.2f}/month royalties), "
            f"which differs from both your current (${data.current_price:.2f}) "
            f"and proposed (${data.proposed_price:.2f}) prices."
        )

    # Construct enhanced response using base result fields
    return SuccessResponse(
        data=EnhancedSimulationResponse(
            book_id=base_result.book_id,
            current_price=base_result.current_price,
            proposed_price=base_result.proposed_price,
            price_change_pct=base_result.price_change_pct,
            book_format=base_result.book_format,
            elasticity=base_result.elasticity,
            current_metrics=base_result.current_metrics,
            proposed_metrics=base_result.proposed_metrics,
            revenue_change_pct=base_result.revenue_change_pct,
            royalty_change_pct=base_result.royalty_change_pct,
            breakeven_sales=base_result.breakeven_sales,
            recommended_price_points=base_result.recommended_price_points,
            revenue_curve=revenue_curve,
            optimal_price=round(optimal_price, 2),
            recommendation=recommendation,
        )
    )
