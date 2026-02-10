"""Knowledge Vault database models."""

from sqlalchemy import Column, Float, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from datetime import datetime
from typing import Optional

from app.database import TenantModel


class KnowledgeEntry(TenantModel):
    """A research / knowledge entry stored in the vault."""

    __tablename__ = "knowledge_entries"

    title: str = Column(String(500), nullable=False, index=True)
    content: str = Column(Text, nullable=False, default="")
    source_url: Optional[str] = Column(String(2048), nullable=True)
    source_type: str = Column(
        String(20), nullable=False, default="manual",
        comment="manual | url | file | clip",
    )
    tags: list[str] = Column(ARRAY(String(100)), nullable=False, server_default="{}")
    credibility_score: Optional[float] = Column(Float, nullable=True)
    metadata_: dict = Column("metadata", JSONB, nullable=False, server_default="{}")

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
