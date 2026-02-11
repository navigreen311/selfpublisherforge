"""Portfolio-level service: overview, kill/scale, recommendations.

Aggregates data across all books in a portfolio to provide:
- Portfolio overview with key metrics
- Kill/scale decisions for individual books
- AI-powered recommendations for portfolio optimization
"""
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.modules.portfolio_economics.schemas import (
    BookSummary,
    ConfidenceLevel,
    DecisionType,
    KillScaleDecision,
    KillScaleRequest,
    PortfolioOverview,
    PortfolioRecommendation,
)

# ─── Kill/Scale Thresholds ────────────────────────────────────────────────────

KILL_ROI_THRESHOLD = -50.0        # ROI below this suggests killing
SCALE_ROI_THRESHOLD = 50.0        # ROI above this suggests scaling
MAINTAIN_MIN_REVENUE = 50.0       # Minimum monthly revenue to maintain

# Revenue trend thresholds
TREND_DECLINING_THRESHOLD = -0.10  # >10% monthly decline is concerning
TREND_GROWING_THRESHOLD = 0.05    # >5% monthly growth is positive

# Review thresholds
REVIEW_CONCERN_THRESHOLD = 3.5    # Below this rating is concerning
REVIEW_STRONG_THRESHOLD = 4.2     # Above this is strong social proof


