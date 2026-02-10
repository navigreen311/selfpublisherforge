"""
Anthropic (Claude) Provider

Wraps the Anthropic SDK to implement the BaseLLMProvider interface,
supporting Claude Opus, Sonnet, and Haiku models.
"""

from __future__ import annotations

import logging
import time
from typing import AsyncIterator

import anthropic

from app.config import get_settings
from app.modules.llm_orchestration.providers.base import (
    BaseLLMProvider,
    LLMRequest,
    LLMResponse,
    LLMStreamChunk,
)

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Claude API provider (Opus, Sonnet, Haiku)."""

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.ANTHROPIC_API_KEY
        self._client = anthropic.AsyncAnthropic(api_key=self._api_key)

    @property
    def provider_name(self) -> str:
        return "anthropic"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Send a synchronous (non-streaming) message to Claude."""
        start = time.perf_counter()
        try:
            kwargs = self._build_kwargs(request)
            message = await self._client.messages.create(**kwargs)
            latency_ms = (time.perf_counter() - start) * 1000

            content = ""
            for block in message.content:
                if block.type == "text":
                    content += block.text

            return LLMResponse(
                model_id=request.model_id,
                content=content,
                input_tokens=message.usage.input_tokens,
                output_tokens=message.usage.output_tokens,
                total_tokens=message.usage.input_tokens + message.usage.output_tokens,
                latency_ms=latency_ms,
                finish_reason=message.stop_reason or "end_turn",
            )

        except anthropic.APIError as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.error("Anthropic API error for model %s: %s", request.model_id, exc)
            return LLMResponse(
                model_id=request.model_id,
                content="",
                latency_ms=latency_ms,
                finish_reason="error",
                metadata={"error": str(exc)},
            )

    async def generate_stream(
        self, request: LLMRequest
    ) -> AsyncIterator[LLMStreamChunk]:
        """Stream response chunks from Claude using SSE."""
        try:
            kwargs = self._build_kwargs(request)
            async with self._client.messages.stream(**kwargs) as stream:
                async for event in stream:
                    if hasattr(event, "type"):
                        if event.type == "content_block_delta":
                            yield LLMStreamChunk(
                                delta=event.delta.text if hasattr(event.delta, "text") else "",
                                model_id=request.model_id,
                            )
                        elif event.type == "message_delta":
                            usage = getattr(event, "usage", None)
                            yield LLMStreamChunk(
                                delta="",
                                output_tokens=usage.output_tokens if usage else 0,
                                finish_reason=getattr(event.delta, "stop_reason", None),
                                model_id=request.model_id,
                            )
                        elif event.type == "message_start":
                            msg = getattr(event, "message", None)
                            if msg and hasattr(msg, "usage"):
                                yield LLMStreamChunk(
                                    delta="",
                                    input_tokens=msg.usage.input_tokens,
                                    model_id=request.model_id,
                                )

        except anthropic.APIError as exc:
            logger.error("Anthropic stream error for model %s: %s", request.model_id, exc)
            yield LLMStreamChunk(
                delta="",
                finish_reason="error",
                model_id=request.model_id,
            )

    async def health_check(self) -> bool:
        """Verify API connectivity with a minimal request."""
        try:
            await self._client.messages.create(
                model="claude-haiku-3-5-20241022",
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_kwargs(request: LLMRequest) -> dict:
        """Build kwargs dict for the Anthropic messages.create call."""
        kwargs: dict = {
            "model": request.model_id,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "messages": [{"role": "user", "content": request.prompt}],
        }
        if request.system_prompt:
            kwargs["system"] = request.system_prompt
        if request.stop_sequences:
            kwargs["stop_sequences"] = request.stop_sequences
        return kwargs
