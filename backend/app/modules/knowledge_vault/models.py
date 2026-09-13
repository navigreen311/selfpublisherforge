"""Knowledge Vault database models."""

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import TenantModel


class KnowledgeEntry(TenantModel):
    """A research / knowledge entry stored in the vault."""

    __tablename__ = "knowledge_entries"

    # Declared with SQLAlchemy 2.0 Mapped[] like every other model here. The
    # legacy `x: str = Column(...)` form these used needed a type: ignore on
    # every field, and made `Model.field == value` read as a bool rather than
    # a SQL expression, so filters using them were type errors.
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    source_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="manual",
        comment="manual | url | file | clip",
    )
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(100)), nullable=False, server_default="{}")
    credibility_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    category: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    project_id: Mapped[str | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True, index=True
    )
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")

    def __repr__(self) -> str:
        return f"<KnowledgeEntry id={self.id} title={self.title!r}>"

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "org_id": str(self.org_id),
            "title": self.title,
            "content": self.content,
            "source_url": self.source_url,
            "source_type": self.source_type,
            "tags": self.tags or [],
            "credibility_score": self.credibility_score,
            "category": self.category,
            "project_id": str(self.project_id) if self.project_id else None,
            "metadata": self.metadata_ or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class KnowledgeAttachment(TenantModel):
    """A file attachment linked to a knowledge entry."""

    __tablename__ = "knowledge_attachments"

    entry_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("knowledge_entries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    s3_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    def __repr__(self) -> str:
        return f"<KnowledgeAttachment id={self.id} file_name={self.file_name!r}>"
