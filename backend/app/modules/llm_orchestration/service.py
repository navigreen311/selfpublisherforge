"""LLM Orchestration Service

High-level service layer that wraps the LLMOrchestrator, CostTracker, and
QualityAssurance components behind a clean async API.  Consumed by other
modules and by the router endpoints.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from app.modules.llm_orchestration.cache import SemanticCache
from app.modules.llm_orchestration.cost_tracker import MODEL_PRICING, CostTracker
from app.modules.llm_orchestration.orchestrator import (
    GenerationOptions,
    GenerationResult,
    LLMOrchestrator,
)
from app.modules.llm_orchestration.providers.base import BaseLLMProvider, LLMStreamChunk
from app.modules.llm_orchestration.quality import QualityAssurance
from app.modules.llm_orchestration.router_config import ModelRouter, ProviderName
from app.modules.llm_orchestration.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    CompletionRequest,
    CompletionResponse,
    CostEstimate,
    CostEstimateRequest,
    UsageStats,
)
from app.modules.llm_orchestration.schemas import (
    QualityReport as QualityReportSchema,
)

logger = logging.getLogger(__name__)


def _quality_report_to_schema(
    report: object,
) -> QualityReportSchema | None:
    """Convert an orchestrator QualityReport dataclass to the Pydantic schema."""
    if report is None:
        return None
    return QualityReportSchema(
        overall_level=report.overall_level.value,  # type: ignore[union-attr,attr-defined]
        overall_score=report.overall_score,  # type: ignore[union-attr,attr-defined]
        readability_score=report.readability_score,  # type: ignore[union-attr,attr-defined]
        readability_grade_level=report.readability_grade_level,  # type: ignore[union-attr,attr-defined]
        word_count=report.word_count,  # type: ignore[union-attr,attr-defined]
        sentence_count=report.sentence_count,  # type: ignore[union-attr,attr-defined]
        avg_sentence_length=report.avg_sentence_length,  # type: ignore[union-attr,attr-defined]
        plagiarism_flag=report.plagiarism_flag,  # type: ignore[union-attr,attr-defined]
        plagiarism_confidence=report.plagiarism_confidence,  # type: ignore[union-attr,attr-defined]
        hallucination_flag=report.hallucination_flag,  # type: ignore[union-attr,attr-defined]
        hallucination_confidence=report.hallucination_confidence,  # type: ignore[union-attr,attr-defined]
        issues=report.issues,  # type: ignore[union-attr,attr-defined]
        passes_threshold=report.passes_threshold,  # type: ignore[union-attr,attr-defined]
    )


def _result_to_completion_response(result: GenerationResult) -> CompletionResponse:
    """Map an orchestrator GenerationResult to a CompletionResponse schema."""
    return CompletionResponse(
        content=result.content,
        model_id=result.model_id,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        total_tokens=result.total_tokens,
        cost_usd=result.cost_usd,
        latency_ms=result.latency_ms,
        cache_hit=result.cache_hit,
        fallback_used=result.fallback_used,
        attempts=result.attempts,
        quality_report=_quality_report_to_schema(result.quality_report),
        succeeded=result.succeeded,
        metadata=result.metadata,
    )


def _result_to_chat_response(result: GenerationResult) -> ChatResponse:
    """Map an orchestrator GenerationResult to a ChatResponse schema."""
    return ChatResponse(
        content=result.content,
        model_id=result.model_id,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        total_tokens=result.total_tokens,
        cost_usd=result.cost_usd,
        latency_ms=result.latency_ms,
        cache_hit=result.cache_hit,
        fallback_used=result.fallback_used,
        attempts=result.attempts,
        quality_report=_quality_report_to_schema(result.quality_report),
        succeeded=result.succeeded,
        metadata=result.metadata,
    )


class LLMOrchestrationService:
    """Async service layer for LLM orchestration.

    Wraps :class:`LLMOrchestrator` and exposes a simplified interface that
    accepts Pydantic request schemas and returns Pydantic response schemas.

    Usage::

        service = LLMOrchestrationService()
        service.register_provider(ProviderName.ANTHROPIC, AnthropicProvider())
        service.register_provider(ProviderName.OPENAI, OpenAIProvider())

        response = await service.complete(CompletionRequest(...))
    """

    def __init__(
        self,
        providers: dict[ProviderName, BaseLLMProvider] | None = None,
        router: ModelRouter | None = None,
        cache: SemanticCache | None = None,
        cost_tracker: CostTracker | None = None,
        quality: QualityAssurance | None = None,
    ) -> None:
        self._cost_tracker = cost_tracker or CostTracker()
        self._quality = quality or QualityAssurance()
        self._orchestrator = LLMOrchestrator(
            providers=providers,
            router=router,
            cache=cache,
            cost_tracker=self._cost_tracker,
            quality=self._quality,
        )

    # ------------------------------------------------------------------
    # Provider management
    # ------------------------------------------------------------------

    def register_provider(self, name: ProviderName, provider: BaseLLMProvider) -> None:
        """Register an LLM provider implementation."""
        self._orchestrator.register_provider(name, provider)

    # ------------------------------------------------------------------
    # Completion (single-turn)
    # ------------------------------------------------------------------

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Run a single-turn completion through the orchestrator.

        Handles routing, caching, fallback, cost tracking, and quality
        assurance transparently.
        """
        options = GenerationOptions(
            temperature=request.config.temperature,
            top_p=request.config.top_p,
            max_tokens=request.config.max_tokens,
            system_prompt=request.system_prompt,
            stop_sequences=request.config.stop_sequences,
            stream=False,
            skip_cache=request.config.skip_cache,
            skip_quality_check=request.config.skip_quality_check,
            org_id=request.org_id,
            metadata=request.metadata,
        )

        result = await self._orchestrator.generate(
            task_type=request.task_type.value,
            prompt=request.prompt,
            context=request.context,
            options=options,
        )

        return _result_to_completion_response(result)

    async def complete_stream(self, request: CompletionRequest) -> AsyncIterator[LLMStreamChunk]:
        """Stream a single-turn completion through the orchestrator.

        Yields :class:`LLMStreamChunk` objects. Streaming bypasses caching
        and quality checks since content arrives incrementally.
        """
        options = GenerationOptions(
            temperature=request.config.temperature,
            top_p=request.config.top_p,
            max_tokens=request.config.max_tokens,
            system_prompt=request.system_prompt,
            stop_sequences=request.config.stop_sequences,
            stream=True,
            skip_cache=request.config.skip_cache,
            skip_quality_check=request.config.skip_quality_check,
            org_id=request.org_id,
            metadata=request.metadata,
        )

        async for chunk in self._orchestrator.generate_stream(
            task_type=request.task_type.value,
            prompt=request.prompt,
            context=request.context,
            options=options,
        ):
            yield chunk

    # ------------------------------------------------------------------
    # Chat (multi-turn)
    # ------------------------------------------------------------------

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Run a multi-turn chat completion.

        Flattens the message history into a single prompt (with role
        annotations) and delegates to the orchestrator.  The last user
        message is treated as the primary prompt, and preceding messages
        form the context.
        """
        prompt, context = self._flatten_messages(request.messages)

        options = GenerationOptions(
            temperature=request.config.temperature,
            top_p=request.config.top_p,
            max_tokens=request.config.max_tokens,
            system_prompt=request.system_prompt,
            stop_sequences=request.config.stop_sequences,
            stream=False,
            skip_cache=request.config.skip_cache,
            skip_quality_check=request.config.skip_quality_check,
            org_id=request.org_id,
            metadata=request.metadata,
        )

        result = await self._orchestrator.generate(
            task_type=request.task_type.value,
            prompt=prompt,
            context=context,
            options=options,
        )

        return _result_to_chat_response(result)

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[LLMStreamChunk]:
        """Stream a multi-turn chat completion.

        Yields :class:`LLMStreamChunk` objects.
        """
        prompt, context = self._flatten_messages(request.messages)

        options = GenerationOptions(
            temperature=request.config.temperature,
            top_p=request.config.top_p,
            max_tokens=request.config.max_tokens,
            system_prompt=request.system_prompt,
            stop_sequences=request.config.stop_sequences,
            stream=True,
            skip_cache=request.config.skip_cache,
            skip_quality_check=request.config.skip_quality_check,
            org_id=request.org_id,
            metadata=request.metadata,
        )

        async for chunk in self._orchestrator.generate_stream(
            task_type=request.task_type.value,
            prompt=prompt,
            context=context,
            options=options,
        ):
            yield chunk

    # ------------------------------------------------------------------
    # Cost estimation
    # ------------------------------------------------------------------

    def estimate_cost(self, request: CostEstimateRequest) -> CostEstimate:
        """Estimate the USD cost for a given model and token counts.

        This is a synchronous operation -- no API call is made.
        """
        cost_usd = self._cost_tracker.calculate_cost(
            model_id=request.model_id,
            input_tokens=request.estimated_input_tokens,
            output_tokens=request.estimated_output_tokens,
        )

        pricing = MODEL_PRICING.get(request.model_id)
        input_cost_per_1k = pricing.input_cost_per_1k if pricing else 0.0
        output_cost_per_1k = pricing.output_cost_per_1k if pricing else 0.0

        return CostEstimate(
            model_id=request.model_id,
            estimated_input_tokens=request.estimated_input_tokens,
            estimated_output_tokens=request.estimated_output_tokens,
            estimated_cost_usd=cost_usd,
            input_cost_per_1k=input_cost_per_1k,
            output_cost_per_1k=output_cost_per_1k,
        )

    # ------------------------------------------------------------------
    # Usage statistics
    # ------------------------------------------------------------------

    def get_usage_stats(self, org_id: str, model_id: str | None = None) -> UsageStats:
        """Return aggregated usage statistics for an organization.

        This is a synchronous operation backed by the in-memory cost tracker.
        """
        summary = self._cost_tracker.get_usage_summary(org_id=org_id, model_id=model_id)

        return UsageStats(
            org_id=summary["org_id"],
            request_count=summary["request_count"],
            total_input_tokens=summary["total_input_tokens"],
            total_output_tokens=summary["total_output_tokens"],
            total_cost_usd=summary["total_cost_usd"],
            budget_usd=summary["budget"],
            remaining_usd=summary["remaining_usd"],
            alert_level=summary["alert_level"],
        )

    # ------------------------------------------------------------------
    # Quality assessment (standalone)
    # ------------------------------------------------------------------

    def assess_quality(self, content: str, task_type: str | None = None) -> QualityReportSchema:
        """Run a standalone quality assessment on arbitrary text.

        Useful for evaluating content that was not generated through the
        orchestrator (e.g. user-supplied text).
        """
        report = self._quality.assess(content, task_type=task_type)
        schema = _quality_report_to_schema(report)
        # _quality_report_to_schema returns Optional but assess() always
        # returns a non-None report, so this is safe.
        assert schema is not None
        return schema

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _flatten_messages(
        messages: list[ChatMessage],
    ) -> tuple[str, str | None]:
        """Flatten a list of chat messages into (prompt, context).

        The last user message becomes the prompt.  All preceding messages
        are concatenated as role-annotated context lines.
        """
        if not messages:
            return "", None

        # The last message is the prompt
        prompt = messages[-1].content

        # Build context from preceding messages
        if len(messages) <= 1:
            return prompt, None

        context_lines: list[str] = []
        for msg in messages[:-1]:
            context_lines.append(f"[{msg.role}]: {msg.content}")

        context = "\n\n".join(context_lines)
        return prompt, context
