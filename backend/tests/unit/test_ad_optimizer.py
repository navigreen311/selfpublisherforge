"""Unit tests for the AdOptimizer (bid optimization engine)."""

import pytest
from uuid import uuid4

from app.modules.advertising.optimizer import (
    AdOptimizer,
    CampaignPerformanceData,
    KeywordPerformanceData,
)
from app.modules.advertising.schemas import (
    BidAdjustment,
    OptimizationRequest,
    OptimizationSuggestion,
)


@pytest.fixture
def optimizer():
    """Create an AdOptimizer instance."""
    return AdOptimizer()


@pytest.fixture
def campaign_id():
    return uuid4()


def _make_keyword(
    keyword: str = "test keyword",
    current_bid: float = 1.00,
    impressions: int = 500,
    clicks: int = 25,
    spend: float = 25.0,
    sales: float = 50.0,
    acos: float = 50.0,
    days: int = 14,
) -> KeywordPerformanceData:
    """Helper to create keyword performance data."""
    return KeywordPerformanceData(
        keyword_bid_id=uuid4(),
        keyword=keyword,
        current_bid=current_bid,
        impressions=impressions,
        clicks=clicks,
        spend=spend,
        sales=sales,
        acos=acos,
        days_of_data=days,
    )


class TestCalculateMetrics:
    """Test metric calculation utility methods."""

    def test_calculate_acos_normal(self, optimizer):
        """ACOS is spend/sales * 100."""
        assert optimizer.calculate_acos(25.0, 100.0) == 25.0

    def test_calculate_acos_zero_sales(self, optimizer):
        """ACOS with zero sales and zero spend should be 0."""
        assert optimizer.calculate_acos(0.0, 0.0) == 0.0

    def test_calculate_acos_spend_no_sales(self, optimizer):
        """ACOS with spend but zero sales should be infinity."""
        result = optimizer.calculate_acos(10.0, 0.0)
        assert result == float("inf")

    def test_calculate_roas_normal(self, optimizer):
        """ROAS is sales/spend."""
        assert optimizer.calculate_roas(25.0, 100.0) == 4.0

    def test_calculate_roas_zero_spend(self, optimizer):
        """ROAS with zero spend should be 0."""
        assert optimizer.calculate_roas(0.0, 100.0) == 0.0

    def test_calculate_ctr(self, optimizer):
        """CTR is clicks/impressions * 100."""
        assert optimizer.calculate_ctr(50, 1000) == 5.0

    def test_calculate_ctr_zero_impressions(self, optimizer):
        assert optimizer.calculate_ctr(0, 0) == 0.0

    def test_calculate_cpc(self, optimizer):
        """CPC is spend/clicks."""
        assert optimizer.calculate_cpc(50.0, 100) == 0.5

    def test_calculate_cpc_zero_clicks(self, optimizer):
        assert optimizer.calculate_cpc(50.0, 0) == 0.0

    def test_calculate_conversion_rate(self, optimizer):
        """Conversion rate is orders/clicks * 100."""
        assert optimizer.calculate_conversion_rate(10, 100) == 10.0

    def test_calculate_conversion_rate_zero_clicks(self, optimizer):
        assert optimizer.calculate_conversion_rate(0, 0) == 0.0


