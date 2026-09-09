"""PublishingAccount, Listing, UploadValidation, ComplianceScan, and PricingRule models."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel, TenantModel

# Import canonical PricingRule from the pricing_automation module
from app.modules.pricing_automation.models import PricingRule


class PublishingPlatform(str, enum.Enum):
    KDP = "kdp"
    INGRAMSPARK = "ingramspark"
    D2D = "d2d"
    ACX = "acx"


class PublishingAccountStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


class ListingStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    LIVE = "live"
    SUPPRESSED = "suppressed"
    REMOVED = "removed"


class ValidationType(str, enum.Enum):
    FORMAT = "format"
    CONTENT = "content"
    METADATA = "metadata"
    COVER = "cover"


class ScanType(str, enum.Enum):
    COPYRIGHT = "copyright"
    TRADEMARK = "trademark"
    CONTENT_POLICY = "content_policy"
    AI_DISCLOSURE = "ai_disclosure"


class RiskLevel(str, enum.Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class PublishingAccount(TenantModel):
    __tablename__ = "publishing_accounts"

    platform: Mapped[PublishingPlatform] = mapped_column(
        SAEnum(PublishingPlatform, name="publishing_platform", create_constraint=True),
        nullable=False,
    )
    credentials_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    status: Mapped[PublishingAccountStatus] = mapped_column(
        SAEnum(PublishingAccountStatus, name="publishing_account_status", create_constraint=True),
        default=PublishingAccountStatus.PENDING,
        server_default="pending",
    )
    health_score: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)

    # Relationships
    organization = relationship(
        "Organization",
        back_populates="publishing_accounts",
        primaryjoin="PublishingAccount.org_id == Organization.id",
        foreign_keys="[PublishingAccount.org_id]",
    )
    listings = relationship("Listing", back_populates="publishing_account", lazy="selectin")

    __table_args__ = (
        Index("ix_publishing_accounts_platform", "platform"),
        Index("ix_publishing_accounts_status", "status"),
        Index("ix_publishing_accounts_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_publishing_accounts_org_id_created_at", "org_id", "created_at"),
    )


class Listing(BaseModel):
    __tablename__ = "listings"

    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    publishing_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("publishing_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform_id: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    status: Mapped[ListingStatus] = mapped_column(
        SAEnum(ListingStatus, name="listing_status", create_constraint=True),
        default=ListingStatus.DRAFT,
        server_default="draft",
    )
    listing_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    last_synced: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # Relationships
    book = relationship("Book", back_populates="listings")
    publishing_account = relationship("PublishingAccount", back_populates="listings")

    __table_args__ = (
        Index("ix_listings_status", "status"),
        Index("ix_listings_listing_data_gin", "listing_data", postgresql_using="gin"),
        Index("ix_listings_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class UploadValidation(BaseModel):
    __tablename__ = "upload_validations"

    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    validation_type: Mapped[ValidationType] = mapped_column(
        SAEnum(ValidationType, name="validation_type", create_constraint=True),
        nullable=False,
    )
    results: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    passed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    errors: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True, default=None)
    warnings: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True, default=None)

    # Relationships
    book = relationship("Book", back_populates="upload_validations")

    __table_args__ = (
        Index("ix_upload_validations_validation_type", "validation_type"),
        Index("ix_upload_validations_passed", "passed"),
        Index("ix_upload_validations_results_gin", "results", postgresql_using="gin"),
        Index("ix_upload_validations_errors_gin", "errors", postgresql_using="gin"),
        Index("ix_upload_validations_warnings_gin", "warnings", postgresql_using="gin"),
        Index("ix_upload_validations_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class ComplianceScan(BaseModel):
    __tablename__ = "compliance_scans"

    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scan_type: Mapped[ScanType] = mapped_column(
        SAEnum(ScanType, name="scan_type", create_constraint=True),
        nullable=False,
    )
    findings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    risk_level: Mapped[RiskLevel] = mapped_column(
        SAEnum(RiskLevel, name="risk_level", create_constraint=True),
        default=RiskLevel.GREEN,
        server_default="green",
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )

    # Relationships
    book = relationship("Book", back_populates="compliance_scans")
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    __table_args__ = (
        Index("ix_compliance_scans_scan_type", "scan_type"),
        Index("ix_compliance_scans_risk_level", "risk_level"),
        Index("ix_compliance_scans_findings_gin", "findings", postgresql_using="gin"),
        Index("ix_compliance_scans_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )
