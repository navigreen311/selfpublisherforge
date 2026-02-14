"""SQLAlchemy models for the Cover Design Studio."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import (
    JSON,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import TenantModel


class Cover(TenantModel):
    """A generated (or uploaded) book cover."""

    __tablename__ = "covers"

    book_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(300), nullable=True)
    author_name: Mapped[str] = mapped_column(String(200), nullable=False)
    genre: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_used: Mapped[str | None] = mapped_column(Text, nullable=True)
    width_px: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_px: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dpi: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    bleed_px: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    platform: Mapped[str] = mapped_column(
        String(30), nullable=False, default="amazon-kdp"
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, default=dict
    )
    parent_cover_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("covers.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    variations: Mapped[list[Cover]] = relationship(
        "Cover",
        back_populates="parent_cover",
        foreign_keys=[parent_cover_id],
    )
    parent_cover: Mapped[Cover | None] = relationship(
        "Cover",
        back_populates="variations",
        remote_side="Cover.id",
        foreign_keys=[parent_cover_id],
    )


class ExtractedProduct(TenantModel):
    """Amazon product data saved by the Chrome Extension."""

    __tablename__ = "extracted_products"

    asin: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(500), nullable=True)
    author: Mapped[str | None] = mapped_column(String(300), nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    bsr: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    bsr_categories: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    categories: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    keywords: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    reviews_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    page_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    marketplace: Mapped[str] = mapped_column(
        String(30), nullable=False, default="amazon.com"
    )
    publication_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dimensions: Mapped[str | None] = mapped_column(String(100), nullable=True)
    isbn: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)


class KnowledgeClip(TenantModel):
    """A clip saved from the browser to the Knowledge Vault."""

    __tablename__ = "knowledge_clips"

    clip_type: Mapped[str] = mapped_column(String(20), nullable=False, default="text")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class CoverABTest(TenantModel):
    """A/B test comparing two cover designs."""

    __tablename__ = "cover_ab_tests"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_a_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("covers.id", ondelete="CASCADE"), nullable=False
    )
    cover_b_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("covers.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", server_default="draft", index=True
    )
    votes_a: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    votes_b: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    public_url: Mapped[str | None] = mapped_column(String(500), nullable=True, unique=True)
    target_audience: Mapped[str | None] = mapped_column(String(500), nullable=True)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    started_at: Mapped[Any | None] = mapped_column(nullable=True)
    ended_at: Mapped[Any | None] = mapped_column(nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True, default=dict)

    # Relationships
    cover_a: Mapped[Cover] = relationship("Cover", foreign_keys=[cover_a_id])
    cover_b: Mapped[Cover] = relationship("Cover", foreign_keys=[cover_b_id])
