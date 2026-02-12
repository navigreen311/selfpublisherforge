"""SQLAlchemy models for dictation sessions, voice commands, and settings."""

import enum
import uuid

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import BaseModel


class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"


class DictationSession(BaseModel):
    """A single voice dictation session owned by a user."""

    __tablename__ = "dictation_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
    )
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en", server_default="en")
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="dictation_session_status", create_constraint=True),
        nullable=False,
        default=SessionStatus.ACTIVE,
        server_default="active",
    )
    raw_transcript: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    refined_text: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    refinement_applied: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    word_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    words_after_refinement: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    __table_args__ = (
        Index("ix_dictation_sessions_user_created", "user_id", "created_at"),
        Index("ix_dictation_sessions_org", "org_id"),
        Index("ix_dictation_sessions_status", "status"),
        Index(
            "ix_dictation_sessions_active",
            "user_id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )


class DictationCommand(BaseModel):
    """Voice command (system-wide or org-custom)."""

    __tablename__ = "dictation_commands"

    trigger_phrase: Mapped[str] = mapped_column(String(200), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        default=None,
        index=True,
    )

    __table_args__ = (
        Index("ix_dictation_commands_org", "org_id"),
        Index("ix_dictation_commands_trigger", "trigger_phrase"),
        Index(
            "ix_dictation_commands_active",
            "id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )


class DictationSettings(BaseModel):
    """Per-user dictation preferences."""

    __tablename__ = "dictation_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    auto_punctuation: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    voice_language: Mapped[str] = mapped_column(String(10), default="en", server_default="en")
    noise_cancellation: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    auto_save_interval_seconds: Mapped[int] = mapped_column(Integer, default=30, server_default="30")
    preferred_style_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        default=None,
    )

    __table_args__ = (Index("ix_dictation_settings_user", "user_id"),)
