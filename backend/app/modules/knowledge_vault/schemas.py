"""Pydantic schemas for the Knowledge Vault module."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

# ── Source type literals ──────────────────────────────────────────
SOURCE_TYPES = {"manual", "url", "file", "clip"}


# ── Create / Update ──────────────────────────────────────────────
class CreateEntryRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(default="")
    source_url: str | None = Field(default=None, max_length=2048)
    source_type: str = Field(default="manual", pattern=r"^(manual|url|file|clip)$")
    tags: list[str] = Field(default_factory=list)
    credibility_score: float | None = Field(default=None, ge=0.0, le=1.0)
    category: str | None = Field(default=None, max_length=200)
    project_id: UUID | None = Field(default=None)
    metadata: dict = Field(default_factory=dict)


class UpdateEntryRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    content: str | None = None
    source_url: str | None = Field(default=None, max_length=2048)
    source_type: str | None = Field(default=None, pattern=r"^(manual|url|file|clip)$")
    tags: list[str] | None = None
    credibility_score: float | None = Field(default=None, ge=0.0, le=1.0)
    category: str | None = Field(default=None, max_length=200)
    project_id: UUID | None = None
    metadata: dict | None = None


# ── Response ─────────────────────────────────────────────────────
class KnowledgeEntryResponse(BaseModel):
    id: UUID
    org_id: UUID
    title: str
    content: str
    source_url: str | None = None
    source_type: str
    tags: list[str]
    credibility_score: float | None = None
    category: str | None = None
    project_id: UUID | None = None
    metadata: dict
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── Search ───────────────────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    tags: list[str] = Field(default_factory=list)
    source_type: str | None = Field(default=None, pattern=r"^(manual|url|file|clip)$")
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SearchHit(BaseModel):
    id: UUID
    title: str
    content_snippet: str
    source_type: str
    tags: list[str]
    score: float
    credibility_score: float | None = None
    created_at: datetime | None = None


class SearchResult(BaseModel):
    hits: list[SearchHit]
    total: int
    query: str


# ── Import ───────────────────────────────────────────────────────
class ImportRequest(BaseModel):
    url: str | None = Field(default=None, max_length=2048)
    file_name: str | None = Field(default=None, max_length=500)
    file_content_base64: str | None = None
    extract_facts: bool = Field(default=True)


class ImportURLRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)


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