class TestOptimizeCampaign:
    """Test the main optimize_campaign method."""

    def test_empty_campaign_no_keywords(self, optimizer, campaign_id):
        """Campaign with no keywords should produce no adjustments."""
        data = CampaignPerformanceData(
            campaign_id=campaign_id,
            campaign_name="Test Campaign",
            keywords=[],
        )
        request = OptimizationRequest(target_acos=30.0)
        result = optimizer.optimize_campaign(data, request)

        assert isinstance(result, OptimizationSuggestion)
        assert result.campaign_id == campaign_id
        assert len(result.bid_adjustments) == 0
        assert len(result.keywords_to_negate) == 0
        assert "No changes recommended" in result.summary

    def test_high_acos_keywords_get_bid_reduction(self, optimizer, campaign_id):
        """Keywords with ACOS significantly above target should get bid reductions."""
        kw = _make_keyword(
            keyword="expensive keyword",
            current_bid=2.00,
            clicks=30,
            spend=60.0,
            sales=60.0,
            acos=80.0,  # above target*1.5 (45%) but below target*3.0 (90%) negation threshold
        )
        data = CampaignPerformanceData(
            campaign_id=campaign_id,
            campaign_name="High ACOS Campaign",
            current_acos=80.0,
            keywords=[kw],
        )
        request = OptimizationRequest(target_acos=30.0)
        result = optimizer.optimize_campaign(data, request)

        assert len(result.bid_adjustments) == 1
        adj = result.bid_adjustments[0]
        assert adj.suggested_bid < adj.current_bid
        assert "exceeds target" in adj.reason.lower() or "ACOS" in adj.reason

    def test_low_acos_keywords_get_bid_increase(self, optimizer, campaign_id):
        """Keywords with ACOS well below target should get bid increases."""
        kw = _make_keyword(
            keyword="efficient keyword",
            current_bid=0.50,
            clicks=50,
            spend=25.0,
            sales=250.0,
            acos=10.0,  # well below 30% target
        )
        data = CampaignPerformanceData(
            campaign_id=campaign_id,
            campaign_name="Low ACOS Campaign",
            current_acos=10.0,
            keywords=[kw],
        )
        request = OptimizationRequest(target_acos=30.0)
        result = optimizer.optimize_campaign(data, request)

        assert len(result.bid_adjustments) == 1
        adj = result.bid_adjustments[0]
        assert adj.suggested_bid > adj.current_bid
        assert "below target" in adj.reason.lower() or "increase" in adj.reason.lower()

    def test_acceptable_acos_no_change(self, optimizer, campaign_id):
        """Keywords with ACOS in acceptable range should not be changed."""
        kw = _make_keyword(
            keyword="good keyword",
            current_bid=1.00,
            clicks=30,
            spend=30.0,
            sales=100.0,
            acos=30.0,  # exactly at target
        )
        data = CampaignPerformanceData(
            campaign_id=campaign_id,
            campaign_name="Good Campaign",
            current_acos=30.0,
            keywords=[kw],
        )
        request = OptimizationRequest(target_acos=30.0)
        result = optimizer.optimize_campaign(data, request)

        assert len(result.bid_adjustments) == 0
        assert len(result.keywords_to_negate) == 0

    def test_zero_sales_many_clicks_gets_negated(self, optimizer, campaign_id):
        """Keywords with many clicks but zero sales should be negated."""
        kw = _make_keyword(
            keyword="wasteful keyword",
            current_bid=1.00,
            clicks=25,  # >= NEGATE_THRESHOLD_CLICKS (20)
            spend=25.0,
            sales=0.0,
            acos=0.0,
        )
        data = CampaignPerformanceData(
            campaign_id=campaign_id,
            campaign_name="Wasteful Campaign",
            keywords=[kw],
        )
        request = OptimizationRequest(target_acos=30.0)
        result = optimizer.optimize_campaign(data, request)

        assert "wasteful keyword" in result.keywords_to_negate

    def test_extremely_high_acos_gets_negated(self, optimizer, campaign_id):
        """Keywords with ACOS > target * 3.0 should be negated."""
        kw = _make_keyword(
            keyword="terrible keyword",
            current_bid=1.00,
            clicks=30,
            spend=100.0,
            sales=10.0,
            acos=1000.0,  # way over target * 3.0 (90%)
        )
        data = CampaignPerformanceData(
            campaign_id=campaign_id,
            campaign_name="Terrible Campaign",
            keywords=[kw],
        )
        request = OptimizationRequest(target_acos=30.0)
        result = optimizer.optimize_campaign(data, request)

        assert "terrible keyword" in result.keywords_to_negate

    def test_insufficient_data_no_action(self, optimizer, campaign_id):
        """Keywords with fewer days than min_data_points should be skipped."""
        kw = _make_keyword(
            keyword="new keyword",
            days=3,  # less than default min_data_points of 7
        )
        data = CampaignPerformanceData(
            campaign_id=campaign_id,
            campaign_name="New Campaign",
            keywords=[kw],
        )
        request = OptimizationRequest(target_acos=30.0, min_data_points=7)
        result = optimizer.optimize_campaign(data, request)

        assert len(result.bid_adjustments) == 0
        assert len(result.keywords_to_negate) == 0

    def test_multiple_keywords_mixed_actions(self, optimizer, campaign_id):
        """Test campaign with multiple keywords needing different actions."""
        keywords = [
            _make_keyword(keyword="reduce_bid", acos=80.0, clicks=30, spend=80, sales=100),
            _make_keyword(keyword="increase_bid", acos=10.0, clicks=30, spend=10, sales=100),
            _make_keyword(keyword="negate_me", acos=0.0, clicks=25, spend=25, sales=0),
            _make_keyword(keyword="keep_same", acos=28.0, clicks=30, spend=28, sales=100),
        ]
        data = CampaignPerformanceData(
            campaign_id=campaign_id,
            campaign_name="Mixed Campaign",
            keywords=keywords,
        )
        request = OptimizationRequest(target_acos=30.0)
        result = optimizer.optimize_campaign(data, request)

        # Should have adjustments for reduce_bid and increase_bid
        adjusted_keywords = {adj.keyword for adj in result.bid_adjustments}
        assert "reduce_bid" in adjusted_keywords
        assert "increase_bid" in adjusted_keywords

        # negate_me should be in negations
        assert "negate_me" in result.keywords_to_negate

        # keep_same should not appear anywhere
        assert "keep_same" not in adjusted_keywords
        assert "keep_same" not in result.keywords_to_negate

    def test_max_bid_increase_respected(self, optimizer, campaign_id):
        """Bid increase should not exceed max_bid_increase_pct."""
        kw = _make_keyword(
            keyword="constrained",
            current_bid=1.00,
            clicks=50,
            spend=10.0,
            sales=200.0,
            acos=5.0,
        )
        data = CampaignPerformanceData(
            campaign_id=campaign_id,
            campaign_name="Constrained Campaign",
            keywords=[kw],
        )
        request = OptimizationRequest(
            target_acos=30.0,
            max_bid_increase_pct=10.0,
        )
        result = optimizer.optimize_campaign(data, request)

        if result.bid_adjustments:
            adj = result.bid_adjustments[0]
            max_allowed = kw.current_bid * 1.10
            assert adj.suggested_bid <= max_allowed + 0.01  # small float tolerance

    def test_max_bid_decrease_respected(self, optimizer, campaign_id):
        """Bid decrease should not exceed max_bid_decrease_pct."""
        kw = _make_keyword(
            keyword="high_acos",
            current_bid=2.00,
            clicks=30,
            spend=60.0,
            sales=60.0,
            acos=100.0,
        )
        data = CampaignPerformanceData(
            campaign_id=campaign_id,
            campaign_name="High ACOS Campaign",
            keywords=[kw],
        )
        request = OptimizationRequest(
            target_acos=30.0,
            max_bid_decrease_pct=15.0,
        )
        result = optimizer.optimize_campaign(data, request)

        if result.bid_adjustments:
            adj = result.bid_adjustments[0]
            min_allowed = kw.current_bid * 0.85
            assert adj.suggested_bid >= min_allowed - 0.01  # small float tolerance

    def test_default_target_acos(self, optimizer, campaign_id):
        """When target_acos is None, should use default of 30%."""
        kw = _make_keyword(acos=80.0, clicks=30, spend=80, sales=100)
        data = CampaignPerformanceData(
            campaign_id=campaign_id,
            campaign_name="Default Target",
            keywords=[kw],
        )
        request = OptimizationRequest(target_acos=None)
        result = optimizer.optimize_campaign(data, request)

        assert result.target_acos == 30.0

    def test_bid_adjustment_has_required_fields(self, optimizer, campaign_id):
        """Verify bid adjustments contain all required fields."""
        kw = _make_keyword(acos=80.0, clicks=30, spend=80, sales=100)
        data = CampaignPerformanceData(
            campaign_id=campaign_id,
            campaign_name="Fields Test",
            keywords=[kw],
        )
        request = OptimizationRequest(target_acos=30.0)
        result = optimizer.optimize_campaign(data, request)

        for adj in result.bid_adjustments:
            assert isinstance(adj, BidAdjustment)
            assert adj.keyword_bid_id is not None
            assert adj.keyword != ""
            assert adj.current_bid > 0
            assert adj.suggested_bid >= 0
            assert adj.reason != ""


