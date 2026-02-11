"""
OpenAI Provider

Wraps the OpenAI SDK to implement the BaseLLMProvider interface,
supporting GPT-4o and GPT-4o Mini models.
"""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator

import openai

from app.config import get_settings
from app.modules.llm_orchestration.providers.base import (
    BaseLLMProvider,
    LLMRequest,
    LLMResponse,
    LLMStreamChunk,
)

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT-4 / GPT-4 Mini provider."""

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self._api_key = api_key or settings.OPENAI_API_KEY
        self._client = openai.AsyncOpenAI(api_key=self._api_key)

    @property
    def provider_name(self) -> str:
        return "openai"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Send a non-streaming completion request to OpenAI."""
        start = time.perf_counter()
        try:
            messages = self._build_messages(request)
            kwargs = self._build_kwargs(request, messages)
            response = await self._client.chat.completions.create(**kwargs)
            latency_ms = (time.perf_counter() - start) * 1000

            choice = response.choices[0] if response.choices else None
            content = choice.message.content or "" if choice else ""
            finish_reason = choice.finish_reason or "stop" if choice else "error"
            usage = response.usage

            return LLMResponse(
                model_id=request.model_id,
                content=content,
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
                latency_ms=latency_ms,
                finish_reason=finish_reason,
            )

        except openai.APIError as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.error("OpenAI API error for model %s: %s", request.model_id, exc)
            return LLMResponse(
                model_id=request.model_id,
                content="",
                latency_ms=latency_ms,
                finish_reason="error",
                metadata={"error": str(exc)},
            )

    async def generate_stream(  # type: ignore[override,misc]
        self, request: LLMRequest
    ) -> AsyncIterator[LLMStreamChunk]:
        """Stream response chunks from OpenAI."""
        try:
            messages = self._build_messages(request)
            kwargs = self._build_kwargs(request, messages, stream=True)
            stream = await self._client.chat.completions.create(**kwargs)

            async for chunk in stream:
                choice = chunk.choices[0] if chunk.choices else None
                if choice is None:
                    continue

                delta = choice.delta
                content = delta.content or "" if delta else ""
                finish = choice.finish_reason

                yield LLMStreamChunk(
                    delta=content,
                    finish_reason=finish,
                    model_id=request.model_id,
                )

        except openai.APIError as exc:
            logger.error("OpenAI stream error for model %s: %s", request.model_id, exc)
            yield LLMStreamChunk(
                delta="",
                finish_reason="error",
                model_id=request.model_id,
            )

    async def health_check(self) -> bool:
        """Verify API connectivity with a minimal request."""
        try:
            await self._client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except (ConnectionError, openai.APIConnectionError, openai.APITimeoutError):
            logger.warning("OpenAI health check failed: connection error", exc_info=True)
            return False
        except openai.APIError as exc:
            logger.warning("OpenAI health check failed: API error: %s", exc, exc_info=True)
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_messages(request: LLMRequest) -> list[dict]:
        """Convert LLMRequest into OpenAI message format."""
        messages: list[dict] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        return messages

    @staticmethod
    def _build_kwargs(
        request: LLMRequest,
        messages: list[dict],
        stream: bool = False,
    ) -> dict:
        """Build kwargs dict for the OpenAI chat.completions.create call."""
        kwargs: dict = {
            "model": request.model_id,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "messages": messages,
            "stream": stream,
        }
        if request.stop_sequences:
            kwargs["stop"] = request.stop_sequences
        return kwargs
