"""Service layer for the Market Intelligence Engine.

Orchestrates the Amazon client, scoring algorithm, and database
interactions to implement niche analysis, keyword research, and
competitor tracking.
"""

from __future__ import annotations

import statistics
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.modules.market_intelligence.amazon_client import (
    AmazonClientBase,
    get_amazon_client,
)
from app.modules.market_intelligence.schemas import (
    BSRHistoryPoint,
    CategoryAnalysis,
    CategoryNode,
    CompetitorDetail,
    CompetitorListItem,
    CompetitorSummary,
    CompetitorTrackRequest,
    GapAnalysisItem,
    KeywordData,
    KeywordResearchRequest,
    KeywordResearchResponse,
    KeywordSuggestionsParams,
    MarketSnapshot,
    MarketTrend,
    MarketTrendsResponse,
    NicheAnalysisRequest,
    NicheAnalysisResponse,
    TrendDataPoint,
    TrendDirection,
)
from app.modules.market_intelligence.scoring import (
    NicheMetrics,
    calculate_niche_scores,
)


class MarketIntelligenceService:
    """Stateless service -- instantiated per-request with a client."""

    def __init__(self, client: Optional[AmazonClientBase] = None) -> None:
        self._client = client or get_amazon_client()

    # ------------------------------------------------------------------
    # Categories
    # ------------------------------------------------------------------

    async def get_categories(
        self, root_id: Optional[str] = None, marketplace: str = "US"
    ) -> list[CategoryNode]:
        raw = await self._client.get_category_tree(root_id=root_id, marketplace=marketplace)
        return [self._map_category(c) for c in raw]

    async def get_category_analysis(
        self, category_id: str, marketplace: str = "US"
    ) -> CategoryAnalysis:
        products = await self._client.search_products(
            keywords="", category_id=category_id, marketplace=marketplace, max_results=20
        )
        bsr_values = [p.bsr for p in products if p.bsr is not None]
        prices = [p.price for p in products if p.price is not None]
        reviews = [p.reviews_count for p in products]
        ratings = [p.rating for p in products if p.rating is not None]

        avg_bsr = statistics.mean(bsr_values) if bsr_values else 0
        median_bsr = statistics.median(bsr_values) if bsr_values else 0

        # BSR distribution buckets
        buckets = {"1-1000": 0, "1001-5000": 0, "5001-20000": 0, "20001-100000": 0, "100001+": 0}
        for b in bsr_values:
            if b <= 1000:
                buckets["1-1000"] += 1
            elif b <= 5000:
                buckets["1001-5000"] += 1
            elif b <= 20000:
                buckets["5001-20000"] += 1
            elif b <= 100000:
                buckets["20001-100000"] += 1
            else:
                buckets["100001+"] += 1

        competition_score = self._estimate_competition(products)

        # Get category name from tree (best effort)
        cats = await self._client.get_category_tree(root_id=category_id, marketplace=marketplace)
        cat_name = cats[0]["name"] if cats else f"Category {category_id}"

        return CategoryAnalysis(
            category_id=category_id,
            category_name=cat_name,
            book_count=len(products),
            avg_bsr=round(avg_bsr, 2),
            median_bsr=round(median_bsr, 2),
            avg_price=round(statistics.mean(prices), 2) if prices else 0,
            avg_reviews=round(statistics.mean(reviews), 2) if reviews else 0,
            avg_rating=round(statistics.mean(ratings), 2) if ratings else 0,
            competition_score=round(competition_score, 2),
            bsr_distribution=buckets,
            top_books=sorted(products, key=lambda p: p.bsr or 999999)[:5],
        )

    # ------------------------------------------------------------------
    # Keywords
    # ------------------------------------------------------------------

    async def research_keywords(
        self, request: KeywordResearchRequest
    ) -> KeywordResearchResponse:
        keyword_data = await self._client.get_keyword_data(
            request.keywords, marketplace=request.marketplace
        )
        return KeywordResearchResponse(
            keywords=keyword_data,
            marketplace=request.marketplace,
            generated_at=datetime.now(tz=timezone.utc),
        )

    async def suggest_keywords(
        self, params: KeywordSuggestionsParams
    ) -> list[KeywordData]:
        """AI-suggested keywords for a genre / niche.

        In a full implementation this would call an LLM to generate
        suggestions.  For now, we expand the genre into common modifier
        patterns and look up their data.
        """
        modifiers = [
            "",
            "books",
            "best",
            "new",
            "top rated",
            "bestselling",
            "guide",
            "how to",
            "for beginners",
            "2024",
        ]
        base = params.niche or params.genre
        expanded = [f"{base} {m}".strip() for m in modifiers][: params.limit]
        return await self._client.get_keyword_data(expanded)

    # ------------------------------------------------------------------
    # Niche analysis
    # ------------------------------------------------------------------

    async def analyze_niche(
        self, request: NicheAnalysisRequest
    ) -> NicheAnalysisResponse:
        # 1. Fetch products matching the niche
        products = await self._client.search_products(
            keywords=request.niche,
            category_id=request.category_id,
            marketplace=request.marketplace,
            max_results=20,
        )

        # 2. Fetch keyword data
        kw_data = await self._client.get_keyword_data(
            [request.niche], marketplace=request.marketplace
        )

        # 3. Assemble metrics
        bsr_values = [p.bsr for p in products if p.bsr is not None]
        reviews = [p.reviews_count for p in products]
        ratings = [p.rating for p in products if p.rating is not None]
        prices = [p.price for p in products if p.price is not None]

        top_10_reviews = sorted(reviews, reverse=True)[:10]

        search_volume = kw_data[0].search_volume if kw_data else 0
        trend_slope = 0.0
        if kw_data and len(kw_data[0].trend_data) >= 2:
            td = kw_data[0].trend_data
            trend_slope = (td[-1] - td[0]) / max(td[0], 1)

        metrics = NicheMetrics(
            avg_monthly_search_volume=search_volume,
            bsr_values=bsr_values,
            trend_slope=trend_slope,
            total_competing_titles=len(products),
            avg_review_count=statistics.mean(reviews) if reviews else 0,
            avg_rating=statistics.mean(ratings) if ratings else 0,
            top_10_avg_reviews=statistics.mean(top_10_reviews) if top_10_reviews else 0,
            avg_price=statistics.mean(prices) if prices else 0,
        )

        scores = calculate_niche_scores(metrics)

        # 4. Gap analysis
        gap_analysis = self._generate_gap_analysis(products, scores)

        # 5. Top competitors
        top_competitors = sorted(products, key=lambda p: p.bsr or 999999)[:5]

        return NicheAnalysisResponse(
            niche=request.niche,
            demand_score=scores.demand_score,
            supply_score=scores.supply_score,
            opportunity_score=scores.opportunity_score,
            top_competitors=top_competitors,
            gap_analysis=gap_analysis,
            avg_monthly_revenue=round(metrics.avg_price * search_volume * 0.03, 2) if search_volume else None,
            avg_bsr=round(statistics.mean(bsr_values), 2) if bsr_values else None,
            recommendation=scores.recommendation,
            analyzed_at=datetime.now(tz=timezone.utc),
        )

    # ------------------------------------------------------------------
    # Competitors
    # ------------------------------------------------------------------

    # In-memory store for development (would use DB in production)
    _tracked: dict[str, CompetitorDetail] = {}

    async def list_competitors(self, marketplace: str = "US") -> list[CompetitorListItem]:
        return [
            CompetitorListItem(
                id=c.id,
                asin=c.asin,
                title=c.title,
                author=c.author,
                bsr=c.bsr,
                price=c.price,
                reviews_count=c.reviews_count,
                rating=c.rating,
                marketplace=c.marketplace,
                tracked_since=c.tracked_since,
            )
            for c in self._tracked.values()
            if c.marketplace == marketplace
        ]

    async def track_competitor(
        self, request: CompetitorTrackRequest
    ) -> CompetitorDetail:
        # Check if already tracked
        for existing in self._tracked.values():
            if existing.asin == request.asin and existing.marketplace == request.marketplace:
                return existing

        product = await self._client.get_product_detail(
            request.asin, marketplace=request.marketplace
        )
        if not product:
            raise ValueError(f"Product {request.asin} not found")

        bsr_history = await self._client.get_bsr_history(
            request.asin, days=30, marketplace=request.marketplace
        )

        now = datetime.now(tz=timezone.utc)
        detail = CompetitorDetail(
            id=uuid.uuid4(),
            asin=product.asin,
            title=product.title,
            author=product.author,
            bsr=product.bsr,
            price=product.price,
            reviews_count=product.reviews_count,
            rating=product.rating,
            image_url=product.image_url,
            marketplace=request.marketplace,
            bsr_history=bsr_history,
            tracked_since=now,
            last_updated=now,
        )
        self._tracked[f"{request.asin}:{request.marketplace}"] = detail
        return detail

    async def get_competitor(
        self, competitor_id: uuid.UUID
    ) -> Optional[CompetitorDetail]:
        for c in self._tracked.values():
            if c.id == competitor_id:
                return c
        return None

    # ------------------------------------------------------------------
    # Trends & Snapshots
    # ------------------------------------------------------------------

    async def get_trends(
        self,
        category_id: Optional[str] = None,
        keyword: Optional[str] = None,
        days: int = 30,
    ) -> MarketTrendsResponse:
        now = datetime.now(tz=timezone.utc)
        trends: list[MarketTrend] = []

        if keyword:
            kw_data = await self._client.get_keyword_data([keyword])
            if kw_data:
                kd = kw_data[0]
                data_points = [
                    TrendDataPoint(
                        date=now - __import__("datetime").timedelta(days=30 * (len(kd.trend_data) - 1 - i)),
                        value=v,
                    )
                    for i, v in enumerate(kd.trend_data)
                ]
                change_pct = 0.0
                if kd.trend_data and kd.trend_data[0] > 0:
                    change_pct = round(
                        ((kd.trend_data[-1] - kd.trend_data[0]) / kd.trend_data[0]) * 100, 2
                    )
                trends.append(
                    MarketTrend(
                        label=f"Keyword: {keyword}",
                        keyword=keyword,
                        direction=kd.trend,
                        data_points=data_points,
                        change_pct=change_pct,
                    )
                )

        if category_id:
            analysis = await self.get_category_analysis(category_id)
            trends.append(
                MarketTrend(
                    label=f"Category: {analysis.category_name}",
                    category_id=category_id,
                    direction=TrendDirection.STABLE,
                    data_points=[],
                    change_pct=0,
                )
            )

        period_start = now - __import__("datetime").timedelta(days=days)
        return MarketTrendsResponse(
            trends=trends, period_start=period_start, period_end=now
        )

    async def get_snapshots(
        self,
        category_id: Optional[str] = None,
        limit: int = 30,
    ) -> list[MarketSnapshot]:
        """Return recent market snapshots.

        In production these would come from the database (populated by
        the Celery task ``generate_market_snapshot``).  Here we generate
        synthetic data.
        """
        import random as _random
        from datetime import timedelta

        now = datetime.now(tz=timezone.utc)
        rng = _random.Random(42)
        cat_id = category_id or "154606011"
        snapshots: list[MarketSnapshot] = []

        for i in range(limit):
            snapshots.append(
                MarketSnapshot(
                    id=uuid.uuid4(),
                    category_id=cat_id,
                    category_name="Self-Help",
                    snapshot_date=now - timedelta(days=i),
                    avg_bsr=round(rng.uniform(10000, 80000), 2),
                    avg_price=round(rng.uniform(4.99, 14.99), 2),
                    book_count=rng.randint(1000, 20000),
                    avg_reviews=round(rng.uniform(50, 500), 2),
                    competition_score=round(rng.uniform(30, 85), 2),
                )
            )
        return snapshots

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _map_category(raw: dict) -> CategoryNode:
        children = [
            MarketIntelligenceService._map_category(c)
            for c in raw.get("children", [])
        ]
        return CategoryNode(
            id=raw["id"],
            name=raw["name"],
            parent_id=raw.get("parent_id"),
            children=children,
            book_count=raw.get("book_count"),
        )

    @staticmethod
    def _estimate_competition(products: list[CompetitorSummary]) -> float:
        """Quick competition estimate (0-100) based on review counts."""
        if not products:
            return 50.0
        reviews = [p.reviews_count for p in products]
        avg = statistics.mean(reviews)
        # More reviews among top results => higher competition
        if avg > 1000:
            return min(95, 60 + avg / 200)
        return min(95, 30 + avg / 50)

    @staticmethod
    def _generate_gap_analysis(
        products: list[CompetitorSummary], scores: "NicheMetrics | object"
    ) -> list[GapAnalysisItem]:
        gaps: list[GapAnalysisItem] = []
        if not products:
            gaps.append(
                GapAnalysisItem(
                    area="Market Entry",
                    description="No competing products found -- wide open opportunity.",
                    opportunity_level="high",
                )
            )
            return gaps

        prices = [p.price for p in products if p.price is not None]
        reviews = [p.reviews_count for p in products]
        ratings = [p.rating for p in products if p.rating is not None]

        # Price gap
        if prices:
            avg_price = statistics.mean(prices)
            if avg_price > 12:
                gaps.append(
                    GapAnalysisItem(
                        area="Price Positioning",
                        description=f"Average price is ${avg_price:.2f}. A lower-priced entry could capture budget-conscious readers.",
                        opportunity_level="medium",
                    )
                )
            else:
                gaps.append(
                    GapAnalysisItem(
                        area="Price Positioning",
                        description=f"Average price is ${avg_price:.2f}. Premium pricing with added value could differentiate.",
                        opportunity_level="medium",
                    )
                )

        # Review gap
        if reviews:
            low_review_count = sum(1 for r in reviews if r < 50)
            if low_review_count > len(reviews) * 0.4:
                gaps.append(
                    GapAnalysisItem(
                        area="Review Barrier",
                        description="Many competitors have fewer than 50 reviews, making entry more viable.",
                        opportunity_level="high",
                    )
                )
            else:
                gaps.append(
                    GapAnalysisItem(
                        area="Review Barrier",
                        description="Most competitors have established review bases. Strong launch strategy needed.",
                        opportunity_level="low",
                    )
                )

        # Quality gap
        if ratings:
            avg_rating = statistics.mean(ratings)
            if avg_rating < 4.2:
                gaps.append(
                    GapAnalysisItem(
                        area="Quality Gap",
                        description=f"Average rating is {avg_rating:.1f} stars. A higher-quality book can stand out.",
                        opportunity_level="high",
                    )
                )
            else:
                gaps.append(
                    GapAnalysisItem(
                        area="Quality Gap",
                        description=f"Average rating is {avg_rating:.1f} stars. Quality bar is high; match or exceed.",
                        opportunity_level="low",
                    )
                )

        return gaps