class TestBudgetRecommendation:
    """Test budget recommendation logic."""

    def test_recommend_increase_when_acos_below_target(self, optimizer, campaign_id):
        """Should recommend budget increase when ACOS is well below target."""
        data = CampaignPerformanceData(
            campaign_id=campaign_id,
            campaign_name="Efficient Campaign",
            current_acos=15.0,  # well below target * 0.8 = 24%
            total_spend=100.0,
            total_sales=667.0,
            keywords=[_make_keyword()],
        )
        recommendation = optimizer._recommend_budget(data, target_acos=30.0)
        assert recommendation is not None
        # Recommends higher than current daily
        assert recommendation > 0

    def test_recommend_decrease_when_acos_above_target(self, optimizer, campaign_id):
        """Should recommend budget decrease when ACOS is above target."""
        data = CampaignPerformanceData(
            campaign_id=campaign_id,
            campaign_name="Expensive Campaign",
            current_acos=50.0,  # above target * 1.3 = 39%
            total_spend=200.0,
            total_sales=400.0,
            keywords=[_make_keyword()],
        )
        recommendation = optimizer._recommend_budget(data, target_acos=30.0)
        assert recommendation is not None

    def test_no_recommendation_when_acos_in_range(self, optimizer, campaign_id):
        """Should return None when ACOS is in acceptable range."""
        data = CampaignPerformanceData(
            campaign_id=campaign_id,
            campaign_name="Normal Campaign",
            current_acos=28.0,  # in range
            total_spend=100.0,
            total_sales=357.0,
            keywords=[_make_keyword()],
        )
        recommendation = optimizer._recommend_budget(data, target_acos=30.0)
        assert recommendation is None

    def test_no_recommendation_no_data(self, optimizer, campaign_id):
        """Should return None when there is no spend or sales data."""
        data = CampaignPerformanceData(
            campaign_id=campaign_id,
            campaign_name="No Data Campaign",
            total_spend=0.0,
            total_sales=0.0,
        )
        recommendation = optimizer._recommend_budget(data, target_acos=30.0)
        assert recommendation is None


