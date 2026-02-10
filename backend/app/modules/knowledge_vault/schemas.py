"""Pydantic schemas for the Knowledge Vault module."""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


# ── Source type literals ──────────────────────────────────────────
SOURCE_TYPES = {"manual", "url", "file", "clip"}


# ── Create / Update ──────────────────────────────────────────────
class CreateEntryRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(default="")
    source_url: Optional[str] = Field(default=None, max_length=2048)
    source_type: str = Field(default="manual", pattern=r"^(manual|url|file|clip)$")
    tags: list[str] = Field(default_factory=list)
    credibility_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    metadata: dict = Field(default_factory=dict)


class UpdateEntryRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    content: Optional[str] = None
    source_url: Optional[str] = Field(default=None, max_length=2048)
    source_type: Optional[str] = Field(default=None, pattern=r"^(manual|url|file|clip)$")
    tags: Optional[list[str]] = None
    credibility_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    metadata: Optional[dict] = None


# ── Response ─────────────────────────────────────────────────────
class KnowledgeEntryResponse(BaseModel):
    id: UUID
    org_id: UUID
    title: str
    content: str
    source_url: Optional[str] = None
    source_type: str
    tags: list[str]
    credibility_score: Optional[float] = None
    metadata: dict
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Search ───────────────────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    tags: list[str] = Field(default_factory=list)
    source_type: Optional[str] = Field(default=None, pattern=r"^(manual|url|file|clip)$")
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SearchHit(BaseModel):
    id: UUID
    title: str
    content_snippet: str
    source_type: str
    tags: list[str]
    score: float
    credibility_score: Optional[float] = None
    created_at: Optional[datetime] = None


class SearchResult(BaseModel):
    hits: list[SearchHit]
    total: int
    query: str


# ── Import ───────────────────────────────────────────────────────
class ImportRequest(BaseModel):
    url: Optional[str] = Field(default=None, max_length=2048)
    file_name: Optional[str] = Field(default=None, max_length=500)
    file_content_base64: Optional[str] = None
    extract_facts: bool = Field(default=True)


class ImportResponse(BaseModel):
    entry_id: UUID
    title: str
    content_preview: str
    tags: list[str]
    source_type: str
    status: str = "completed"


# ── Summarize ────────────────────────────────────────────────────
class SummarizeResponse(BaseModel):
    entry_id: UUID
    summary: str
    key_points: list[str]
    suggested_tags: list[str]


# ── Tags ─────────────────────────────────────────────────────────
class TagListResponse(BaseModel):
    tags: list[str]
    counts: dict[str, int]


# ── Suggestions ──────────────────────────────────────────────────
class SuggestionEntry(BaseModel):
    topic: str
    reason: str
    search_query: str


class SuggestionsResponse(BaseModel):
    suggestions: list[SuggestionEntry]
