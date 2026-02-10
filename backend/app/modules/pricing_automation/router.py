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

from app.core.dependencies import get_current_user
from app.core.pagination import PaginatedResponse
from app.database import get_db
from app.modules.pricing_automation.schemas import (
    ABTestCreate,
    ABTestResponse,
    BookFormat,
    CompetitorPriceSummary,
    KUCalculatorRequest,
    KUCalculatorResponse,
    PriceSimulationRequest,
    PriceSimulationResponse,
    PricingRuleCreate,
    PricingRuleResponse,
    PricingRuleUpdate,
    PromotionCreate,
    PromotionResponse,
    PromotionStatus,
    RuleStatus,
)
from app.modules.pricing_automation.service import PricingAutomationService

router = APIRouter(prefix="/pricing", tags=["pricing"])


def _get_service(db: AsyncSession = Depends(get_db)) -> PricingAutomationService:
    return PricingAutomationService(db)


# ──────────────────── Pricing Rules ────────────────────


@router.get("/rules", response_model=PaginatedResponse[PricingRuleResponse])
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
    rules, total = await service.list_rules(
        org_id=org_id, status=status, book_id=book_id, limit=limit, offset=offset
    )
    return PaginatedResponse(
        items=rules,
        total_count=total,
        has_more=(offset + limit) < total,
    )


@router.post(
    "/rules",
    response_model=PricingRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_pricing_rule(
    data: PricingRuleCreate,
    current_user: dict = Depends(get_current_user),
    service: PricingAutomationService = Depends(_get_service),
):
    """Create a new pricing rule."""
    org_id = current_user["org_id"]
    return await service.create_rule(org_id, data)


@router.patch("/rules/{rule_id}", response_model=PricingRuleResponse)
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


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
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
    return None


# ──────────────────── Price Simulation ────────────────────


@router.post("/simulate", response_model=PriceSimulationResponse)
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


@router.get("/promotions", response_model=PaginatedResponse[PromotionResponse])
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


@router.post("/ku-calculator", response_model=KUCalculatorResponse)
async def ku_calculator(
    data: KUCalculatorRequest,
    current_user: dict = Depends(get_current_user),
    service: PricingAutomationService = Depends(_get_service),
):
    """Calculate KU (Kindle Unlimited) vs. wide distribution revenue."""
    return await service.calculate_ku_revenue(data)
