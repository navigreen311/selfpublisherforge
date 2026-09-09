"""ProofOrder SQLAlchemy model."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Index, Integer, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# Valid status lifecycle values
PROOF_ORDER_STATUSES = (
    "ordered",
    "processing",
    "printed",
    "shipped",
    "delivered",
    "reviewed",
    "approved",
    "rejected",
    "cancelled",
)


class ProofOrder(Base):
    """A physical proof copy order placed during the publishing pipeline."""

    __tablename__ = "proof_orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    publishing_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    book_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    platform: Mapped[str | None] = mapped_column(String(50), nullable=True)

    interior_file_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_file_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    shipping_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shipping_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    shipping_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    billing: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)

    cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estimated_delivery: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="ordered", server_default="ordered"
    )
    checklist: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    issues: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    ordered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_proof_orders_org", "org_id", "ordered_at"),
        Index("idx_proof_orders_status", "status"),
        Index("idx_proof_orders_publishing", "publishing_id"),
    )
