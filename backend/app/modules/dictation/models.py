"""Dictation models — re-exports from canonical location.

Canonical dictation models live in ``app.models.dictation``.
This module re-exports them for backwards compatibility with
``app.modules.dictation.service`` imports.
"""

# DictationSettings only exists in the module layer (not in app.models.dictation),
# so we define it here.
import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import BaseModel
from app.models.dictation import (
    DictationCommand,
    DictationSession,
)
from app.models.dictation import (
    DictationSessionStatus as SessionStatus,
)

# Re-exported for backwards compatibility. Declared in __all__ rather than
# carrying a `# `, because ruff's import sorter relocates the block
# and the trailing noqa does not travel with it — which silently dropped the
# SessionStatus alias.
__all__ = [
    "DictationCommand",
    "DictationSession",
    "DictationSettings",
    "SessionStatus",
]


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
