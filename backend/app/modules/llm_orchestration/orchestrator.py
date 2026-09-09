"""
Central LLM Orchestrator

Single entry point for all LLM generation in the application.
Routes requests to the correct model based on task type, handles
streaming (SSE), retries with fallback chains, caching, cost tracking,
and post-generation quality assurance with progressive enhancement.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from app.modules.llm_orchestration.cache import SemanticCache
from app.modules.llm_orchestration.cost_tracker import CostTracker
from app.modules.llm_orchestration.providers.base import (
    BaseLLMProvider,
    LLMRequest,
    LLMStreamChunk,
)
from app.modules.llm_orchestration.quality import QualityAssurance, QualityReport
from app.modules.llm_orchestration.router_config import (
    ModelRouter,
    ProviderName,
)

logger = logging.getLogger(__name__)


@dataclass
class GenerationOptions:
    """User-facing options for a generation request."""

    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: int | None = None  # None = use route default
    system_prompt: str | None = None
    stop_sequences: list[str] = field(default_factory=list)
    stream: bool = False
    skip_cache: bool = False
    skip_quality_check: bool = False
    org_id: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class GenerationResult:
    """Full result of an orchestrated generation."""

    content: str = ""
    model_id: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    cache_hit: bool = False
    quality_report: QualityReport | None = None
    fallback_used: bool = False
    attempts: int = 0
    metadata: dict = field(default_factory=dict)

    @property
    def succeeded(self) -> bool:
        return bool(self.content)


class LLMOrchestrator:
    """Central orchestration engine for all LLM interactions."""

    def __init__(
        self,
        providers: dict[ProviderName, BaseLLMProvider] | None = None,
        router: ModelRouter | None = None,
        cache: SemanticCache | None = None,
        cost_tracker: CostTracker | None = None,
        quality: QualityAssurance | None = None,
    ) -> None:
        self._providers: dict[ProviderName, BaseLLMProvider] = providers or {}
        self._router = router or ModelRouter()
        self._cache = cache or SemanticCache()
        self._cost_tracker = cost_tracker or CostTracker()
        self._quality = quality or QualityAssurance()

    def register_provider(self, name: ProviderName, provider: BaseLLMProvider) -> None:
        """Register a provider implementation."""
        self._providers[name] = provider

    # ------------------------------------------------------------------
    # Non-streaming generation
    # ------------------------------------------------------------------

    async def generate(
        self,
        task_type: str,
        prompt: str,
        context: str | None = None,
        options: GenerationOptions | None = None,
    ) -> GenerationResult:
        """Generate a complete response with routing, caching, cost tracking,
        fallback, and quality assurance."""
        from app.modules.llm_orchestration.router_config import TaskType

        opts = options or GenerationOptions()
        task = TaskType(task_type)
        result = GenerationResult()

        # Merge context into prompt
        full_prompt = f"{context}\n\n{prompt}" if context else prompt

        # 1. Check cache
        if not opts.skip_cache:
            primary_model = self._router.get_primary_model(task)
            cached = await self._cache.get(
                task_type=task,
                prompt=full_prompt,
                model_id=primary_model.value,
                system_prompt=opts.system_prompt,
            )
            if cached:
                result.content = cached.get("content", "")
                result.model_id = cached.get("model_id", primary_model.value)
                result.input_tokens = cached.get("input_tokens", 0)
                result.output_tokens = cached.get("output_tokens", 0)
                result.total_tokens = cached.get("total_tokens", 0)
                result.cost_usd = 0.0  # cached = free
                result.cache_hit = True
                result.attempts = 0
                logger.info("Cache hit for task=%s", task.value)
                return result

        # 2. Check budget
        if opts.org_id and not self._cost_tracker.check_budget(opts.org_id):
            logger.warning("Budget exceeded for org %s", opts.org_id)
            result.metadata["error"] = "monthly_budget_exceeded"
            return result

        # 3. Try each model in the chain (primary + fallbacks)
        chain = self._router.get_full_chain(task)
        max_tokens = opts.max_tokens or self._router.get_max_tokens(task)

        for i, model_id in enumerate(chain):
            result.attempts += 1
            provider_name = self._router.get_provider(model_id)
            provider = self._providers.get(provider_name)

            if provider is None:
                logger.warning(
                    "No provider registered for %s, skipping %s",
                    provider_name.value,
                    model_id.value,
                )
                continue

            request = LLMRequest(
                prompt=full_prompt,
                system_prompt=opts.system_prompt,
                model_id=model_id.value,
                max_tokens=max_tokens,
                temperature=opts.temperature,
                top_p=opts.top_p,
                stop_sequences=opts.stop_sequences,
                metadata=opts.metadata,
            )

            response = await provider.generate(request)

            if response.succeeded:
                result.content = response.content
                result.model_id = response.model_id
                result.input_tokens = response.input_tokens
                result.output_tokens = response.output_tokens
                result.total_tokens = response.total_tokens
                result.latency_ms = response.latency_ms
                result.fallback_used = i > 0

                # Quality check + progressive enhancement
                if not opts.skip_quality_check:
                    report = self._quality.assess(result.content, task.value)
                    result.quality_report = report

                    # If quality is below threshold and we have more models,
                    # try the next one (progressive enhancement)
                    if self._quality.needs_enhancement(report) and i < len(chain) - 1:
                        logger.info(
                            "Quality score %.1f below threshold, escalating from %s",
                            report.overall_score,
                            model_id.value,
                        )
                        continue

                # Cost tracking
                cost = self._cost_tracker.calculate_cost(
                    result.model_id,
                    result.input_tokens,
                    result.output_tokens,
                )
                result.cost_usd = cost

                if opts.org_id:
                    await self._cost_tracker.record_usage(
                        org_id=opts.org_id,
                        model_id=result.model_id,
                        task_type=task.value,
                        input_tokens=result.input_tokens,
                        output_tokens=result.output_tokens,
                    )

                # Cache the response
                if not opts.skip_cache:
                    await self._cache.set(
                        task_type=task,
                        prompt=full_prompt,
                        model_id=result.model_id,
                        response_data={
                            "content": result.content,
                            "model_id": result.model_id,
                            "input_tokens": result.input_tokens,
                            "output_tokens": result.output_tokens,
                            "total_tokens": result.total_tokens,
                        },
                        system_prompt=opts.system_prompt,
                    )

                logger.info(
                    "Generation complete: task=%s model=%s tokens=%d cost=$%.6f latency=%.0fms",
                    task.value,
                    result.model_id,
                    result.total_tokens,
                    result.cost_usd,
                    result.latency_ms,
                )
                return result

            # Current model failed — try next in chain
            logger.warning(
                "Model %s failed for task %s, trying fallback",
                model_id.value,
                task.value,
            )

        # All models failed
        logger.error("All models exhausted for task %s", task.value)
        result.metadata["error"] = "all_models_failed"
        return result

    # ------------------------------------------------------------------
    # Streaming generation
    # ------------------------------------------------------------------

    async def generate_stream(
        self,
        task_type: str,
        prompt: str,
        context: str | None = None,
        options: GenerationOptions | None = None,
    ) -> AsyncIterator[LLMStreamChunk]:
        """Stream response chunks with model routing and fallback.

        Note: streaming bypasses caching and quality checks since
        content arrives incrementally.
        """
        from app.modules.llm_orchestration.router_config import TaskType

        opts = options or GenerationOptions()
        task = TaskType(task_type)
        full_prompt = f"{context}\n\n{prompt}" if context else prompt

        # Budget check
        if opts.org_id and not self._cost_tracker.check_budget(opts.org_id):
            yield LLMStreamChunk(
                delta="",
                finish_reason="budget_exceeded",
            )
            return

        chain = self._router.get_full_chain(task)
        max_tokens = opts.max_tokens or self._router.get_max_tokens(task)

        for i, model_id in enumerate(chain):
            provider_name = self._router.get_provider(model_id)
            provider = self._providers.get(provider_name)
            if provider is None:
                continue

            request = LLMRequest(
                prompt=full_prompt,
                system_prompt=opts.system_prompt,
                model_id=model_id.value,
                max_tokens=max_tokens,
                temperature=opts.temperature,
                top_p=opts.top_p,
                stop_sequences=opts.stop_sequences,
                metadata=opts.metadata,
            )

            had_content = False
            errored = False

            async for chunk in provider.generate_stream(request):  # type: ignore[attr-defined]
                if chunk.finish_reason == "error":
                    errored = True
                    break
                if chunk.delta:
                    had_content = True
                yield chunk

            if had_content and not errored:
                # Track cost (approximate — stream may not report exact token counts)
                if opts.org_id:
                    await self._cost_tracker.record_usage(
                        org_id=opts.org_id,
                        model_id=model_id.value,
                        task_type=task.value,
                        input_tokens=0,  # exact count unavailable in stream
                        output_tokens=0,
                    )
                return

            # Stream failed — try next model
            logger.warning(
                "Stream from %s failed for task %s, trying fallback",
                model_id.value,
                task.value,
            )

        # All models failed
        yield LLMStreamChunk(
            delta="",
            finish_reason="all_models_failed",
        )
