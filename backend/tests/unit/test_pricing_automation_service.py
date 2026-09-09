"""Unit tests for the Pricing Automation service layer.

Covers pricing rules, price simulation, competitor prices,
A/B tests, promotions, and KU calculator.

All tests use mocked AsyncSession -- no real DB.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.pricing_automation.models import ABTestStatus, RuleStatus
from app.modules.pricing_automation.schemas import (
    ABTestCreate,
    BookFormat,
    KUCalculatorRequest,
    PriceSimulationRequest,
    PricingRuleCreate,
    PricingRuleUpdate,
    PromotionCreate,
)
from app.modules.pricing_automation.service import PricingAutomationService

# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def org_id():
    return uuid.uuid4()


@pytest.fixture
def book_id():
    return uuid.uuid4()


@pytest.fixture
def mock_db():
    """Return an AsyncMock simulating an AsyncSession."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def service(mock_db):
    """Return a PricingAutomationService instance with mocked DB."""
    return PricingAutomationService(mock_db)


def _make_pricing_rule(**overrides):
    """Factory helper to create a PricingRule mock."""
    defaults = {
        "id": uuid.uuid4(),
        "org_id": uuid.uuid4(),
        "name": "Test Rule",
        "description": "Test pricing rule",
        "book_id": uuid.uuid4(),
        "strategy": "fixed",
        "book_format": BookFormat.EBOOK,
        "min_price": Decimal("2.99"),
        "max_price": Decimal("9.99"),
        "target_price": Decimal("4.99"),
        "parameters": {},
        "is_auto_apply": False,
        "status": RuleStatus.DRAFT,
        "created_at": datetime.now(UTC),
        "deleted_at": None,
    }
    defaults.update(overrides)
    rule = MagicMock()
    for k, v in defaults.items():
        setattr(rule, k, v)
    return rule


# ===========================================================================
# Tests: list_rules
# ===========================================================================

class TestListRules:
    """Tests for PricingAutomationService.list_rules."""

    @pytest.mark.asyncio
    async def test_returns_rules_with_pagination(
        self,
        service,
        org_id,
    ):
        """list_rules should return paginated list of pricing rules."""
        rule1 = _make_pricing_rule()
        rule2 = _make_pricing_rule()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [rule1, rule2, rule1, rule2]

        service.db.execute.side_effect = [mock_result, mock_result]

        rules, total = await service.list_rules(org_id, limit=10, offset=0)

        assert len(rules) == 2
        assert total == 4

    @pytest.mark.asyncio
    async def test_filters_by_status(
        self,
        service,
        org_id,
    ):
        """list_rules should filter by status when provided."""
        rule1 = _make_pricing_rule(status=RuleStatus.ACTIVE)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [rule1]

        service.db.execute.side_effect = [mock_result, mock_result]

        rules, total = await service.list_rules(org_id, status=RuleStatus.ACTIVE)

        assert len(rules) == 1
        assert rules[0].status == RuleStatus.ACTIVE


# ===========================================================================
# Tests: create_rule
# ===========================================================================

class TestCreateRule:
    """Tests for PricingAutomationService.create_rule."""

    @pytest.mark.asyncio
    async def test_creates_pricing_rule(
        self,
        service,
        org_id,
        book_id,
    ):
        """create_rule should create a new pricing rule."""
        data = PricingRuleCreate(
            name="Dynamic Pricing",
            description="Adjust price based on competitors",
            book_id=book_id,
            strategy="dynamic",
            book_format=BookFormat.EBOOK,
            min_price=Decimal("2.99"),
            max_price=Decimal("9.99"),
            target_price=Decimal("4.99"),
            parameters={},
            is_auto_apply=False,
        )

        result = await service.create_rule(org_id, data)

        service.db.add.assert_called_once()
        service.db.flush.assert_awaited_once()
        assert result.name == "Dynamic Pricing"


# ===========================================================================
# Tests: update_rule
# ===========================================================================

class TestUpdateRule:
    """Tests for PricingAutomationService.update_rule."""

    @pytest.mark.asyncio
    async def test_updates_pricing_rule(
        self,
        service,
        org_id,
    ):
        """update_rule should update an existing rule."""
        rule_id = uuid.uuid4()
        rule = _make_pricing_rule(id=rule_id)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = rule
        service.db.execute.return_value = mock_result

        update_data = PricingRuleUpdate(
            name="Updated Rule Name",
            is_auto_apply=True,
        )

        result = await service.update_rule(org_id, rule_id, update_data)

        assert result is not None
        assert rule.name == "Updated Rule Name"
        assert rule.is_auto_apply is True


# ===========================================================================
# Tests: simulate_price
# ===========================================================================

