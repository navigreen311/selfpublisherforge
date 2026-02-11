"""SQLAlchemy models for billing events and audit trail."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BillingEvent(Base):
    """Billing event record for audit trail and idempotency.

    Tracks all billing-related events from Stripe webhooks including
    subscription changes, payment failures, and cancellations.
    Used for idempotency (preventing duplicate processing) and
    triggering win-back campaigns.
    """

    __tablename__ = "billing_events"

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
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Type of event: subscription_upgraded, payment_failed, etc.",
    )
    stripe_event_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
        comment="Stripe event ID for idempotency",
    )
    event_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Event payload data",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_billing_events_org_created", "org_id", created_at.desc()),
        Index("ix_billing_events_type", "event_type"),
        Index(
            "ix_billing_events_org_type",
            "org_id",
            "event_type",
            created_at.desc(),
        ),
        UniqueConstraint("stripe_event_id", name="uq_billing_events_stripe_id"),
    )
