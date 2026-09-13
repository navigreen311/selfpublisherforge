"""SQLAlchemy models for notifications and notification preferences."""

import enum
import uuid
from datetime import datetime, time

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NotificationType(str, enum.Enum):
    """Types of notifications."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    AI_COMPLETE = "ai_complete"
    PUBLISH_STATUS = "publish_status"
    TEAM_INVITE = "team_invite"


class NotificationChannel(str, enum.Enum):
    """Channels for notification delivery."""

    EMAIL = "email"
    IN_APP = "in_app"
    PUSH = "push"


class Notification(Base):
    """In-app notification record."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type_enum", create_constraint=True),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_notifications_user_created", "user_id", created_at.desc()),
        Index("ix_notifications_org", "org_id"),
        Index(
            "ix_notifications_unread",
            "user_id",
            "created_at",
            postgresql_where=text("read_at IS NULL"),
        ),
    )


class NotificationPreference(Base):
    """User preference for a specific notification channel + category."""

    __tablename__ = "notification_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(
            NotificationChannel,
            name="notification_channel_enum",
            create_constraint=True,
        ),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Columns the database has carried since the migrations that created
    # them; they were never declared here, so every read of one was invisible
    # to the type checker and to `alembic check`.
    preferences: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'"))
    quiet_hours_start: Mapped[time | None] = mapped_column(Time, nullable=True, default=None)
    quiet_hours_end: Mapped[time | None] = mapped_column(Time, nullable=True, default=None)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    __table_args__ = (
        UniqueConstraint("user_id", name="notification_preferences_user_id_key"),
        UniqueConstraint("user_id", "channel", "category", name="uq_user_channel_category"),
    )
