"""Unit tests for the niche scoring algorithm.

Tests verify that:
  - Demand, supply, and opportunity scores are in [0, 100].
  - Higher search volume / lower BSR produce higher demand scores.
  - More competing titles / higher review barriers produce higher supply scores.
  - Opportunity score reflects the combination of demand and supply.
  - Edge cases (zero values, empty lists) are handled gracefully.
  - Recommendations match score thresholds.
"""


from app.modules.market_intelligence.scoring import (
    NicheMetrics,
    NicheScores,
    _clamp,
    _compute_demand,
    _compute_opportunity,
    _compute_supply,
    _generate_recommendation,
    _sigmoid_scale,
    calculate_niche_scores,
)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _scores(metrics: NicheMetrics) -> NicheScores:
    return calculate_niche_scores(metrics)


# ---------------------------------------------------------------------------
# Tests: _clamp
# ---------------------------------------------------------------------------

class TestClamp:
    def test_within_range(self):
        assert _clamp(50) == 50

    def test_below_min(self):
        assert _clamp(-10) == 0

    def test_above_max(self):
        assert _clamp(150) == 100

    def test_boundary_values(self):
        assert _clamp(0) == 0
        assert _clamp(100) == 100


# ---------------------------------------------------------------------------
# Tests: _sigmoid_scale
# ---------------------------------------------------------------------------

class TestSigmoidScale:
    def test_at_midpoint_is_50(self):
        result = _sigmoid_scale(5000, midpoint=5000, steepness=0.001)
        assert 49 < result < 51

    def test_above_midpoint_gt_50(self):
        result = _sigmoid_scale(10000, midpoint=5000, steepness=0.001)
        assert result > 50

    def test_below_midpoint_lt_50(self):
        result = _sigmoid_scale(1000, midpoint=5000, steepness=0.001)
        assert result < 50


# ---------------------------------------------------------------------------
# Tests: Demand score
# ---------------------------------------------------------------------------

class TestDemandScore:
    def test_high_search_volume_increases_demand(self):
        low_sv = NicheMetrics(avg_monthly_search_volume=500)
        high_sv = NicheMetrics(avg_monthly_search_volume=50000)
        assert _compute_demand(high_sv) > _compute_demand(low_sv)

    def test_low_bsr_increases_demand(self):
        low_bsr = NicheMetrics(bsr_values=[500, 1000, 2000])
        high_bsr = NicheMetrics(bsr_values=[100000, 200000, 300000])
        assert _compute_demand(low_bsr) > _compute_demand(high_bsr)

    def test_positive_trend_increases_demand(self):
        declining = NicheMetrics(trend_slope=-0.2)
        growing = NicheMetrics(trend_slope=0.2)
        assert _compute_demand(growing) > _compute_demand(declining)

    def test_empty_bsr_values_uses_neutral(self):
        m = NicheMetrics(bsr_values=[], avg_monthly_search_volume=5000)
        score = _compute_demand(m)
        assert 0 <= score <= 100

    def test_demand_in_range(self):
        m = NicheMetrics(
            avg_monthly_search_volume=10000,
            bsr_values=[1000, 5000, 10000],
            trend_slope=0.1,
        )
        score = _compute_demand(m)
        assert 0 <= score <= 100


# ---------------------------------------------------------------------------
# Tests: Supply score
# ---------------------------------------------------------------------------

class TestSupplyScore:
    def test_more_titles_increases_supply(self):
        few = NicheMetrics(total_competing_titles=50)
        many = NicheMetrics(total_competing_titles=5000)
        assert _compute_supply(many) > _compute_supply(few)

    def test_high_review_barrier_increases_supply(self):
        low_reviews = NicheMetrics(top_10_avg_reviews=20)
        high_reviews = NicheMetrics(top_10_avg_reviews=2000)
        assert _compute_supply(high_reviews) > _compute_supply(low_reviews)

    def test_high_rating_increases_supply(self):
        low_rating = NicheMetrics(avg_rating=3.0)
        high_rating = NicheMetrics(avg_rating=4.8)
        assert _compute_supply(high_rating) > _compute_supply(low_rating)

    def test_supply_in_range(self):
        m = NicheMetrics(
            total_competing_titles=500,
            top_10_avg_reviews=200,
            avg_rating=4.2,
        )
        score = _compute_supply(m)
        assert 0 <= score <= 100


