"""MarketCategory, MarketKeyword, CompetitorBook, CompetitorReview, and MarketSnapshot models."""
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel


class MarketCategory(BaseModel):
    __tablename__ = "market_categories"

    amazon_node_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True, default=None, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    path: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True, default=None)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("market_categories.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )
    book_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    avg_bsr: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    competition_score: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)

    # Self-referential relationship
    parent = relationship("MarketCategory", remote_side="MarketCategory.id", backref="children")
    snapshots = relationship("MarketSnapshot", back_populates="category", lazy="selectin")

    __table_args__ = (
        Index("ix_market_categories_path_gin", "path", postgresql_using="gin"),
        Index("ix_market_categories_competition_score", "competition_score"),
        Index("ix_market_categories_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class MarketKeyword(BaseModel):
    __tablename__ = "market_keywords"

    keyword: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    search_volume: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    competition_score: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    cpc_estimate: Mapped[float | None] = mapped_column(
        Numeric(10, 4), nullable=True, default=None
    )
    trend_direction: Mapped[str | None] = mapped_column(
        String(20), nullable=True, default=None
    )
    last_updated: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    __table_args__ = (
        Index("ix_market_keywords_search_volume", "search_volume"),
        Index("ix_market_keywords_competition_score", "competition_score"),
        Index("ix_market_keywords_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class CompetitorBook(BaseModel):
    __tablename__ = "competitor_books"

    org_id: Mapped[uuid.UUID | None] = mapped_column(index=True, nullable=True, default=None)
    asin: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    bsr_current: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    bsr_history: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True, default=None)
    reviews_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    rating: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    category: Mapped[str | None] = mapped_column(String(300), nullable=True, default=None)
    category_ids: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True, default=None)
    cover_url: Mapped[str | None] = mapped_column(String(1000), nullable=True, default=None)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Relationships
    reviews = relationship("CompetitorReview", back_populates="competitor_book", lazy="selectin",
                           foreign_keys="CompetitorReview.competitor_book_id")
    analyses = relationship("CompetitorAnalysis", back_populates="book", lazy="selectin")

    __table_args__ = (
        Index("ix_competitor_books_bsr_current", "bsr_current"),
        Index("ix_competitor_books_bsr_history_gin", "bsr_history", postgresql_using="gin"),
        Index("ix_competitor_books_category_ids_gin", "category_ids", postgresql_using="gin"),
        Index("ix_competitor_books_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )

    @property
    def bsr(self) -> int | None:
        """Alias for bsr_current used by competitor_finder module."""
        return self.bsr_current

    @bsr.setter
    def bsr(self, value: int | None) -> None:
        self.bsr_current = value

    @property
    def review_count(self) -> int:
        """Alias for reviews_count used by competitor_finder module."""
        return self.reviews_count

    @review_count.setter
    def review_count(self, value: int) -> None:
        self.reviews_count = value


class CompetitorReview(BaseModel):
    __tablename__ = "competitor_reviews"

    competitor_book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("competitor_books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_name: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    review_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    verified_purchase: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    helpful_votes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    weakness_signals: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Relationships
    competitor_book = relationship("CompetitorBook", back_populates="reviews")

    __table_args__ = (
        Index("ix_competitor_reviews_rating", "rating"),
        Index("ix_competitor_reviews_sentiment_score", "sentiment_score"),
        Index("ix_competitor_reviews_weakness_signals_gin", "weakness_signals", postgresql_using="gin"),
        Index(
            "ix_competitor_reviews_review_text_fulltext",
            "review_text",
            postgresql_using="gin",
            postgresql_ops={"review_text": "gin_trgm_ops"},
        ),
        Index("ix_competitor_reviews_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )

    @property
    def book_id(self) -> uuid.UUID:
        """Alias for competitor_book_id used by competitor_finder module."""
        return self.competitor_book_id

    @book_id.setter
    def book_id(self, value: uuid.UUID) -> None:
        self.competitor_book_id = value

    @property
    def body(self) -> str | None:
        """Alias for review_text used by competitor_finder module."""
        return self.review_text

    @body.setter
    def body(self, value: str | None) -> None:
        self.review_text = value


class MarketSnapshot(BaseModel):
    __tablename__ = "market_snapshots"

    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("market_categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    top_100_asins: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True, default=None)
    metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    # Relationships
    category = relationship("MarketCategory", back_populates="snapshots")

    __table_args__ = (
        Index("ix_market_snapshots_snapshot_date", "snapshot_date"),
        Index("ix_market_snapshots_top_100_asins_gin", "top_100_asins", postgresql_using="gin"),
        Index("ix_market_snapshots_metrics_gin", "metrics", postgresql_using="gin"),
        Index("ix_market_snapshots_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )
