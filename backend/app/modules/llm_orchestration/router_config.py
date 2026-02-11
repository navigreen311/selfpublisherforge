"""
Model Routing Configuration

Maps task types to primary and fallback LLM models. Implements selection
logic including progressive enhancement (Haiku draft -> Sonnet upgrade).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TaskType(str, Enum):
    """Supported generation task types."""

    LONG_FORM_WRITING = "long_form_writing"
    BLURB_AD_COPY = "blurb_ad_copy"
    MARKET_ANALYSIS = "market_analysis"
    STYLE_FINGERPRINTING = "style_fingerprinting"
    REVIEW_SENTIMENT = "review_sentiment"
    QUICK_EDITS_GRAMMAR = "quick_edits_grammar"


class ModelID(str, Enum):
    """Canonical model identifiers used across the orchestration layer."""

    CLAUDE_OPUS = "claude-opus-4-20250514"
    CLAUDE_SONNET = "claude-sonnet-4-5-20250929"
    CLAUDE_HAIKU = "claude-haiku-3-5-20241022"
    GPT_4 = "gpt-4o"
    GPT_4_MINI = "gpt-4o-mini"


class ProviderName(str, Enum):
    """LLM provider identifiers."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"


# Mapping from model ID to provider
MODEL_PROVIDER_MAP: dict[ModelID, ProviderName] = {
    ModelID.CLAUDE_OPUS: ProviderName.ANTHROPIC,
    ModelID.CLAUDE_SONNET: ProviderName.ANTHROPIC,
    ModelID.CLAUDE_HAIKU: ProviderName.ANTHROPIC,
    ModelID.GPT_4: ProviderName.OPENAI,
    ModelID.GPT_4_MINI: ProviderName.OPENAI,
}


@dataclass(frozen=True)
class ModelRoute:
    """A single routing rule: primary model + optional fallback chain."""

    primary: ModelID
    fallbacks: list[ModelID] = field(default_factory=list)
    max_tokens: int = 4096
    cache_ttl_seconds: int = 86400  # 24 hours default


# Blueprint routing table
ROUTING_TABLE: dict[TaskType, ModelRoute] = {
    TaskType.LONG_FORM_WRITING: ModelRoute(
        primary=ModelID.CLAUDE_OPUS,
        fallbacks=[ModelID.CLAUDE_SONNET],
        max_tokens=8192,
        cache_ttl_seconds=0,  # no caching for creative writing
    ),
    TaskType.BLURB_AD_COPY: ModelRoute(
        primary=ModelID.CLAUDE_SONNET,
        fallbacks=[ModelID.GPT_4],
        max_tokens=2048,
        cache_ttl_seconds=86400,  # 24h
    ),
    TaskType.MARKET_ANALYSIS: ModelRoute(
        primary=ModelID.CLAUDE_SONNET,
        fallbacks=[ModelID.GPT_4],
        max_tokens=4096,
        cache_ttl_seconds=86400,  # 24h
    ),
    TaskType.STYLE_FINGERPRINTING: ModelRoute(
        primary=ModelID.CLAUDE_OPUS,
        fallbacks=[],
        max_tokens=4096,
        cache_ttl_seconds=604800,  # 7 days
    ),
    TaskType.REVIEW_SENTIMENT: ModelRoute(
        primary=ModelID.CLAUDE_HAIKU,
        fallbacks=[ModelID.CLAUDE_SONNET],
        max_tokens=1024,
        cache_ttl_seconds=86400,  # 24h
    ),
    TaskType.QUICK_EDITS_GRAMMAR: ModelRoute(
        primary=ModelID.CLAUDE_HAIKU,
        fallbacks=[ModelID.GPT_4_MINI],
        max_tokens=2048,
        cache_ttl_seconds=0,  # no caching for edits
    ),
}


class ModelRouter:
    """Resolves task types to model selection with fallback support."""

    def __init__(
        self,
        routing_table: dict[TaskType, ModelRoute] | None = None,
    ) -> None:
        self._table = routing_table or ROUTING_TABLE

    def get_route(self, task_type: TaskType) -> ModelRoute:
        """Return the routing rule for a given task type."""
        if task_type not in self._table:
            raise ValueError(f"Unknown task type: {task_type}")
        return self._table[task_type]

    def get_primary_model(self, task_type: TaskType) -> ModelID:
        """Return the primary model for a task type."""
        return self.get_route(task_type).primary

    def get_fallback_chain(self, task_type: TaskType) -> list[ModelID]:
        """Return ordered fallback models (excluding primary)."""
        return list(self.get_route(task_type).fallbacks)

    def get_full_chain(self, task_type: TaskType) -> list[ModelID]:
        """Return [primary] + fallbacks as a single ordered list."""
        route = self.get_route(task_type)
        return [route.primary, *route.fallbacks]

    def get_provider(self, model_id: ModelID) -> ProviderName:
        """Return the provider name for a model."""
        return MODEL_PROVIDER_MAP[model_id]

    def get_max_tokens(self, task_type: TaskType) -> int:
        """Return max output tokens for a task type."""
        return self.get_route(task_type).max_tokens

    def get_cache_ttl(self, task_type: TaskType) -> int:
        """Return cache TTL in seconds for a task type (0 = no caching)."""
        return self.get_route(task_type).cache_ttl_seconds
