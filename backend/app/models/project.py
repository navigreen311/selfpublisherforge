"""Project, Book, Series, PenName, and BookVersion models."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseModel, TenantModel


class ProjectType(str, enum.Enum):
    BOOK = "book"
    SERIES = "series"
    COURSE = "course"


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPLETED = "completed"


class BookFormat(str, enum.Enum):
    EBOOK = "ebook"
    PRINT = "print"
    AUDIO = "audio"


class BookStatus(str, enum.Enum):
    DRAFT = "draft"
    WRITING = "writing"
    EDITING = "editing"
    FORMATTING = "formatting"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class SeriesStatus(str, enum.Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class Project(TenantModel):
    __tablename__ = "projects"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[ProjectType] = mapped_column(
        SAEnum(ProjectType, name="project_type", create_constraint=True),
        nullable=False,
    )
    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus, name="project_status", create_constraint=True),
        default=ProjectStatus.DRAFT,
        server_default="draft",
    )
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    pen_name_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("pen_names.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )

    # Relationships
    organization = relationship(
        "Organization", back_populates="projects",
        primaryjoin="Project.org_id == Organization.id",
        foreign_keys="[Project.org_id]",
    )
    pen_name = relationship("PenName", back_populates="projects")
    books = relationship("Book", back_populates="project", lazy="selectin")

    __table_args__ = (
        Index("ix_projects_type", "type"),
        Index("ix_projects_status", "status"),
        Index("ix_projects_settings_gin", "settings", postgresql_using="gin"),
        Index("ix_projects_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_projects_org_id_created_at", "org_id", "created_at"),
    )


class Book(BaseModel):
    __tablename__ = "books"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    isbn: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None, index=True)
    asin: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None, index=True)
    format: Mapped[BookFormat] = mapped_column(
        SAEnum(BookFormat, name="book_format", create_constraint=True),
        default=BookFormat.EBOOK,
        server_default="ebook",
    )
    status: Mapped[BookStatus] = mapped_column(
        SAEnum(BookStatus, name="book_status", create_constraint=True),
        default=BookStatus.DRAFT,
        server_default="draft",
    )
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True, default=None
    )

    # Relationships
    project = relationship("Project", back_populates="books")
    manuscripts = relationship("Manuscript", back_populates="book", lazy="selectin")
    book_versions = relationship("BookVersion", back_populates="book", lazy="selectin")
    listings = relationship("Listing", back_populates="book", lazy="selectin")
    upload_validations = relationship("UploadValidation", back_populates="book", lazy="selectin")
    compliance_scans = relationship("ComplianceScan", back_populates="book", lazy="selectin")
    pricing_rules = relationship(
        "PricingRule", back_populates="book", lazy="selectin",
        primaryjoin="Book.id == foreign(PricingRule.book_id)",
    )
    campaigns = relationship(
        "Campaign", back_populates="book", lazy="selectin",
        primaryjoin="Book.id == foreign(Campaign.book_id)",
    )
    launch_plans = relationship("LaunchPlan", back_populates="book", lazy="selectin")
    writing_sessions = relationship("WritingSession", back_populates="book", lazy="selectin")
    royalty_records = relationship(
        "RoyaltyRecord", back_populates="book", lazy="selectin",
        primaryjoin="Book.id == foreign(RoyaltyRecord.book_id)",
    )

    __table_args__ = (
        Index("ix_books_format", "format"),
        Index("ix_books_status", "status"),
        Index("ix_books_metadata_gin", "metadata", postgresql_using="gin"),
        Index("ix_books_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )


class Series(TenantModel):
    __tablename__ = "series"

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    genre_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, default=None)
    book_order: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True, default=None)
    reading_order: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True, default=None)
    status: Mapped[SeriesStatus] = mapped_column(
        SAEnum(SeriesStatus, name="series_status", create_constraint=True),
        default=SeriesStatus.PLANNED,
        server_default="planned",
    )

    # Relationships
    organization = relationship(
        "Organization", back_populates="series",
        primaryjoin="Series.org_id == Organization.id",
        foreign_keys="[Series.org_id]",
    )

    __table_args__ = (
        Index("ix_series_status", "status"),
        Index("ix_series_book_order_gin", "book_order", postgresql_using="gin"),
        Index("ix_series_reading_order_gin", "reading_order", postgresql_using="gin"),
        Index("ix_series_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_series_org_id_created_at", "org_id", "created_at"),
    )


class PenName(TenantModel):
    __tablename__ = "pen_names"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    brand_guidelines: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Relationships
    organization = relationship(
        "Organization", back_populates="pen_names",
        primaryjoin="PenName.org_id == Organization.id",
        foreign_keys="[PenName.org_id]",
    )
    projects = relationship("Project", back_populates="pen_name", lazy="selectin")

    __table_args__ = (
        Index("ix_pen_names_active", "active"),
        Index("ix_pen_names_brand_guidelines_gin", "brand_guidelines", postgresql_using="gin"),
        Index("ix_pen_names_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
        Index("ix_pen_names_org_id_created_at", "org_id", "created_at"),
    )


class BookVersion(BaseModel):
    __tablename__ = "book_versions"

    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    manuscript_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
    )

    # Relationships
    book = relationship("Book", back_populates="book_versions")
    created_by_user = relationship("User", back_populates="book_versions")

    __table_args__ = (
        Index("ix_book_versions_deleted_at_partial", "id", postgresql_where="deleted_at IS NULL"),
    )