def calculate_kill_scale(request: KillScaleRequest) -> KillScaleDecision:
    """Analyze a book and recommend kill, scale, maintain, or revive.

    Decision matrix:
    - KILL: Negative ROI, declining trend, low reviews, high costs
    - SCALE: Positive ROI, growing/stable trend, good reviews
    - MAINTAIN: Breakeven, stable, acceptable performance
    - REVIVE: Was performing well but declining, potential for turnaround
    """
    # Calculate current ROI
    if request.total_investment > 0:
        current_roi = (
            (request.total_revenue_to_date - request.total_investment)
            / request.total_investment * 100
        )
    else:
        current_roi = 100.0 if request.total_revenue_to_date > 0 else 0.0

    # Calculate monthly revenue trend rate
    if request.trend_direction == "up":
        monthly_trend = 0.08  # Approximate 8% growth
    elif request.trend_direction == "down":
        monthly_trend = -0.12  # Approximate 12% decline
    else:
        monthly_trend = 0.0

    # Project future revenue (simple trend projection)
    projected_6m_revenue = sum(
        max(0, request.current_monthly_revenue * ((1 + monthly_trend) ** m))
        for m in range(1, 7)
    )
    projected_12m_revenue = sum(
        max(0, request.current_monthly_revenue * ((1 + monthly_trend) ** m))
        for m in range(1, 13)
    )

    # Scoring factors
    score = 50.0  # Start neutral
    reasoning = []
    actions = []

    # ROI factor (+/- 20 points)
    if current_roi > 200:
        score += 20
        reasoning.append(f"Strong ROI of {current_roi:.0f}%")
    elif current_roi > 100:
        score += 15
        reasoning.append(f"Healthy ROI of {current_roi:.0f}%")
    elif current_roi > 0:
        score += 5
        reasoning.append(f"Positive but modest ROI of {current_roi:.0f}%")
    elif current_roi > -50:
        score -= 10
        reasoning.append(f"Negative ROI of {current_roi:.0f}% -- not yet recouped investment")
    else:
        score -= 20
        reasoning.append(f"Deeply negative ROI of {current_roi:.0f}% -- significant loss")

    # Trend factor (+/- 15 points)
    if request.trend_direction == "up":
        score += 15
        reasoning.append("Revenue trending upward")
    elif request.trend_direction == "down":
        score -= 15
        reasoning.append("Revenue trending downward")
    else:
        reasoning.append("Revenue is flat/stable")

    # Monthly revenue factor (+/- 10 points)
    if request.current_monthly_revenue >= 500:
        score += 10
        reasoning.append(f"Strong monthly revenue of ${request.current_monthly_revenue:.0f}")
    elif request.current_monthly_revenue >= 100:
        score += 5
        reasoning.append(f"Decent monthly revenue of ${request.current_monthly_revenue:.0f}")
    elif request.current_monthly_revenue >= MAINTAIN_MIN_REVENUE:
        reasoning.append(f"Modest monthly revenue of ${request.current_monthly_revenue:.0f}")
    else:
        score -= 10
        reasoning.append(f"Very low monthly revenue of ${request.current_monthly_revenue:.0f}")

    # Review quality factor (+/- 10 points)
    if request.review_rating is not None:
        if request.review_rating >= REVIEW_STRONG_THRESHOLD:
            score += 10
            reasoning.append(f"Excellent reviews ({request.review_rating:.1f} stars, {request.review_count} reviews)")
        elif request.review_rating >= REVIEW_CONCERN_THRESHOLD:
            score += 3
            reasoning.append(f"Acceptable reviews ({request.review_rating:.1f} stars)")
        else:
            score -= 10
            reasoning.append(f"Poor reviews ({request.review_rating:.1f} stars) -- may hurt long-term sales")

    if request.review_count > 100:
        score += 5
        reasoning.append("Strong social proof with 100+ reviews")
    elif request.review_count < 10 and request.months_since_launch > 3:
        score -= 5
        reasoning.append("Very few reviews after launch period")

    # Series factor (+/- 5 points)
    if request.is_series:
        if request.series_position == 1:
            score += 5
            reasoning.append("Book 1 in series -- drives read-through revenue")
        elif request.series_position and request.series_position > 1:
            score += 3
            reasoning.append(f"Series book #{request.series_position} -- benefits from read-through")

    # Marketing efficiency
    if request.monthly_marketing_spend > 0:
        marketing_roi = request.current_monthly_revenue / request.monthly_marketing_spend
        if marketing_roi < 1.0:
            score -= 5
            reasoning.append(f"Marketing spend exceeds revenue (ROI: {marketing_roi:.1f}x)")
            actions.append("Reduce or restructure marketing spend")
        elif marketing_roi > 3.0:
            score += 5
            reasoning.append(f"Efficient marketing (ROI: {marketing_roi:.1f}x)")
            actions.append("Consider increasing marketing budget to scale")

    # Time factor
    if request.months_since_launch < 3:
        reasoning.append("Book is still in launch phase -- give it more time")
        score += 5

    # Clamp score
    score = max(0.0, min(100.0, score))

    # Determine decision
    if score >= 70:
        decision = DecisionType.SCALE
        actions.extend([
            "Increase marketing budget by 50-100%",
            "Run targeted advertising campaigns",
            "Consider audiobook format if not available",
            "Request BookBub featured deal",
        ])
    elif score >= 45:
        decision = DecisionType.MAINTAIN
        actions.extend([
            "Continue current marketing strategy",
            "Monitor trends monthly",
            "Consider minor price optimization",
        ])
    elif score >= 30 and request.months_since_launch > 6:
        # Could be a revive candidate if it had decent performance before
        if current_roi > -20 or request.review_rating and request.review_rating >= 4.0:
            decision = DecisionType.REVIVE
            actions.extend([
                "Refresh book cover and description",
                "Run a limited-time price promotion",
                "Consider new keyword targeting",
                "Seek newsletter swaps or cross-promotions",
            ])
        else:
            decision = DecisionType.KILL
            actions.extend([
                "Stop active marketing spend",
                "Consider unpublishing or enrolling in KU if not already",
                "Redirect resources to better-performing titles",
            ])
    else:
        decision = DecisionType.KILL
        actions.extend([
            "Stop active marketing spend immediately",
            "Consider unpublishing or making exclusive to KU",
            "Use lessons learned for future titles",
            "Redirect investment to higher-ROI books",
        ])

    # Series protection -- never kill book 1 if later books perform
    if decision == DecisionType.KILL and request.is_series and request.series_position == 1:
        decision = DecisionType.MAINTAIN
        reasoning.append("Protected from kill: Book 1 in series drives read-through")
        actions.insert(0, "Maintain book 1 as series entry point even at low individual ROI")

    # Confidence
    if request.months_since_launch >= 6 and request.review_count >= 20:
        confidence = ConfidenceLevel.HIGH
    elif request.months_since_launch >= 3 or request.review_count >= 10:
        confidence = ConfidenceLevel.MEDIUM
    else:
        confidence = ConfidenceLevel.LOW

    # Estimate additional investment/return for scale decisions
    estimated_additional_investment = None
    estimated_additional_return = None
    if decision == DecisionType.SCALE:
        estimated_additional_investment = request.monthly_marketing_spend * 6 + 500
        estimated_additional_return = projected_12m_revenue * 0.3

    return KillScaleDecision(
        book_id=request.book_id,
        decision=decision,
        confidence=confidence,
        score=round(score, 1),
        current_roi=round(current_roi, 1),
        projected_6m_revenue=round(projected_6m_revenue, 2),
        projected_12m_revenue=round(projected_12m_revenue, 2),
        monthly_revenue_trend=round(monthly_trend, 4),
        reasoning=reasoning,
        actions=actions,
        estimated_additional_investment=estimated_additional_investment,
        estimated_additional_return=estimated_additional_return,
        calculated_at=datetime.now(UTC),
    )


