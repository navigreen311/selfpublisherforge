"""SQLAlchemy models for Puzzle Books."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import TenantModel


class PuzzleBook(TenantModel):
    __tablename__ = "puzzle_books"
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    audience: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    puzzle_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    difficulty_mode: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    themes: Mapped[list | None] = mapped_column(PG_ARRAY(String), nullable=True, default=None)
    seasonal_theme: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    word_difficulty: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    clue_style: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    status: Mapped[str | None] = mapped_column(String(20), default="draft")
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    puzzles: Mapped[list[Puzzle]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Puzzle(TenantModel):
    __tablename__ = "puzzles"
    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("puzzle_books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    puzzle_type: Mapped[str] = mapped_column(String(50), nullable=False)
    puzzle_number: Mapped[int] = mapped_column(Integer, nullable=False)
    theme: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None)
    difficulty: Mapped[str | None] = mapped_column(String(50), nullable=True, default=None)
    difficulty_score: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    grid_size: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None)
    grid_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    word_list: Mapped[list | None] = mapped_column(PG_ARRAY(String), nullable=True, default=None)
    clues: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    solution_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    qa_scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    qa_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=None)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    book: Mapped[PuzzleBook] = relationship(back_populates="puzzles")
