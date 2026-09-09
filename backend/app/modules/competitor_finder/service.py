"""Service layer for the Competitor Weakness Finder module.

Orchestrates analysis, manages alerts, and coordinates between the
review analyzer, opportunity generator, and gap detector.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.competitor_finder.gap_detector import (
    BookData,
    run_gap_analysis,
)
from app.modules.competitor_finder.models import (
    CompetitorAlert,
    CompetitorAnalysis,
    CompetitorBook,
    CompetitorReview,
    GapAnalysisResult,
    OpportunityBlueprint,
    WeaknessSignal,
)
from app.modules.competitor_finder.opportunity_generator import (
    generate_opportunity_blueprint,
)
from app.modules.competitor_finder.review_analyzer import (
    AnalysisResult,
    ReviewData,
    analyze_reviews_with_ai,
)
from app.modules.competitor_finder.schemas import (
    AlertSeverity,
    AlertType,
    AnalysisStatus,
    BatchAnalyzeRequest,
    CompetitorAnalyzeRequest,
    GapAnalysisRequest,
)

logger = logging.getLogger(__name__)


class CompetitorFinderService:
    """Main service for competitor analysis operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Single book analysis
    # ------------------------------------------------------------------

    async def analyze_competitor(
        self,
        request: CompetitorAnalyzeRequest,
        org_id: UUID,
    ) -> CompetitorAnalysis:
        """Start a deep analysis of a single competitor book."""
        # Verify book exists
        book = await self._get_book(request.book_id)
        if not book:
            raise ValueError(f"Competitor book {request.book_id} not found")

        # Create analysis record
        analysis = CompetitorAnalysis(
            org_id=org_id,
            book_id=request.book_id,
            status=AnalysisStatus.PROCESSING.value,
        )
        self.db.add(analysis)
        await self.db.flush()

        try:
            # Fetch reviews
            reviews = await self._get_reviews(request.book_id, limit=request.max_reviews)
            review_data = [
                ReviewData(
                    review_id=r.id,
                    rating=int(r.rating or 3),
                    title=r.title or "",
                    body=r.review_text or "",
                    helpful_votes=r.helpful_votes,
                    verified_purchase=r.verified_purchase,
                )
                for r in reviews
            ]

            # Run review analysis
            result = await analyze_reviews_with_ai(
                reviews=review_data,
                book_title=book.title,
                book_category=book.category or "",
            )

            # Update analysis record
            analysis.sentiment_score = result.sentiment_score
            analysis.review_summary = result.review_summary
            analysis.weakness_count = result.weakness_count
            analysis.strength_count = result.strength_count
            analysis.overall_score = self._compute_overall_score(result)
            analysis.positioning_analysis = {
                "total_reviews": result.total_reviews_analyzed,
                "book_rating": book.rating,
                "book_bsr": book.bsr,
                "category": book.category,
            }

            # Save weakness signals
            for signal in result.weakness_signals:
                ws = WeaknessSignal(
                    analysis_id=analysis.id,
                    category=signal.category.value,
                    severity=signal.severity.value,
                    signal_text=signal.signal_text,
                    evidence=signal.evidence,
                    frequency=signal.frequency,
                    confidence=signal.confidence,
                    actionable=signal.actionable,
                    suggestion=signal.suggestion,
                )
                self.db.add(ws)

            # Generate opportunity blueprint if requested
            if request.include_opportunity and result.weakness_signals:
                blueprint_data = await generate_opportunity_blueprint(
                    weaknesses=result.weakness_signals,
                    book_title=book.title,
                    book_category=book.category or "",
                    book_price=book.price,
                    book_rating=book.rating,
                )
                blueprint = OpportunityBlueprint(
                    analysis_id=analysis.id,
                    title_suggestions=blueprint_data.title_suggestions,
                    content_strategy=blueprint_data.content_strategy,
                    format_recommendations=blueprint_data.format_recommendations,
                    pricing_strategy=blueprint_data.pricing_strategy,
                    differentiators=blueprint_data.differentiators,
                    target_audience=blueprint_data.target_audience,
                    estimated_opportunity_score=blueprint_data.estimated_opportunity_score,
                    full_blueprint=blueprint_data.full_blueprint,
                )
                self.db.add(blueprint)

            analysis.status = AnalysisStatus.COMPLETED.value
            analysis.completed_at = datetime.now(UTC)

        except (SQLAlchemyError, ValueError, RuntimeError, OSError) as e:
            logger.error("Analysis failed for book %s: %s", request.book_id, e, exc_info=True)
            analysis.status = AnalysisStatus.FAILED.value
            analysis.error_message = str(e)

        await self.db.flush()
        return analysis

    # ------------------------------------------------------------------
    # Weaknesses retrieval
    # ------------------------------------------------------------------

    async def get_weaknesses(
        self,
        analysis_id: UUID,
        org_id: UUID,
    ) -> list[WeaknessSignal]:
        """Get weakness signals for a completed analysis."""
        # Verify the analysis belongs to this org
        analysis = await self._get_analysis(analysis_id, org_id)
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        stmt = (
            select(WeaknessSignal)
            .where(WeaknessSignal.analysis_id == analysis_id)
            .order_by(WeaknessSignal.confidence.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Batch analysis
    # ------------------------------------------------------------------

    async def batch_analyze(
        self,
        request: BatchAnalyzeRequest,
        org_id: UUID,
    ) -> list[CompetitorAnalysis]:
        """Analyze the top N books in a category.

        Returns a list of analysis records (initially in pending/processing state).
        The actual analysis can be offloaded to Celery tasks.
        """
        # Find books in the category
        stmt = (
            select(CompetitorBook)
            .where(
                CompetitorBook.org_id == org_id,
                CompetitorBook.category == request.category,
            )
            .order_by(CompetitorBook.bsr_current.asc().nullslast())
            .limit(request.top_n)
        )
        result = await self.db.execute(stmt)
        books = list(result.scalars().all())

        if not books:
            raise ValueError(f"No competitor books found in category '{request.category}'")

        analyses: list[CompetitorAnalysis] = []
        for book in books:
            analysis = CompetitorAnalysis(
                org_id=org_id,
                book_id=book.id,
                status=AnalysisStatus.PENDING.value,
            )
            self.db.add(analysis)
            analyses.append(analysis)

        await self.db.flush()
        return analyses

    # ------------------------------------------------------------------
    # Opportunity blueprint retrieval
    # ------------------------------------------------------------------

    async def get_opportunity(
        self,
        analysis_id: UUID,
        org_id: UUID,
    ) -> OpportunityBlueprint | None:
        """Get the opportunity blueprint for a completed analysis."""
        analysis = await self._get_analysis(analysis_id, org_id)
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        stmt = select(OpportunityBlueprint).where(OpportunityBlueprint.analysis_id == analysis_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Gap analysis
    # ------------------------------------------------------------------

    async def run_gap_analysis(
        self,
        request: GapAnalysisRequest,
        org_id: UUID,
    ) -> GapAnalysisResult:
        """Run a cover/title/content gap analysis for a niche."""
        # Fetch books for the analysis
        if request.book_ids:
            stmt = select(CompetitorBook).where(
                CompetitorBook.id.in_(request.book_ids),
                CompetitorBook.org_id == org_id,
            )
        else:
            stmt = (
                select(CompetitorBook)
                .where(CompetitorBook.org_id == org_id)
                .order_by(CompetitorBook.bsr_current.asc().nullslast())
                .limit(request.max_books)
            )
            if request.category:
                stmt = stmt.where(CompetitorBook.category == request.category)

        result = await self.db.execute(stmt)
        books = list(result.scalars().all())

        if not books:
            raise ValueError("No competitor books found for gap analysis")

        # Convert to BookData
        book_data_list = [
            BookData(
                title=b.title,
                author=b.author,
                category=b.category,
                price=b.price,
                rating=b.rating,
                review_count=b.review_count,
                cover_url=b.cover_url,
                bsr=b.bsr,
            )
            for b in books
        ]

        # Run gap analysis
        gap_data = await run_gap_analysis(
            books=book_data_list,
            niche=request.niche,
            category=request.category,
        )

        # Save result
        gap_result = GapAnalysisResult(
            org_id=org_id,
            niche=request.niche,
            category=request.category,
            books_analyzed=gap_data.books_analyzed,
            cover_gaps=[g.model_dump() for g in gap_data.cover_gaps],
            title_gaps=[g.model_dump() for g in gap_data.title_gaps],
            content_gaps=[g.model_dump() for g in gap_data.content_gaps],
            summary=gap_data.summary,
            recommendations=gap_data.recommendations,
            status="completed",
        )
        self.db.add(gap_result)
        await self.db.flush()

        return gap_result

    # ------------------------------------------------------------------
    # Alerts
    # ------------------------------------------------------------------

    async def get_alerts(
        self,
        org_id: UUID,
        include_dismissed: bool = False,
        limit: int = 50,
    ) -> list[CompetitorAlert]:
        """Get competitor alerts for an organization."""
        stmt = (
            select(CompetitorAlert)
            .where(CompetitorAlert.org_id == org_id)
            .order_by(CompetitorAlert.created_at.desc())
            .limit(limit)
        )
        if not include_dismissed:
            stmt = stmt.where(CompetitorAlert.dismissed == False)  # noqa: E712

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_alert(
        self,
        org_id: UUID,
        alert_type: AlertType,
        title: str,
        description: str | None = None,
        severity: AlertSeverity = AlertSeverity.INFO,
        book_id: UUID | None = None,
        data: dict | None = None,
    ) -> CompetitorAlert:
        """Create a new competitor alert."""
        alert = CompetitorAlert(
            org_id=org_id,
            book_id=book_id,
            alert_type=alert_type.value,
            severity=severity.value,
            title=title,
            description=description,
            data=data,
        )
        self.db.add(alert)
        await self.db.flush()
        return alert

    async def dismiss_alert(self, alert_id: UUID, org_id: UUID) -> bool:
        """Dismiss (soft-hide) an alert."""
        stmt = (
            update(CompetitorAlert)
            .where(
                CompetitorAlert.id == alert_id,
                CompetitorAlert.org_id == org_id,
            )
            .values(dismissed=True)
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0  # type: ignore[return-value]

    async def mark_alert_read(self, alert_id: UUID, org_id: UUID) -> bool:
        """Mark an alert as read."""
        stmt = (
            update(CompetitorAlert)
            .where(
                CompetitorAlert.id == alert_id,
                CompetitorAlert.org_id == org_id,
            )
            .values(read=True)
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_book(self, book_id: UUID) -> CompetitorBook | None:
        """Fetch a competitor book by ID."""
        stmt = select(CompetitorBook).where(CompetitorBook.id == book_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_reviews(self, book_id: UUID, limit: int = 100) -> list[CompetitorReview]:
        """Fetch reviews for a book."""
        stmt = (
            select(CompetitorReview)
            .where(CompetitorReview.competitor_book_id == book_id)
            .order_by(CompetitorReview.helpful_votes.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_analysis(self, analysis_id: UUID, org_id: UUID) -> CompetitorAnalysis | None:
        """Fetch an analysis by ID, scoped to org."""
        stmt = select(CompetitorAnalysis).where(
            CompetitorAnalysis.id == analysis_id,
            CompetitorAnalysis.org_id == org_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _compute_overall_score(result: AnalysisResult) -> float:
        """Compute an overall competitor quality score (0-100).

        Higher score = stronger competitor = harder to beat.
        """
        # Sentiment contribution (0-50)
        sentiment_component = result.sentiment_score * 50

        # Weakness penalty (0-30)
        weakness_penalty = min(result.weakness_count * 3, 30)

        # Strength bonus (0-20)
        strength_bonus = min(result.strength_count * 0.5, 20)

        score = sentiment_component - weakness_penalty + strength_bonus
        return round(max(0, min(100, score)), 2)
