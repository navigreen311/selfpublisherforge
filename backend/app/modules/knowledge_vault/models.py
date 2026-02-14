"""Knowledge Vault database models."""


from sqlalchemy import BigInteger, Column, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID

from app.database import BaseModel, TenantModel


class KnowledgeEntry(TenantModel):
    """A research / knowledge entry stored in the vault."""

    __tablename__ = "knowledge_entries"

    title: str = Column(String(500), nullable=False, index=True)  # type: ignore[assignment]
    content: str = Column(Text, nullable=False, default="")  # type: ignore[assignment]
    source_url: str | None = Column(String(2048), nullable=True)  # type: ignore[assignment]
    source_type: str = Column(  # type: ignore[assignment]
        String(20), nullable=False, default="manual",
        comment="manual | url | file | clip",
    )
    tags: list[str] = Column(ARRAY(String(100)), nullable=False, server_default="{}")  # type: ignore[assignment]
    credibility_score: float | None = Column(Float, nullable=True)  # type: ignore[assignment]
    metadata_: dict = Column("metadata", JSONB, nullable=False, server_default="{}")  # type: ignore[assignment]

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
            "metadata": self.metadata_ or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class KnowledgeAttachment(BaseModel):
    """A file attachment linked to a knowledge entry."""

    __tablename__ = "knowledge_attachments"

    entry_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_name: str = Column(String(500), nullable=False)  # type: ignore[assignment]
    file_url: str = Column(String(2048), nullable=False)  # type: ignore[assignment]
    file_size: int = Column(BigInteger, nullable=False, default=0)  # type: ignore[assignment]
    mime_type: str = Column(String(127), nullable=False, default="application/octet-stream")  # type: ignore[assignment]
    s3_key: str = Column(String(1024), nullable=True)  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"<KnowledgeAttachment id={self.id} file_name={self.file_name!r}>"