# ---------------------------------------------------------------------------
# Tests: Opportunity score
# ---------------------------------------------------------------------------

class TestOpportunityScore:
    def test_high_demand_low_supply_gives_high_opportunity(self):
        score = _compute_opportunity(demand=90, supply=20)
        assert score > 70

    def test_low_demand_high_supply_gives_low_opportunity(self):
        score = _compute_opportunity(demand=20, supply=90)
        assert score < 20

    def test_opportunity_in_range(self):
        for d in [0, 25, 50, 75, 100]:
            for s in [0, 25, 50, 75, 100]:
                score = _compute_opportunity(d, s)
                assert 0 <= score <= 100, f"Out of range for demand={d}, supply={s}: {score}"


# ---------------------------------------------------------------------------
# Tests: Recommendation
# ---------------------------------------------------------------------------

class TestRecommendation:
    def test_excellent_opportunity(self):
        rec = _generate_recommendation(80, 20, 80)
        assert "Excellent" in rec

    def test_good_opportunity(self):
        rec = _generate_recommendation(60, 40, 60)
        assert "Good" in rec

    def test_moderate_opportunity(self):
        rec = _generate_recommendation(45, 50, 40)
        assert "Moderate" in rec

    def test_challenging_opportunity(self):
        rec = _generate_recommendation(20, 80, 10)
        assert "Challenging" in rec


# ---------------------------------------------------------------------------
# Tests: End-to-end calculate_niche_scores
# ---------------------------------------------------------------------------

class TestCalculateNicheScores:
    def test_returns_niche_scores_dataclass(self):
        m = NicheMetrics()
        result = calculate_niche_scores(m)
        assert isinstance(result, NicheScores)

    def test_all_scores_in_range(self):
        m = NicheMetrics(
            avg_monthly_search_volume=10000,
            bsr_values=[1000, 5000, 10000, 50000, 100000],
            trend_slope=0.05,
            total_competing_titles=300,
            avg_review_count=150,
            avg_rating=4.0,
            top_10_avg_reviews=500,
            avg_price=9.99,
        )
        result = calculate_niche_scores(m)
        assert 0 <= result.demand_score <= 100
        assert 0 <= result.supply_score <= 100
        assert 0 <= result.opportunity_score <= 100
        assert len(result.recommendation) > 0

    def test_zero_metrics(self):
        m = NicheMetrics()
        result = calculate_niche_scores(m)
        assert 0 <= result.demand_score <= 100
        assert 0 <= result.supply_score <= 100
        assert 0 <= result.opportunity_score <= 100

    def test_extreme_high_metrics(self):
        m = NicheMetrics(
            avg_monthly_search_volume=1_000_000,
            bsr_values=[1, 2, 3, 4, 5],
            trend_slope=1.0,
            total_competing_titles=100_000,
            avg_review_count=10000,
            avg_rating=5.0,
            top_10_avg_reviews=50000,
            avg_price=99.99,
        )
        result = calculate_niche_scores(m)
        assert 0 <= result.demand_score <= 100
        assert 0 <= result.supply_score <= 100
        assert 0 <= result.opportunity_score <= 100

    def test_good_niche_scenario(self):
        """High demand, low competition -> high opportunity."""
        m = NicheMetrics(
            avg_monthly_search_volume=30000,
            bsr_values=[2000, 5000, 8000],
            trend_slope=0.15,
            total_competing_titles=50,
            avg_review_count=30,
            avg_rating=3.5,
            top_10_avg_reviews=40,
            avg_price=9.99,
        )
        result = calculate_niche_scores(m)
        assert result.opportunity_score > 50
        assert result.demand_score > result.supply_score

    def test_bad_niche_scenario(self):
        """Low demand, high competition -> low opportunity."""
        m = NicheMetrics(
            avg_monthly_search_volume=200,
            bsr_values=[200000, 300000, 400000],
            trend_slope=-0.3,
            total_competing_titles=10000,
            avg_review_count=2000,
            avg_rating=4.7,
            top_10_avg_reviews=5000,
            avg_price=5.99,
        )
        result = calculate_niche_scores(m)
        assert result.opportunity_score < 40
        assert result.supply_score > result.demand_score
