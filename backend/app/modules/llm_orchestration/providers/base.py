"""
Abstract LLM Provider Interface

Defines the contract that all provider implementations (Anthropic, OpenAI, etc.)
must satisfy, enabling a clean provider-abstraction layer.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class LLMRequest:
    """Normalized request sent to any LLM provider."""

    prompt: str
    system_prompt: str | None = None
    model_id: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 1.0
    stop_sequences: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Normalized response from any LLM provider."""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    model_id: str = ""
    content: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    finish_reason: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict = field(default_factory=dict)

    @property
    def succeeded(self) -> bool:
        return bool(self.content) and self.finish_reason != "error"


@dataclass
class LLMStreamChunk:
    """A single chunk of streamed output."""

    delta: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    finish_reason: str | None = None
    model_id: str = ""


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return canonical provider name (e.g. 'anthropic', 'openai')."""
        ...

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Send a completion request and return the full response."""
        ...

    @abstractmethod
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Send a completion request and yield streamed chunks."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider API is reachable."""
        ...
