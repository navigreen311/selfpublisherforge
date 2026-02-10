"""LLM provider implementations.

Provider-specific classes (AnthropicProvider, OpenAIProvider) are imported
lazily to avoid hard dependency on third-party SDKs at module load time.
"""

from app.modules.llm_orchestration.providers.base import (
    BaseLLMProvider,
    LLMRequest,
    LLMResponse,
    LLMStreamChunk,
)

__all__ = [
    "BaseLLMProvider",
    "LLMRequest",
    "LLMResponse",
    "LLMStreamChunk",
    "AnthropicProvider",
    "OpenAIProvider",
]


def __getattr__(name: str):
    if name == "AnthropicProvider":
        from app.modules.llm_orchestration.providers.anthropic import AnthropicProvider
        return AnthropicProvider
    if name == "OpenAIProvider":
        from app.modules.llm_orchestration.providers.openai import OpenAIProvider
        return OpenAIProvider
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