class TestSummaryGeneration:
    """Test summary generation for optimization results."""

    def test_summary_with_adjustments(self, optimizer, campaign_id):
        """Summary should mention number of adjustments."""
        data = CampaignPerformanceData(
            campaign_id=campaign_id,
            campaign_name="Adjust Campaign",
            current_acos=45.0,
        )
        summary = optimizer._generate_summary(data, 30.0, 3, 1)
        assert "3 bid adjustment" in summary
        assert "1" in summary
        assert "above" in summary

    def test_summary_no_changes(self, optimizer, campaign_id):
        """Summary should indicate no changes when none recommended."""
        data = CampaignPerformanceData(
            campaign_id=campaign_id,
            campaign_name="Stable Campaign",
            current_acos=29.0,
        )
        summary = optimizer._generate_summary(data, 30.0, 0, 0)
        assert "No changes recommended" in summary

    def test_summary_below_target(self, optimizer, campaign_id):
        """Summary should indicate ACOS is below target."""
        data = CampaignPerformanceData(
            campaign_id=campaign_id,
            campaign_name="Efficient Campaign",
            current_acos=15.0,
        )
        summary = optimizer._generate_summary(data, 30.0, 1, 0)
        assert "below" in summary


class TestKeywordAnalysis:
    """Test individual keyword analysis edge cases."""

    def test_low_impressions_low_clicks_no_action(self, optimizer):
        """Keywords with very low impressions and clicks should get no action."""
        kw = _make_keyword(
            impressions=50,  # below MIN_IMPRESSIONS_FOR_RELEVANCE
            clicks=3,  # below MIN_CLICKS_FOR_DECISION
            acos=50.0,
        )
        result = optimizer._analyze_keyword(kw, 30.0, 20.0, 30.0)
        assert result is None

    def test_bid_floor_respected(self, optimizer):
        """Suggested bid should never go below $0.02."""
        kw = _make_keyword(
            current_bid=0.05,
            clicks=30,
            spend=50.0,
            sales=10.0,
            acos=500.0,  # Very high, but not enough for negation threshold
        )
        # With 500% ACOS and target 30%, NEGATE_THRESHOLD_ACOS * 30 = 90
        # 500 > 90, so this will be negated
        result = optimizer._analyze_keyword(kw, 30.0, 20.0, 30.0)
        assert result == "negate"

    def test_keyword_with_calculated_acos(self, optimizer):
        """Test keyword where ACOS needs to be calculated from spend/sales."""
        kw = _make_keyword(
            current_bid=1.00,
            clicks=30,
            spend=60.0,
            sales=100.0,
            acos=0.0,  # not pre-calculated; should be computed as 60%
        )
        result = optimizer._analyze_keyword(kw, 30.0, 20.0, 30.0)
        # 60% ACOS > 30% * 1.5 = 45%, so should get a bid reduction
        assert isinstance(result, BidAdjustment)
        assert result.suggested_bid < kw.current_bid
