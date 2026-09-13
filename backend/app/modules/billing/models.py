"""SQLAlchemy models for billing events and audit trail."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
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


class Invoice(Base):
    """A billing invoice row.

    Created by migration 018 and never declared in the model layer; the admin
    billing view is still a stub (T-010b) and reads nothing from it.
    """

    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True, default="USD")
    description: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True, default="paid")
    period_start: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True, default=None)
    pdf_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )


class Webhook(Base):
    """An outbound webhook subscription.

    Created by migration 018. `settings/router.py` exposes /webhooks endpoints
    that do not read this table.
    """

    __tablename__ = "webhooks"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    events: Mapped[list] = mapped_column(ARRAY(Text()), nullable=False)
    secret: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True, default="active")
    last_delivery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    last_response_code: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )
