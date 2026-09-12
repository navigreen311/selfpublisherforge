"""Voice dictation models — sessions, commands."""

import enum
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel, TenantModel


class DictationSessionStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class DictationSession(TenantModel):
    __tablename__ = "dictation_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    book_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("books.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    chapter_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active", server_default="active")
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    words_dictated: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    words_after_refinement: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    raw_transcript: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    refined_text: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    asr_provider: Mapped[str] = mapped_column(
        String(50), nullable=False, default="faster_whisper", server_default="faster_whisper"
    )
    asr_model: Mapped[str] = mapped_column(String(100), nullable=False, default="large-v3", server_default="large-v3")
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en", server_default="en")
    audio_recording_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    refinement_applied: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    refinement_style_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("style_profiles.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    session_metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None, server_default="{}")
    ended_at: Mapped[None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # Relationships
    user = relationship("User", backref="dictation_sessions")
    book = relationship("Book", backref="dictation_sessions")
    chapter = relationship("Chapter", backref="dictation_sessions")
    refinement_style_profile = relationship("StyleProfile", backref="dictation_sessions")

    __table_args__ = (
        Index("ix_dictation_sessions_status", "status"),
        Index("ix_dictation_sessions_asr_provider", "asr_provider"),
        Index("ix_dictation_sessions_session_metrics_gin", "session_metrics", postgresql_using="gin"),
        Index("ix_dictation_sessions_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_dictation_sessions_org_id_created_at", "org_id", "created_at"),
    )


class DictationCommand(BaseModel):
    """A voice command. System commands are global; custom ones are org-scoped.

    Deliberately not a TenantModel: that contract says every row belongs to an
    organization, and the built-in commands do not.
    """

    __tablename__ = "dictation_commands"

    # The built-in commands belong to no organization: `list_commands` selects
    # `is_system IS TRUE OR org_id = :org`, so a system row is meant to be
    # visible to every tenant. TenantModel makes org_id NOT NULL, which made
    # that impossible to insert — the seeder passed org_id=None and the column
    # refused it. Overridden as nullable for the system rows only; a custom
    # command still carries its org, and no org-scoped query can match NULL.
    org_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)

    command_phrase: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    __table_args__ = (
        Index("ix_dictation_commands_command_phrase", "command_phrase"),
        Index("ix_dictation_commands_action", "action"),
        Index("ix_dictation_commands_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_dictation_commands_org_id_created_at", "org_id", "created_at"),
    )
