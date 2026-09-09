"""SQLAlchemy models for Puzzle Books."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel, TenantModel
from app.modules.specialty.models.enums import (
    AnswerKeyPosition,
    Audience,
    BookStatus,
    ClueStyle,
    Difficulty,
    DifficultyMode,
    PuzzleType,
    WordDifficulty,
)


class PuzzleBook(TenantModel):
    """Master record for a puzzle book."""

    __tablename__ = "puzzle_books"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    audience: Mapped[str] = mapped_column(
        Enum(Audience, name="audience", native_enum=True, create_type=False),
        nullable=False,
        default=Audience.adults,
    )
    puzzle_config: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    difficulty_mode: Mapped[str] = mapped_column(
        Enum(DifficultyMode, name="difficulty_mode", native_enum=True),
        nullable=False,
        default=DifficultyMode.progressive,
    )
    themes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    seasonal_theme: Mapped[str | None] = mapped_column(String(50), nullable=True)
    word_difficulty: Mapped[str | None] = mapped_column(
        Enum(WordDifficulty, name="word_difficulty", native_enum=True),
        nullable=True,
    )
    clue_style: Mapped[str | None] = mapped_column(
        Enum(ClueStyle, name="clue_style", native_enum=True),
        nullable=True,
    )
    answer_key_position: Mapped[str] = mapped_column(
        Enum(AnswerKeyPosition, name="answer_key_position", native_enum=True),
        nullable=False,
        default=AnswerKeyPosition.back_of_book,
    )
    has_toc: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    has_hints: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    layout_mode: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(BookStatus, name="book_status", native_enum=True, create_type=False),
        nullable=False,
        default=BookStatus.draft,
        server_default="draft",
    )
    qa_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    puzzles: Mapped[list[Puzzle]] = relationship(
        "Puzzle",
        back_populates="book",
        cascade="all, delete-orphan",
    )


class Puzzle(BaseModel):
    """Individual puzzle in a puzzle book."""

    __tablename__ = "puzzles"

    book_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("puzzle_books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    puzzle_type: Mapped[str] = mapped_column(
        Enum(PuzzleType, name="puzzle_type", native_enum=True),
        nullable=False,
    )
    puzzle_number: Mapped[int] = mapped_column(Integer, nullable=False)
    theme: Mapped[str | None] = mapped_column(String(100), nullable=True)
    difficulty: Mapped[str] = mapped_column(
        Enum(Difficulty, name="difficulty", native_enum=True),
        nullable=False,
        default=Difficulty.medium,
    )
    difficulty_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    grid_size: Mapped[str | None] = mapped_column(String(20), nullable=True)
    grid_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    word_list: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    clues: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    answer_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    has_unique_solution: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Relationships
    book: Mapped[PuzzleBook] = relationship("PuzzleBook", back_populates="puzzles")
