"""Service layer for the Market Intelligence Engine.

Orchestrates the Amazon client, scoring algorithm, and database
interactions to implement niche analysis, keyword research, and
competitor tracking.

NOTE: org_id scoping is enforced on all DB-backed queries to prevent
cross-tenant data leakage.  Client-only methods (categories, keywords,
niche analysis) accept the org_id parameter for forward compatibility
so that filtering can be applied when DB-backed caching is added.
"""

from __future__ import annotations

import statistics
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.market import (
    CompetitorBook,
    MarketCategory,
)
from app.models.market import (
    MarketSnapshot as MarketSnapshotDB,
)
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

    def __init__(self, client: AmazonClientBase | None = None) -> None:
        self._client = client or get_amazon_client()

    # ------------------------------------------------------------------
    # Categories
    # ------------------------------------------------------------------

    async def get_categories(
        self,
        root_id: str | None = None,
        marketplace: str = "US",
        org_id: uuid.UUID | None = None,
    ) -> list[CategoryNode]:
        raw = await self._client.get_category_tree(root_id=root_id, marketplace=marketplace)
        return [self._map_category(c) for c in raw]

    async def get_category_analysis(
        self,
        category_id: str,
        marketplace: str = "US",
        org_id: uuid.UUID | None = None,
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
        self,
        request: KeywordResearchRequest,
        org_id: uuid.UUID | None = None,
    ) -> KeywordResearchResponse:
        keyword_data = await self._client.get_keyword_data(request.keywords, marketplace=request.marketplace)
        return KeywordResearchResponse(
            keywords=keyword_data,
            marketplace=request.marketplace,
            generated_at=datetime.now(tz=UTC),
        )

    async def suggest_keywords(
        self,
        params: KeywordSuggestionsParams,
        org_id: uuid.UUID | None = None,
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
        self,
        request: NicheAnalysisRequest,
        org_id: uuid.UUID | None = None,
    ) -> NicheAnalysisResponse:
        # 1. Fetch products matching the niche
        products = await self._client.search_products(
            keywords=request.niche,
            category_id=request.category_id,
            marketplace=request.marketplace,
            max_results=20,
        )

        # 2. Fetch keyword data
        kw_data = await self._client.get_keyword_data([request.niche], marketplace=request.marketplace)

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
            analyzed_at=datetime.now(tz=UTC),
        )

    # ------------------------------------------------------------------
    # Competitors (DB-backed)
    # ------------------------------------------------------------------

    async def list_competitors(
        self, db: AsyncSession, org_id: uuid.UUID | None = None, marketplace: str = "US"
    ) -> list[CompetitorListItem]:
        """List tracked competitor books from the database."""
        query = select(CompetitorBook).where(CompetitorBook.deleted_at.is_(None))
        if org_id is not None:
            query = query.where(CompetitorBook.org_id == org_id)
        result = await db.execute(query)
        rows = result.scalars().all()
        return [self._map_db_competitor_list_item(row, marketplace) for row in rows]

    async def track_competitor(
        self, db: AsyncSession, request: CompetitorTrackRequest, org_id: uuid.UUID | None = None
    ) -> CompetitorDetail:
        """Start tracking a competitor by ASIN. Uses DB persistence."""
        # Check if already tracked in DB
        existing_query = select(CompetitorBook).where(
            CompetitorBook.asin == request.asin,
            CompetitorBook.deleted_at.is_(None),
        )
        if org_id is not None:
            existing_query = existing_query.where(CompetitorBook.org_id == org_id)
        result = await db.execute(existing_query)
        existing = result.scalar_one_or_none()
        if existing is not None:
            return self._map_db_competitor_detail(existing, request.marketplace)

        # Fetch from Amazon client
        product = await self._client.get_product_detail(request.asin, marketplace=request.marketplace)
        if not product:
            raise AppException(
                status_code=404,
                code="PRODUCT_NOT_FOUND",
                message=f"Product {request.asin} not found on Amazon",
            )

        bsr_history = await self._client.get_bsr_history(request.asin, days=30, marketplace=request.marketplace)

        # Serialize BSR history for JSONB storage
        bsr_history_json = [{"date": pt.date.isoformat(), "bsr": pt.bsr, "price": pt.price} for pt in bsr_history]

        # Create CompetitorBook in DB
        book = CompetitorBook(
            org_id=org_id,
            asin=product.asin,
            title=product.title,
            author=product.author or "",
            bsr_current=product.bsr,
            bsr_history=bsr_history_json,
            price=product.price,
            reviews_count=product.reviews_count,
            rating=product.rating,
            cover_url=product.image_url,
            metadata_json={"marketplace": request.marketplace},
        )
        db.add(book)
        await db.flush()
        await db.refresh(book)

        return self._map_db_competitor_detail(book, request.marketplace)

    async def get_competitor(
        self,
        db: AsyncSession,
        competitor_id: uuid.UUID,
        org_id: uuid.UUID | None = None,
    ) -> CompetitorDetail:
        """Get a single competitor by ID from the database.

        When org_id is provided the query is scoped to that tenant,
        preventing cross-tenant data access.
        """
        query = select(CompetitorBook).where(
            CompetitorBook.id == competitor_id,
            CompetitorBook.deleted_at.is_(None),
        )
        if org_id is not None:
            query = query.where(CompetitorBook.org_id == org_id)
        result = await db.execute(query)
        row = result.scalar_one_or_none()
        if row is None:
            raise AppException(
                status_code=404,
                code="COMPETITOR_NOT_FOUND",
                message=f"Competitor {competitor_id} not found",
            )
        return self._map_db_competitor_detail(row)

    # ------------------------------------------------------------------
    # Trends & Snapshots
    # ------------------------------------------------------------------

    async def get_trends(
        self,
        category_id: str | None = None,
        keyword: str | None = None,
        days: int = 30,
        org_id: uuid.UUID | None = None,
    ) -> MarketTrendsResponse:
        now = datetime.now(tz=UTC)
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
                    change_pct = round(((kd.trend_data[-1] - kd.trend_data[0]) / kd.trend_data[0]) * 100, 2)
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
            analysis = await self.get_category_analysis(category_id, org_id=org_id)
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
        return MarketTrendsResponse(trends=trends, period_start=period_start, period_end=now)

    async def get_snapshots(
        self,
        db: AsyncSession,
        category_id: str | None = None,
        limit: int = 30,
        org_id: uuid.UUID | None = None,
    ) -> list[MarketSnapshot]:
        """Return recent market snapshots from the database.

        When org_id is provided the query is scoped to that tenant.
        If no snapshots exist yet, returns an empty list.
        """
        query = (
            select(MarketSnapshotDB)
            .where(MarketSnapshotDB.deleted_at.is_(None))
            .order_by(MarketSnapshotDB.snapshot_date.desc())
            .limit(limit)
        )
        if org_id is not None:
            query = query.where(MarketSnapshotDB.org_id == org_id)
        if category_id:
            # Find MarketCategory by amazon_node_id, then filter snapshots
            cat_query = select(MarketCategory).where(
                MarketCategory.amazon_node_id == category_id,
                MarketCategory.deleted_at.is_(None),
            )
            if org_id is not None:
                cat_query = cat_query.where(MarketCategory.org_id == org_id)
            cat_result = await db.execute(cat_query)
            cat_obj = cat_result.scalar_one_or_none()
            if cat_obj:
                query = query.where(MarketSnapshotDB.category_id == cat_obj.id)
            else:
                # Category not found in DB -- return empty list
                return []
        result = await db.execute(query)
        rows = result.scalars().all()
        return [self._map_db_snapshot(r) for r in rows]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _map_category(raw: dict) -> CategoryNode:
        children = [MarketIntelligenceService._map_category(c) for c in raw.get("children", [])]
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
        products: list[CompetitorSummary],
        scores: NicheMetrics | object,  # noqa: ARG004  # part of the scorer signature; this strategy ignores it
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

    @staticmethod
    def _map_db_competitor_list_item(book: CompetitorBook, marketplace: str = "US") -> CompetitorListItem:
        """Map a CompetitorBook ORM row to a CompetitorListItem schema."""
        # Extract marketplace from metadata_json if available
        meta = book.metadata_json or {}
        mp = meta.get("marketplace", marketplace)
        return CompetitorListItem(
            id=book.id,
            asin=book.asin,
            title=book.title,
            author=book.author or "",
            bsr=book.bsr_current,
            price=float(book.price) if book.price is not None else None,
            reviews_count=book.reviews_count,
            rating=book.rating,
            marketplace=mp,
            tracked_since=book.created_at,
        )

    @staticmethod
    def _map_db_competitor_detail(book: CompetitorBook, marketplace: str = "US") -> CompetitorDetail:
        """Map a CompetitorBook ORM row to a CompetitorDetail schema."""
        meta = book.metadata_json or {}
        mp = meta.get("marketplace", marketplace)

        # Deserialize BSR history from JSONB
        bsr_history: list[BSRHistoryPoint] = []
        raw_history = book.bsr_history
        if isinstance(raw_history, list):
            for pt in raw_history:
                bsr_history.append(
                    BSRHistoryPoint(
                        date=pt["date"],
                        bsr=pt["bsr"],
                        price=pt.get("price"),
                    )
                )

        return CompetitorDetail(
            id=book.id,
            asin=book.asin,
            title=book.title,
            author=book.author or "",
            bsr=book.bsr_current,
            price=float(book.price) if book.price is not None else None,
            reviews_count=book.reviews_count,
            rating=book.rating,
            image_url=book.cover_url,
            category=book.category,
            marketplace=mp,
            bsr_history=bsr_history,
            tracked_since=book.created_at,
            last_updated=book.updated_at,
        )

    @staticmethod
    def _map_db_snapshot(snap: MarketSnapshotDB) -> MarketSnapshot:
        """Map a MarketSnapshot ORM row to a MarketSnapshot schema."""
        metrics = snap.metrics or {}
        # Access the related category for name and amazon_node_id
        cat = snap.category
        category_id_str = cat.amazon_node_id if cat and cat.amazon_node_id else str(snap.category_id)
        category_name = cat.name if cat else "Unknown"

        return MarketSnapshot(
            id=snap.id,
            category_id=category_id_str,
            category_name=category_name,
            snapshot_date=datetime.combine(snap.snapshot_date, datetime.min.time(), tzinfo=UTC)
            if not isinstance(snap.snapshot_date, datetime)
            else snap.snapshot_date,
            avg_bsr=metrics.get("avg_bsr", 0.0),
            avg_price=metrics.get("avg_price", 0.0),
            book_count=metrics.get("book_count", 0),
            avg_reviews=metrics.get("avg_reviews", 0.0),
            competition_score=metrics.get("competition_score", 0.0),
        )