def build_portfolio_overview(
    org_id: UUID,
    books: list[dict],
) -> PortfolioOverview:
    """Build a portfolio overview from a list of book data dicts.

    Each book dict should contain:
        book_id, title, genre, monthly_revenue, monthly_units,
        total_revenue, total_investment, launch_date, status
    """
    if not books:
        return PortfolioOverview(org_id=org_id)

    active_books = [b for b in books if b.get("status", "active") == "active"]
    total_revenue = sum(b.get("total_revenue", 0.0) for b in books)
    total_investment = sum(b.get("total_investment", 0.0) for b in books)
    monthly_revenue = sum(b.get("monthly_revenue", 0.0) for b in active_books)

    portfolio_roi = (
        ((total_revenue - total_investment) / total_investment * 100)
        if total_investment > 0 else 0.0
    )

    book_summaries = [
        BookSummary(
            book_id=b.get("book_id", uuid4()),
            title=b.get("title", "Unknown"),
            genre=b.get("genre", "Unknown"),
            launch_date=b.get("launch_date"),
            monthly_revenue=b.get("monthly_revenue", 0.0),
            monthly_units=b.get("monthly_units", 0),
            total_revenue=b.get("total_revenue", 0.0),
            roi=(
                ((b.get("total_revenue", 0) - b.get("total_investment", 0))
                 / b.get("total_investment", 1) * 100)
                if b.get("total_investment", 0) > 0 else 0.0
            ),
            status=b.get("status", "active"),
        )
        for b in books
    ]

    # Sort by monthly revenue for top/under performers
    sorted_books = sorted(book_summaries, key=lambda x: x.monthly_revenue, reverse=True)
    top_performers = sorted_books[:5]
    underperformers = sorted_books[-5:] if len(sorted_books) > 5 else []

    # Genre distribution
    genre_distribution: dict[str, int] = {}
    revenue_by_genre: dict[str, float] = {}
    for b in books:
        genre = b.get("genre", "Unknown")
        genre_distribution[genre] = genre_distribution.get(genre, 0) + 1
        revenue_by_genre[genre] = revenue_by_genre.get(genre, 0.0) + b.get("total_revenue", 0.0)

    # Monthly trend (simplified)
    monthly_trend = 0.0  # Would need historical data for real trend

    return PortfolioOverview(
        org_id=org_id,
        total_books=len(books),
        active_books=len(active_books),
        total_revenue=round(total_revenue, 2),
        total_investment=round(total_investment, 2),
        portfolio_roi=round(portfolio_roi, 1),
        monthly_revenue=round(monthly_revenue, 2),
        monthly_trend=round(monthly_trend, 4),
        top_performers=top_performers,
        underperformers=underperformers,
        genre_distribution=genre_distribution,
        revenue_by_genre={k: round(v, 2) for k, v in revenue_by_genre.items()},
        updated_at=datetime.now(UTC),
    )


