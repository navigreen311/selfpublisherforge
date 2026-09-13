"""AI bid optimization engine for advertising campaigns.

Analyzes performance data, suggests bid adjustments, and enforces ACOS targets.
Uses statistical analysis and optional LLM-assisted strategy recommendations.
"""

import logging
from dataclasses import dataclass, field
from uuid import UUID

from app.modules.advertising.schemas import (
    BidAdjustment,
    OptimizationRequest,
    OptimizationSuggestion,
)

logger = logging.getLogger(__name__)


@dataclass
class KeywordPerformanceData:
    """Aggregated performance data for a single keyword."""

    keyword_bid_id: UUID
    keyword: str
    current_bid: float
    impressions: int = 0
    clicks: int = 0
    spend: float = 0.0
    sales: float = 0.0
    orders: int = 0
    acos: float = 0.0
    days_of_data: int = 0


@dataclass
class CampaignPerformanceData:
    """Aggregated campaign-level performance data."""

    campaign_id: UUID
    campaign_name: str
    current_acos: float = 0.0
    total_spend: float = 0.0
    total_sales: float = 0.0
    total_impressions: int = 0
    total_clicks: int = 0
    keywords: list[KeywordPerformanceData] = field(default_factory=list)


class AdOptimizer:
    """Bid optimization engine that analyzes performance and suggests changes.

    Strategy:
    1. Calculate keyword-level ACOS
    2. Compare against target ACOS
    3. Suggest bid adjustments proportional to deviation
    4. Identify underperforming keywords for negation
    5. Suggest new keywords from search term data
    """

    # Thresholds for keyword classification
    HIGH_ACOS_MULTIPLIER = 1.5  # keyword ACOS > target * 1.5 = reduce bid
    LOW_ACOS_MULTIPLIER = 0.7  # keyword ACOS < target * 0.7 = increase bid
    MIN_CLICKS_FOR_DECISION = 10  # minimum clicks to make a bid decision
    MIN_IMPRESSIONS_FOR_RELEVANCE = 100  # minimum impressions to consider keyword
    NEGATE_THRESHOLD_CLICKS = 20  # clicks with 0 sales -> negate
    NEGATE_THRESHOLD_ACOS = 3.0  # ACOS > target * 3.0 -> negate

    def optimize_campaign(
        self,
        campaign_data: CampaignPerformanceData,
        request: OptimizationRequest,
    ) -> OptimizationSuggestion:
        """Run optimization analysis on a campaign and return suggestions.

        Args:
            campaign_data: Aggregated performance data for the campaign.
            request: Optimization parameters (target ACOS, bid limits, etc.).

        Returns:
            OptimizationSuggestion with bid adjustments and recommendations.
        """
        target_acos = request.target_acos or 30.0  # default 30% ACOS target
        bid_adjustments: list[BidAdjustment] = []
        keywords_to_negate: list[str] = []
        keywords_to_add: list[str] = []

        for kw_data in campaign_data.keywords:
            # Skip keywords without enough data
            if kw_data.days_of_data < request.min_data_points:
                continue

            adjustment = self._analyze_keyword(
                kw_data=kw_data,
                target_acos=target_acos,
                max_increase_pct=request.max_bid_increase_pct,
                max_decrease_pct=request.max_bid_decrease_pct,
            )

            if adjustment is not None:
                if isinstance(adjustment, str) and adjustment == "negate":
                    keywords_to_negate.append(kw_data.keyword)
                elif isinstance(adjustment, BidAdjustment):
                    bid_adjustments.append(adjustment)  # type: ignore[arg-type]

        # Calculate budget recommendation
        budget_recommendation = self._recommend_budget(
            campaign_data=campaign_data,
            target_acos=target_acos,
        )

        # Generate summary
        summary = self._generate_summary(
            campaign_data=campaign_data,
            target_acos=target_acos,
            num_adjustments=len(bid_adjustments),
            num_negations=len(keywords_to_negate),
        )

        return OptimizationSuggestion(
            campaign_id=campaign_data.campaign_id,
            campaign_name=campaign_data.campaign_name,
            current_acos=campaign_data.current_acos,
            target_acos=target_acos,
            bid_adjustments=bid_adjustments,
            keywords_to_add=keywords_to_add,
            keywords_to_negate=keywords_to_negate,
            budget_recommendation=budget_recommendation,
            summary=summary,
        )

    def _analyze_keyword(
        self,
        kw_data: KeywordPerformanceData,
        target_acos: float,
        max_increase_pct: float,
        max_decrease_pct: float,
    ) -> BidAdjustment | str | None:
        """Analyze a single keyword and return a bid adjustment or 'negate'.

        Returns:
            BidAdjustment if bid should change, 'negate' if keyword should be
            negated, or None if no action needed.
        """
        # Case 1: Keyword has clicks but zero sales (potential waste)
        if kw_data.clicks >= self.NEGATE_THRESHOLD_CLICKS and kw_data.sales == 0:
            return "negate"

        # Case 2: Not enough clicks to make a decision
        if kw_data.clicks < self.MIN_CLICKS_FOR_DECISION:
            # Low impressions too -> no action
            if kw_data.impressions < self.MIN_IMPRESSIONS_FOR_RELEVANCE:
                return None
            # Has impressions but few clicks -> might need higher bid for visibility
            # but not enough data to decide
            return None

        # Calculate keyword ACOS
        kw_acos = kw_data.acos
        if kw_acos == 0 and kw_data.spend > 0 and kw_data.sales > 0:
            kw_acos = (kw_data.spend / kw_data.sales) * 100

        # Case 3: ACOS way too high -> negate
        if kw_acos > target_acos * self.NEGATE_THRESHOLD_ACOS:
            return "negate"

        # Case 4: ACOS above target -> reduce bid
        if kw_acos > target_acos * self.HIGH_ACOS_MULTIPLIER:
            reduction_factor = min(
                max_decrease_pct / 100,
                (kw_acos - target_acos) / (kw_acos * 2),
            )
            suggested_bid = max(
                0.02,  # minimum bid floor
                kw_data.current_bid * (1 - reduction_factor),
            )
            expected_impact = -(kw_acos - target_acos) * reduction_factor
            return BidAdjustment(
                keyword_bid_id=kw_data.keyword_bid_id,
                keyword=kw_data.keyword,
                current_bid=kw_data.current_bid,
                suggested_bid=round(suggested_bid, 2),
                reason=f"ACOS {kw_acos:.1f}% exceeds target {target_acos:.1f}%. Reducing bid by {reduction_factor*100:.0f}%.",
                expected_acos_impact=round(expected_impact, 2),
            )

        # Case 5: ACOS well below target -> increase bid (capture more volume)
        if kw_acos < target_acos * self.LOW_ACOS_MULTIPLIER and kw_data.sales > 0:
            headroom = target_acos - kw_acos
            increase_factor = min(
                max_increase_pct / 100,
                headroom / (target_acos * 2),
            )
            suggested_bid = kw_data.current_bid * (1 + increase_factor)
            expected_impact = headroom * increase_factor * 0.5
            return BidAdjustment(
                keyword_bid_id=kw_data.keyword_bid_id,
                keyword=kw_data.keyword,
                current_bid=kw_data.current_bid,
                suggested_bid=round(suggested_bid, 2),
                reason=f"ACOS {kw_acos:.1f}% is well below target {target_acos:.1f}%. Increasing bid by {increase_factor*100:.0f}% to capture more volume.",
                expected_acos_impact=round(expected_impact, 2),
            )

        # Case 6: ACOS in acceptable range -> no change
        return None

    def _recommend_budget(
        self,
        campaign_data: CampaignPerformanceData,
        target_acos: float,
    ) -> float | None:
        """Recommend a daily budget based on performance.

        Returns None if insufficient data.
        """
        if campaign_data.total_spend == 0 or campaign_data.total_sales == 0:
            return None

        # If ACOS is below target, we can afford to spend more
        if campaign_data.current_acos < target_acos * 0.8:
            # Recommend 20% budget increase
            current_daily = campaign_data.total_spend / max(1, len(campaign_data.keywords))
            return round(current_daily * 1.2, 2)

        # If ACOS is above target, recommend reducing budget
        if campaign_data.current_acos > target_acos * 1.3:
            current_daily = campaign_data.total_spend / max(1, len(campaign_data.keywords))
            return round(current_daily * 0.8, 2)

        return None

    def _generate_summary(
        self,
        campaign_data: CampaignPerformanceData,
        target_acos: float,
        num_adjustments: int,
        num_negations: int,
    ) -> str:
        """Generate a human-readable summary of the optimization."""
        parts = [f"Campaign '{campaign_data.campaign_name}' analysis:"]

        if campaign_data.current_acos > 0:
            acos_status = "above" if campaign_data.current_acos > target_acos else "below"
            parts.append(
                f"Current ACOS {campaign_data.current_acos:.1f}% is {acos_status} " f"the target of {target_acos:.1f}%."
            )

        if num_adjustments > 0:
            parts.append(f"Suggested {num_adjustments} bid adjustment(s).")

        if num_negations > 0:
            parts.append(f"Recommended negating {num_negations} underperforming keyword(s).")

        if num_adjustments == 0 and num_negations == 0:
            parts.append("No changes recommended at this time.")

        return " ".join(parts)

    def calculate_acos(self, spend: float, sales: float) -> float:
        """Calculate Advertising Cost of Sale (ACOS) percentage."""
        if sales == 0:
            return 0.0 if spend == 0 else float("inf")
        return round((spend / sales) * 100, 2)

    def calculate_roas(self, spend: float, sales: float) -> float:
        """Calculate Return on Ad Spend (ROAS)."""
        if spend == 0:
            return 0.0
        return round(sales / spend, 2)

    def calculate_ctr(self, clicks: int, impressions: int) -> float:
        """Calculate Click-Through Rate (CTR) percentage."""
        if impressions == 0:
            return 0.0
        return round((clicks / impressions) * 100, 2)

    def calculate_cpc(self, spend: float, clicks: int) -> float:
        """Calculate Cost Per Click (CPC)."""
        if clicks == 0:
            return 0.0
        return round(spend / clicks, 2)

    def calculate_conversion_rate(self, orders: int, clicks: int) -> float:
        """Calculate conversion rate percentage."""
        if clicks == 0:
            return 0.0
        return round((orders / clicks) * 100, 2)