class TestSimulatePrice:
    """Tests for PricingAutomationService.simulate_price."""

    @pytest.mark.asyncio
    @patch("app.modules.pricing_automation.service.simulate_price_change")
    async def test_runs_price_simulation(
        self,
        mock_simulate_price_change,
        service,
    ):
        """simulate_price should call the simulator and return results."""
        mock_simulate_price_change.return_value = MagicMock(
            current_price=Decimal("4.99"),
            new_price=Decimal("3.99"),
            estimated_revenue_change=Decimal("50.00"),
            estimated_unit_change=15,
            break_even_units=10,
        )

        request = PriceSimulationRequest(
            current_price=Decimal("4.99"),
            new_price=Decimal("3.99"),
            current_units=100,
            elasticity=1.2,
        )

        result = await service.simulate_price(request)

        assert result.current_price == Decimal("4.99")
        assert result.new_price == Decimal("3.99")
        mock_simulate_price_change.assert_called_once()


# ===========================================================================
# Tests: get_competitor_prices
# ===========================================================================

class TestGetCompetitorPrices:
    """Tests for PricingAutomationService.get_competitor_prices."""

    @pytest.mark.asyncio
    async def test_returns_competitor_price_summary(
        self,
        service,
        org_id,
        book_id,
    ):
        """get_competitor_prices should return aggregated competitor pricing data."""
        comp1 = MagicMock(
            price=Decimal("4.99"),
            bsr_rank=5000,
            review_rating=4.3,
        )
        comp2 = MagicMock(
            price=Decimal("5.99"),
            bsr_rank=3000,
            review_rating=4.5,
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [comp1, comp2]
        service.db.execute.return_value = mock_result

        result = await service.get_competitor_prices(org_id, book_id)

        assert result.total_competitors == 2
        assert result.avg_price == Decimal("5.49")
        assert result.min_price == Decimal("4.99")
        assert result.max_price == Decimal("5.99")


# ===========================================================================
# Tests: create_ab_test
# ===========================================================================

class TestCreateABTest:
    """Tests for PricingAutomationService.create_ab_test."""

    @pytest.mark.asyncio
    async def test_creates_pricing_ab_test(
        self,
        service,
        org_id,
        book_id,
    ):
        """create_ab_test should create a new pricing A/B test."""
        data = ABTestCreate(
            book_id=book_id,
            name="Price Test",
            description="Test $3.99 vs $4.99",
            price_a=Decimal("3.99"),
            price_b=Decimal("4.99"),
            book_format=BookFormat.EBOOK,
            duration_days=14,
        )

        result = await service.create_ab_test(org_id, data)

        service.db.add.assert_called_once()
        service.db.flush.assert_awaited_once()
        assert result.name == "Price Test"
        assert result.status == ABTestStatus.DRAFT


# ===========================================================================
# Tests: list_promotions
# ===========================================================================

class TestListPromotions:
    """Tests for PricingAutomationService.list_promotions."""

    @pytest.mark.asyncio
    async def test_returns_promotions_with_pagination(
        self,
        service,
        org_id,
    ):
        """list_promotions should return paginated list of promotions."""
        promo1 = MagicMock(id=uuid.uuid4())
        promo2 = MagicMock(id=uuid.uuid4())

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [promo1, promo2, promo1, promo2]

        service.db.execute.side_effect = [mock_result, mock_result]

        promotions, total = await service.list_promotions(org_id, limit=10, offset=0)

        assert len(promotions) == 2
        assert total == 4


# ===========================================================================
# Tests: create_promotion
# ===========================================================================

class TestCreatePromotion:
    """Tests for PricingAutomationService.create_promotion."""

    @pytest.mark.asyncio
    async def test_creates_promotion(
        self,
        service,
        org_id,
        book_id,
    ):
        """create_promotion should create a new promotion."""
        data = PromotionCreate(
            book_id=book_id,
            name="Holiday Sale",
            description="50% off for Black Friday",
            original_price=Decimal("9.99"),
            promo_price=Decimal("4.99"),
            book_format=BookFormat.EBOOK,
            start_date=datetime(2025, 11, 25, tzinfo=UTC),
            end_date=datetime(2025, 11, 28, tzinfo=UTC),
            platform="amazon",
        )

        result = await service.create_promotion(org_id, data)

        service.db.add.assert_called_once()
        service.db.flush.assert_awaited_once()
        assert result.name == "Holiday Sale"


# ===========================================================================
# Tests: calculate_ku_revenue
# ===========================================================================

class TestCalculateKURevenue:
    """Tests for PricingAutomationService.calculate_ku_revenue."""

    @pytest.mark.asyncio
    @patch("app.modules.pricing_automation.service.calculate_ku_vs_wide")
    async def test_calculates_ku_vs_wide_revenue(
        self,
        mock_calculate_ku_vs_wide,
        service,
    ):
        """calculate_ku_revenue should call the KU calculator."""
        mock_calculate_ku_vs_wide.return_value = MagicMock(
            ku_revenue=Decimal("500.00"),
            wide_revenue=Decimal("600.00"),
            recommendation="wide",
        )

        request = KUCalculatorRequest(
            ku_pages_read=50000,
            ku_rate_per_page=Decimal("0.0045"),
            wide_units_sold=100,
            wide_price=Decimal("4.99"),
            wide_royalty_rate=Decimal("0.70"),
        )

        result = await service.calculate_ku_revenue(request)

        assert result.ku_revenue == Decimal("500.00")
        assert result.recommendation == "wide"
        mock_calculate_ku_vs_wide.assert_called_once()