def generate_portfolio_recommendations(
    overview: PortfolioOverview,
) -> list[PortfolioRecommendation]:
    """Generate AI-powered recommendations based on portfolio analysis."""
    recommendations: list[PortfolioRecommendation] = []

    # Diversification analysis
    if overview.total_books > 0 and len(overview.genre_distribution) == 1:
        genre = list(overview.genre_distribution.keys())[0]
        recommendations.append(PortfolioRecommendation(
            category="diversification",
            priority="high",
            title="Diversify your genre portfolio",
            description=(
                f"All {overview.total_books} books are in {genre}. "
                "Consider expanding to adjacent genres to reduce risk."
            ),
            estimated_impact="Reduce single-genre dependency by 30-50%",
            actions=[
                f"Research genres adjacent to {genre}",
                "Start with a single book in a new genre to test",
                "Consider cross-genre appeal in future book ideas",
            ],
        ))
    elif overview.total_books >= 5:
        # Check for genre concentration
        max_genre_count = max(overview.genre_distribution.values()) if overview.genre_distribution else 0
        concentration = max_genre_count / overview.total_books if overview.total_books > 0 else 0
        if concentration > 0.7:
            dominant_genre = max(
                overview.genre_distribution,
                key=lambda k: overview.genre_distribution.get(k, 0)  # type: ignore[arg-type]
            )
            recommendations.append(PortfolioRecommendation(
                category="diversification",
                priority="medium",
                title="Genre concentration risk",
                description=(
                    f"{concentration:.0%} of your books are in {dominant_genre}. "
                    "Consider diversifying to protect against genre market shifts."
                ),
                estimated_impact="Reduce genre risk exposure",
                actions=[
                    "Write 1-2 books in a complementary genre",
                    "Use pen names if needed for genre separation",
                ],
            ))

    # ROI optimization
    if overview.portfolio_roi < 0:
        recommendations.append(PortfolioRecommendation(
            category="optimization",
            priority="high",
            title="Negative portfolio ROI",
            description=(
                f"Portfolio ROI is {overview.portfolio_roi:.0f}%. "
                "Review underperforming books and consider killing or reviving them."
            ),
            estimated_impact="Potential to recover 20-40% of losses",
            actions=[
                "Run kill/scale analysis on each underperforming book",
                "Stop marketing spend on books with no traction",
                "Invest in cover refreshes for books with good content but poor sales",
            ],
        ))
    elif overview.portfolio_roi < 50:
        recommendations.append(PortfolioRecommendation(
            category="optimization",
            priority="medium",
            title="Portfolio ROI below target",
            description=(
                f"Portfolio ROI is {overview.portfolio_roi:.0f}%. "
                "Focus on scaling top performers and optimizing pricing."
            ),
            actions=[
                "Double down on marketing for top 3 books",
                "Test price increases on books with high review ratings",
                "Consider bundling underperformers with top sellers",
            ],
        ))

    # Growth opportunities
    if overview.total_books < 5:
        recommendations.append(PortfolioRecommendation(
            category="growth",
            priority="high",
            title="Build your backlist",
            description=(
                f"You have {overview.total_books} book(s). "
                "Growing to 5+ books creates significant compounding revenue effects."
            ),
            estimated_impact="Backlist of 5+ books typically 2-3x total revenue",
            actions=[
                "Aim to publish at least 3-4 books per year",
                "Consider series to leverage read-through",
                "Use rapid-release strategy for new series",
            ],
        ))

    # Underperformer analysis
    if overview.underperformers:
        low_revenue = [b for b in overview.underperformers if b.monthly_revenue < 20]
        if low_revenue:
            recommendations.append(PortfolioRecommendation(
                category="risk",
                priority="medium",
                title=f"{len(low_revenue)} books earning under $20/month",
                description=(
                    "These books may be dragging down portfolio efficiency. "
                    "Evaluate whether to invest in reviving them or reallocate resources."
                ),
                actions=[
                    "Run kill/scale analysis on each low-performer",
                    "Consider cover and blurb refreshes",
                    "Evaluate keyword and category targeting",
                ],
            ))

    return recommendations
