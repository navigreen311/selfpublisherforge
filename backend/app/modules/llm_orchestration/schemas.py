"""Pydantic schemas for the LLM Orchestration module.

Request/response models for completion, chat, cost estimation,
quality reporting, and usage statistics.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    """Return timezone-aware UTC now."""
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TaskTypeEnum(str, Enum):
    """Mirrors router_config.TaskType for API validation."""

    LONG_FORM_WRITING = "long_form_writing"
    BLURB_AD_COPY = "blurb_ad_copy"
    MARKET_ANALYSIS = "market_analysis"
    STYLE_FINGERPRINTING = "style_fingerprinting"
    REVIEW_SENTIMENT = "review_sentiment"
    QUICK_EDITS_GRAMMAR = "quick_edits_grammar"


class QualityLevelEnum(str, Enum):
    """Discrete quality rating returned in quality reports."""

    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Chat messages
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    """A single message in a chat conversation."""

    role: str = Field(
        ...,
        description="Message role: 'system', 'user', or 'assistant'.",
        pattern="^(system|user|assistant)$",
    )
    content: str = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# Model configuration
# ---------------------------------------------------------------------------

class ModelConfig(BaseModel):
    """Per-request model configuration overrides."""

    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    max_tokens: int | None = Field(
        default=None,
        ge=1,
        description="Max output tokens. None uses the route default.",
    )
    stop_sequences: list[str] = Field(default_factory=list)
    stream: bool = False
    skip_cache: bool = False
    skip_quality_check: bool = False


# ---------------------------------------------------------------------------
# Completion request / response
# ---------------------------------------------------------------------------

class CompletionRequest(BaseModel):
    """Request body for a single-turn LLM completion."""

    task_type: TaskTypeEnum
    prompt: str = Field(..., min_length=1, max_length=100_000)
    context: str | None = Field(
        default=None,
        max_length=200_000,
        description="Optional context prepended to the prompt.",
    )
    system_prompt: str | None = Field(
        default=None,
        max_length=50_000,
        description="Optional system prompt for the model.",
    )
    config: ModelConfig = Field(default_factory=ModelConfig)
    org_id: str | None = Field(
        default=None,
        description="Organization ID for budget tracking.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class CompletionResponse(BaseModel):
    """Response body for a completed LLM generation."""
    model_config = ConfigDict(protected_namespaces=())

    content: str = ""
    model_id: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    cache_hit: bool = False
    fallback_used: bool = False
    attempts: int = 0
    quality_report: QualityReport | None = None
    succeeded: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Chat request / response
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """Request body for a multi-turn chat completion.

    The last message in ``messages`` is treated as the prompt; preceding
    messages provide conversational context.
    """

    task_type: TaskTypeEnum
    messages: list[ChatMessage] = Field(..., min_length=1)
    system_prompt: str | None = Field(
        default=None,
        max_length=50_000,
    )
    config: ModelConfig = Field(default_factory=ModelConfig)
    org_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Response body for a chat completion."""
    model_config = ConfigDict(protected_namespaces=())

    content: str = ""
    model_id: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    cache_hit: bool = False
    fallback_used: bool = False
    attempts: int = 0
    quality_report: QualityReport | None = None
    succeeded: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Cost estimation
# ---------------------------------------------------------------------------

class CostEstimateRequest(BaseModel):
    """Request body for estimating the cost of a generation."""
    model_config = ConfigDict(protected_namespaces=())

    model_id: str = Field(
        ...,
        description="The model identifier (e.g. 'claude-opus-4-20250514').",
    )
    estimated_input_tokens: int = Field(..., ge=0)
    estimated_output_tokens: int = Field(..., ge=0)


class CostEstimate(BaseModel):
    """Estimated USD cost for a generation request."""
    model_config = ConfigDict(protected_namespaces=())

    model_id: str
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    input_cost_per_1k: float = 0.0
    output_cost_per_1k: float = 0.0


# ---------------------------------------------------------------------------
# Quality report
# ---------------------------------------------------------------------------

class QualityReport(BaseModel):
    """Quality assessment of a generated LLM response."""

    overall_level: QualityLevelEnum = QualityLevelEnum.GOOD
    overall_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Overall quality score (0-100).",
    )
    readability_score: float = 0.0
    readability_grade_level: float = 0.0
    word_count: int = 0
    sentence_count: int = 0
    avg_sentence_length: float = 0.0
    plagiarism_flag: bool = False
    plagiarism_confidence: float = 0.0
    hallucination_flag: bool = False
    hallucination_confidence: float = 0.0
    issues: list[str] = Field(default_factory=list)
    passes_threshold: bool = True


# ---------------------------------------------------------------------------
# Usage statistics
# ---------------------------------------------------------------------------

class UsageStats(BaseModel):
    """Aggregated usage statistics for an organization."""

    org_id: str
    request_count: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    budget_usd: float = 0.0
    remaining_usd: float = 0.0
    alert_level: str = "none"


# ---------------------------------------------------------------------------
# Forward reference resolution
# ---------------------------------------------------------------------------

# CompletionResponse and ChatResponse reference QualityReport, which is
# defined after them.  Pydantic v2 deferred resolution requires an explicit
# model_rebuild() call so the forward reference is resolved correctly.
CompletionResponse.model_rebuild()
ChatResponse.model_rebuild()
