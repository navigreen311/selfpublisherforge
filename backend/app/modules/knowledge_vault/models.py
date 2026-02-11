"""Knowledge Vault database models."""


from sqlalchemy import Column, Float, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from app.database import TenantModel


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
