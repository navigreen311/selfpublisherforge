"""Service layer for Pricing Automation module.

Handles all business logic for pricing rules, competitor monitoring,
promotions, A/B tests, and price simulation.
"""

from __future__ import annotations

import statistics
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.pricing_automation.ku_calculator import calculate_ku_vs_wide
from app.modules.pricing_automation.models import (
    ABTestStatus,
    CompetitorPrice,
    PricingABTest,
    PricingRule,
    Promotion,
    PromotionStatus,
    RuleStatus,
)
from app.modules.pricing_automation.schemas import (
    ABTestCreate,
    ABTestResponse,
    BookFormat,
    CompetitorPriceEntry,
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
)
from app.modules.pricing_automation.simulator import simulate_price_change


class PricingAutomationService:
    """Core service for pricing automation operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ──────────────────── Pricing Rules ────────────────────

    async def list_rules(
        self,
        org_id: UUID,
        status: RuleStatus | None = None,
        book_id: UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[PricingRuleResponse], int]:
        """List pricing rules for an organization with optional filters."""
        query = select(PricingRule).where(PricingRule.org_id == org_id).where(PricingRule.deleted_at.is_(None))
        count_query = (
            select(func.count())
            .select_from(PricingRule)
            .where(PricingRule.org_id == org_id)
            .where(PricingRule.deleted_at.is_(None))
        )

        if status is not None:
            query = query.where(PricingRule.status == status)
            count_query = count_query.where(PricingRule.status == status)
        if book_id is not None:
            query = query.where(PricingRule.book_id == book_id)
            count_query = count_query.where(PricingRule.book_id == book_id)

        # Get total count
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0

        # Fetch paginated results
        query = query.order_by(PricingRule.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        rules = result.scalars().all()

        return [PricingRuleResponse.model_validate(r) for r in rules], total_count

    async def create_rule(self, org_id: UUID, data: PricingRuleCreate) -> PricingRuleResponse:
        """Create a new pricing rule."""
        rule = PricingRule(
            org_id=org_id,
            name=data.name,
            description=data.description,
            book_id=data.book_id,
            strategy=data.strategy,
            book_format=data.book_format,
            min_price=data.min_price,
            max_price=data.max_price,
            target_price=data.target_price,
            parameters=data.parameters,
            is_auto_apply=data.is_auto_apply,
            status=RuleStatus.DRAFT,
        )
        self.db.add(rule)
        await self.db.flush()
        await self.db.refresh(rule)
        return PricingRuleResponse.model_validate(rule)

    async def get_rule(self, org_id: UUID, rule_id: UUID) -> PricingRuleResponse | None:
        """Get a single pricing rule by ID."""
        result = await self.db.execute(
            select(PricingRule)
            .where(PricingRule.id == rule_id)
            .where(PricingRule.org_id == org_id)
            .where(PricingRule.deleted_at.is_(None))
        )
        rule = result.scalar_one_or_none()
        return PricingRuleResponse.model_validate(rule) if rule else None

    async def update_rule(self, org_id: UUID, rule_id: UUID, data: PricingRuleUpdate) -> PricingRuleResponse | None:
        """Update an existing pricing rule."""
        result = await self.db.execute(
            select(PricingRule)
            .where(PricingRule.id == rule_id)
            .where(PricingRule.org_id == org_id)
            .where(PricingRule.deleted_at.is_(None))
        )
        rule = result.scalar_one_or_none()
        if rule is None:
            return None

        update_data = data.model_dump(exclude_unset=True, exclude_none=True)
        for field_name, value in update_data.items():
            setattr(rule, field_name, value)

        await self.db.flush()
        await self.db.refresh(rule)
        return PricingRuleResponse.model_validate(rule)

    async def delete_rule(self, org_id: UUID, rule_id: UUID) -> bool:
        """Soft-delete a pricing rule."""
        result = await self.db.execute(
            select(PricingRule)
            .where(PricingRule.id == rule_id)
            .where(PricingRule.org_id == org_id)
            .where(PricingRule.deleted_at.is_(None))
        )
        rule = result.scalar_one_or_none()
        if rule is None:
            return False

        rule.deleted_at = datetime.now(UTC)
        rule.status = RuleStatus.ARCHIVED
        await self.db.flush()
        return True

    # ──────────────────── Price Simulation ────────────────────

    async def simulate_price(self, request: PriceSimulationRequest) -> PriceSimulationResponse:
        """Run price change simulation (stateless computation)."""
        return simulate_price_change(request)

    # ──────────────────── Competitor Prices ────────────────────

    async def get_competitor_prices(
        self,
        org_id: UUID,
        book_id: UUID,
        book_format: BookFormat | None = None,
    ) -> CompetitorPriceSummary:
        """Retrieve competitor pricing data and summary statistics for a book."""
        query = (
            select(CompetitorPrice)
            .where(CompetitorPrice.org_id == org_id)
            .where(CompetitorPrice.book_id == book_id)
            .where(CompetitorPrice.deleted_at.is_(None))
        )
        if book_format is not None:
            query = query.where(CompetitorPrice.book_format == book_format)

        query = query.order_by(CompetitorPrice.snapshot_date.desc())
        result = await self.db.execute(query)
        competitors = result.scalars().all()

        entries = [CompetitorPriceEntry.model_validate(c) for c in competitors]
        prices = [c.price for c in competitors]

        if prices:
            sorted_prices = sorted(prices)
            n = len(sorted_prices)
            avg_price = round(statistics.mean(prices), 2)
            median_price = round(statistics.median(prices), 2)
            min_price = round(sorted_prices[0], 2)
            max_price = round(sorted_prices[-1], 2)
            p25 = round(sorted_prices[n // 4], 2) if n >= 4 else min_price
            p75 = round(sorted_prices[(3 * n) // 4], 2) if n >= 4 else max_price

            bsr_values = [c.bsr_rank for c in competitors if c.bsr_rank is not None]
            avg_bsr = round(statistics.mean(bsr_values), 2) if bsr_values else None

            rating_values = [c.review_rating for c in competitors if c.review_rating is not None]
            avg_rating = round(statistics.mean(rating_values), 2) if rating_values else None
        else:
            avg_price = median_price = min_price = max_price = p25 = p75 = 0.0
            avg_bsr = None
            avg_rating = None

        effective_format = book_format or BookFormat.EBOOK

        return CompetitorPriceSummary(
            book_id=book_id,
            book_format=effective_format,
            total_competitors=len(entries),
            avg_price=avg_price,
            median_price=median_price,
            min_price=min_price,
            max_price=max_price,
            price_percentile_25=p25,
            price_percentile_75=p75,
            avg_bsr=avg_bsr,
            avg_review_rating=avg_rating,
            competitors=entries,
        )

    # ──────────────────── A/B Tests ────────────────────

    async def create_ab_test(self, org_id: UUID, data: ABTestCreate) -> ABTestResponse:
        """Create a pricing A/B test."""
        ab_test = PricingABTest(
            org_id=org_id,
            pricing_rule_id=data.pricing_rule_id,
            book_id=data.book_id,
            name=data.name,
            description=data.description,
            price_a=data.price_a,
            price_b=data.price_b,
            book_format=data.book_format,
            duration_days=data.duration_days,
            status=ABTestStatus.DRAFT,
        )
        self.db.add(ab_test)
        await self.db.flush()
        await self.db.refresh(ab_test)
        return ABTestResponse.model_validate(ab_test)

    # ──────────────────── Promotions ────────────────────

    async def list_promotions(
        self,
        org_id: UUID,
        book_id: UUID | None = None,
        status: PromotionStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[PromotionResponse], int]:
        """List promotional calendar entries for an organization."""
        query = select(Promotion).where(Promotion.org_id == org_id).where(Promotion.deleted_at.is_(None))
        count_query = (
            select(func.count())
            .select_from(Promotion)
            .where(Promotion.org_id == org_id)
            .where(Promotion.deleted_at.is_(None))
        )

        if book_id is not None:
            query = query.where(Promotion.book_id == book_id)
            count_query = count_query.where(Promotion.book_id == book_id)
        if status is not None:
            query = query.where(Promotion.status == status)
            count_query = count_query.where(Promotion.status == status)

        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar() or 0

        query = query.order_by(Promotion.start_date.asc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        promotions = result.scalars().all()

        return [PromotionResponse.model_validate(p) for p in promotions], total_count

    async def create_promotion(self, org_id: UUID, data: PromotionCreate) -> PromotionResponse:
        """Schedule a new promotion."""
        promotion = Promotion(
            org_id=org_id,
            pricing_rule_id=data.pricing_rule_id,
            book_id=data.book_id,
            name=data.name,
            description=data.description,
            original_price=data.original_price,
            promo_price=data.promo_price,
            book_format=data.book_format,
            start_date=data.start_date,
            end_date=data.end_date,
            platform=data.platform,
            notes=data.notes,
            status=PromotionStatus.SCHEDULED,
        )
        self.db.add(promotion)
        await self.db.flush()
        await self.db.refresh(promotion)
        return PromotionResponse.model_validate(promotion)

    # ──────────────────── KU Calculator ────────────────────

    async def calculate_ku_revenue(self, request: KUCalculatorRequest) -> KUCalculatorResponse:
        """Calculate KU vs. wide distribution revenue (stateless)."""
        return calculate_ku_vs_wide(request)
