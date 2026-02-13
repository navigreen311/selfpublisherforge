"""Dictation models — re-exports from canonical location.

Canonical dictation models live in ``app.models.dictation``.
This module re-exports them for backwards compatibility with
``app.modules.dictation.service`` imports.
"""

from app.models.dictation import (  # noqa: F401
    DictationCommand,
    DictationSession,
    DictationSessionStatus as SessionStatus,
)

# DictationSettings only exists in the module layer (not in app.models.dictation),
# so we define it here.
import uuid

from sqlalchemy import Boolean, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey

from app.database import BaseModel


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
