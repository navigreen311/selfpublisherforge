"""
Integration tests for the LLM orchestration flow.

Tests the full generation pipeline with mocked providers: routing,
fallback, caching, cost tracking, quality checks, streaming,
and budget enforcement.
"""

from __future__ import annotations

from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from app.modules.llm_orchestration.cache import SemanticCache
from app.modules.llm_orchestration.cost_tracker import BudgetAlertLevel, CostTracker
from app.modules.llm_orchestration.orchestrator import (
    GenerationOptions,
    GenerationResult,
    LLMOrchestrator,
)
from app.modules.llm_orchestration.providers.base import (
    BaseLLMProvider,
    LLMRequest,
    LLMResponse,
    LLMStreamChunk,
)
from app.modules.llm_orchestration.quality import QualityAssurance
from app.modules.llm_orchestration.router_config import (
    ModelID,
    ModelRouter,
    ProviderName,
    TaskType,
)


# -------------------------------------------------------------------
# Mock provider factory
# -------------------------------------------------------------------

def make_mock_provider(
    provider_name: str,
    content: str = "Mock response content with enough words to pass quality checks. "
    "This is a well-formed sentence that contains multiple clauses. "
    "The content is designed to achieve an acceptable readability score.",
    input_tokens: int = 100,
    output_tokens: int = 200,
    succeed: bool = True,
) -> BaseLLMProvider:
    """Create a mock LLM provider that returns configurable responses."""
    provider = AsyncMock(spec=BaseLLMProvider)
    provider.provider_name = provider_name

    async def _generate(request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            model_id=request.model_id,  # echo back the routed model
            content=content if succeed else "",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=50.0,
            finish_reason="end_turn" if succeed else "error",
        )

    provider.generate = AsyncMock(side_effect=_generate)

    async def _stream(request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        if succeed:
            words = content.split()
            for word in words:
                yield LLMStreamChunk(delta=word + " ", model_id=request.model_id)
            yield LLMStreamChunk(
                delta="", finish_reason="end_turn", model_id=request.model_id
            )
        else:
            yield LLMStreamChunk(
                delta="", finish_reason="error", model_id=request.model_id
            )

    provider.generate_stream = _stream
    provider.health_check = AsyncMock(return_value=True)

    return provider


# -------------------------------------------------------------------
# Mock Redis for cache
# -------------------------------------------------------------------

def make_mock_redis() -> AsyncMock:
    redis = AsyncMock()
    redis._store: dict[str, str] = {}
    redis._ttls: dict[str, int] = {}

    async def _get(key):
        return redis._store.get(key)

    async def _set(key, value, ex=None):
        redis._store[key] = value
        if ex is not None:
            redis._ttls[key] = ex

    async def _delete(key):
        if key in redis._store:
            del redis._store[key]
            return 1
        return 0

    redis.get = AsyncMock(side_effect=_get)
    redis.set = AsyncMock(side_effect=_set)
    redis.delete = AsyncMock(side_effect=_delete)

    return redis


# -------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------

@pytest.fixture
def mock_anthropic() -> BaseLLMProvider:
    return make_mock_provider("anthropic")


@pytest.fixture
def mock_openai() -> BaseLLMProvider:
    return make_mock_provider("openai")


@pytest.fixture
def failing_anthropic() -> BaseLLMProvider:
    return make_mock_provider("anthropic", succeed=False)


@pytest.fixture
def mock_redis() -> AsyncMock:
    return make_mock_redis()


@pytest.fixture
def orchestrator(
    mock_anthropic: BaseLLMProvider,
    mock_openai: BaseLLMProvider,
    mock_redis: AsyncMock,
) -> LLMOrchestrator:
    cache = SemanticCache(redis_client=mock_redis)
    return LLMOrchestrator(
        providers={
            ProviderName.ANTHROPIC: mock_anthropic,
            ProviderName.OPENAI: mock_openai,
        },
        router=ModelRouter(),
        cache=cache,
        cost_tracker=CostTracker(),
        quality=QualityAssurance(),
    )


@pytest.fixture
def orchestrator_with_failing_primary(
    failing_anthropic: BaseLLMProvider,
    mock_openai: BaseLLMProvider,
    mock_redis: AsyncMock,
) -> LLMOrchestrator:
    cache = SemanticCache(redis_client=mock_redis)
    return LLMOrchestrator(
        providers={
            ProviderName.ANTHROPIC: failing_anthropic,
            ProviderName.OPENAI: mock_openai,
        },
        router=ModelRouter(),
        cache=cache,
        cost_tracker=CostTracker(),
        quality=QualityAssurance(),
    )


# -------------------------------------------------------------------
# Basic generation flow
# -------------------------------------------------------------------

@pytest.mark.asyncio
class TestBasicGeneration:
    """End-to-end generation with mocked providers."""

    async def test_successful_generation(self, orchestrator: LLMOrchestrator):
        result = await orchestrator.generate(
            task_type=TaskType.BLURB_AD_COPY.value,
            prompt="Write a blurb for a mystery novel",
        )
        assert result.succeeded
        assert result.content != ""
        assert result.attempts == 1

    async def test_generation_tracks_cost(self, orchestrator: LLMOrchestrator):
        opts = GenerationOptions(org_id="org-integration-test")
        result = await orchestrator.generate(
            task_type=TaskType.MARKET_ANALYSIS.value,
            prompt="Analyze the romance genre market",
            options=opts,
        )
        assert result.succeeded
        assert result.cost_usd >= 0

    async def test_generation_with_context(self, orchestrator: LLMOrchestrator):
        result = await orchestrator.generate(
            task_type=TaskType.BLURB_AD_COPY.value,
            prompt="Write ad copy",
            context="Book is about a detective in 1920s Paris",
        )
        assert result.succeeded

    async def test_generation_with_options(self, orchestrator: LLMOrchestrator):
        opts = GenerationOptions(
            temperature=0.3,
            max_tokens=512,
            system_prompt="You are a book marketing expert.",
        )
        result = await orchestrator.generate(
            task_type=TaskType.BLURB_AD_COPY.value,
            prompt="Write a compelling blurb",
            options=opts,
        )
        assert result.succeeded


# -------------------------------------------------------------------
# Fallback behaviour
# -------------------------------------------------------------------

@pytest.mark.asyncio
class TestFallbackBehaviour:
    """Test fallback to secondary models when primary fails."""

    async def test_falls_back_on_primary_failure(
        self, orchestrator_with_failing_primary: LLMOrchestrator
    ):
        # Blurb: primary=Sonnet(anthropic, fails) -> fallback=GPT-4(openai, succeeds)
        result = await orchestrator_with_failing_primary.generate(
            task_type=TaskType.BLURB_AD_COPY.value,
            prompt="Write a blurb",
        )
        assert result.succeeded
        assert result.fallback_used is True
        assert result.attempts >= 2

    async def test_all_models_fail_returns_empty(
        self, mock_redis: AsyncMock
    ):
        failing_a = make_mock_provider("anthropic", succeed=False)
        failing_o = make_mock_provider("openai", succeed=False)
        cache = SemanticCache(redis_client=mock_redis)
        orch = LLMOrchestrator(
            providers={
                ProviderName.ANTHROPIC: failing_a,
                ProviderName.OPENAI: failing_o,
            },
            cache=cache,
        )
        result = await orch.generate(
            task_type=TaskType.BLURB_AD_COPY.value,
            prompt="Write a blurb",
        )
        assert not result.succeeded
        assert result.metadata.get("error") == "all_models_failed"


# -------------------------------------------------------------------
# Caching integration
# -------------------------------------------------------------------

@pytest.mark.asyncio
class TestCachingIntegration:
    """Test that caching correctly stores and retrieves responses."""

    async def test_second_call_is_cache_hit(
        self, orchestrator: LLMOrchestrator, mock_anthropic: BaseLLMProvider
    ):
        # Market analysis has caching enabled (TTL=24h)
        prompt = "Analyze the thriller genre"
        r1 = await orchestrator.generate(
            task_type=TaskType.MARKET_ANALYSIS.value,
            prompt=prompt,
        )
        assert r1.succeeded
        assert r1.cache_hit is False

        r2 = await orchestrator.generate(
            task_type=TaskType.MARKET_ANALYSIS.value,
            prompt=prompt,
        )
        assert r2.succeeded
        assert r2.cache_hit is True
        assert r2.cost_usd == 0.0  # cached response is free

    async def test_no_caching_for_long_form_writing(
        self, orchestrator: LLMOrchestrator, mock_anthropic: BaseLLMProvider
    ):
        prompt = "Write a chapter"
        r1 = await orchestrator.generate(
            task_type=TaskType.LONG_FORM_WRITING.value,
            prompt=prompt,
        )
        assert r1.cache_hit is False

        r2 = await orchestrator.generate(
            task_type=TaskType.LONG_FORM_WRITING.value,
            prompt=prompt,
        )
        assert r2.cache_hit is False

    async def test_skip_cache_flag(
        self, orchestrator: LLMOrchestrator, mock_anthropic: BaseLLMProvider
    ):
        prompt = "Analyze market"
        await orchestrator.generate(
            task_type=TaskType.MARKET_ANALYSIS.value,
            prompt=prompt,
        )
        r2 = await orchestrator.generate(
            task_type=TaskType.MARKET_ANALYSIS.value,
            prompt=prompt,
            options=GenerationOptions(skip_cache=True),
        )
        assert r2.cache_hit is False


# -------------------------------------------------------------------
# Cost tracking integration
# -------------------------------------------------------------------

@pytest.mark.asyncio
class TestCostTrackingIntegration:
    """Test cost tracking through the orchestrator."""

    async def test_cost_recorded_for_org(self, orchestrator: LLMOrchestrator):
        org_id = "org-cost-test"
        opts = GenerationOptions(org_id=org_id)
        await orchestrator.generate(
            task_type=TaskType.REVIEW_SENTIMENT.value,
            prompt="Analyze these reviews",
            options=opts,
        )
        summary = orchestrator._cost_tracker.get_usage_summary(org_id)
        assert summary["request_count"] == 1
        assert summary["total_cost_usd"] > 0

    async def test_budget_exceeded_blocks_generation(
        self, orchestrator: LLMOrchestrator
    ):
        org_id = "org-broke"
        orchestrator._cost_tracker.set_budget(org_id, 0.0001)
        # Spend past budget
        await orchestrator._cost_tracker.record_usage(
            org_id, ModelID.CLAUDE_OPUS.value, "test", 10000, 10000
        )
        opts = GenerationOptions(org_id=org_id)
        result = await orchestrator.generate(
            task_type=TaskType.BLURB_AD_COPY.value,
            prompt="Should be blocked",
            options=opts,
        )
        assert not result.succeeded
        assert result.metadata.get("error") == "monthly_budget_exceeded"


# -------------------------------------------------------------------
# Quality assurance integration
# -------------------------------------------------------------------

@pytest.mark.asyncio
class TestQualityIntegration:
    """Test quality checks within the orchestration flow."""

    async def test_quality_report_attached(self, orchestrator: LLMOrchestrator):
        result = await orchestrator.generate(
            task_type=TaskType.BLURB_AD_COPY.value,
            prompt="Write a blurb",
        )
        assert result.quality_report is not None
        assert result.quality_report.word_count > 0

    async def test_skip_quality_check(self, orchestrator: LLMOrchestrator):
        opts = GenerationOptions(skip_quality_check=True)
        result = await orchestrator.generate(
            task_type=TaskType.BLURB_AD_COPY.value,
            prompt="Write a blurb",
            options=opts,
        )
        assert result.quality_report is None

    async def test_progressive_enhancement_escalates(
        self, mock_redis: AsyncMock
    ):
        """If Haiku returns low-quality content, orchestrator escalates to Sonnet."""
        # Haiku returns very short (low quality) content
        poor_anthropic = AsyncMock(spec=BaseLLMProvider)
        poor_anthropic.provider_name = "anthropic"

        call_count = 0

        async def _generate(request: LLMRequest) -> LLMResponse:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call (Haiku) — poor quality
                return LLMResponse(
                    model_id=request.model_id,
                    content="OK",  # too short
                    input_tokens=10,
                    output_tokens=2,
                    total_tokens=12,
                    latency_ms=10.0,
                    finish_reason="end_turn",
                )
            else:
                # Second call (Sonnet) — good quality
                return LLMResponse(
                    model_id=request.model_id,
                    content=(
                        "The sentiment analysis reveals predominantly positive reviews "
                        "with strong themes of character development and plot pacing. "
                        "Readers consistently praise the atmospheric setting and the "
                        "author's ability to create tension throughout the narrative."
                    ),
                    input_tokens=50,
                    output_tokens=100,
                    total_tokens=150,
                    latency_ms=80.0,
                    finish_reason="end_turn",
                )

        poor_anthropic.generate = AsyncMock(side_effect=_generate)

        cache = SemanticCache(redis_client=mock_redis)
        orch = LLMOrchestrator(
            providers={ProviderName.ANTHROPIC: poor_anthropic},
            cache=cache,
            cost_tracker=CostTracker(),
            quality=QualityAssurance(enhancement_threshold=96.0),
        )

        # Review sentiment: Haiku -> Sonnet
        # "OK" scores ~95 (short content penalty) which is below threshold=96
        # so it should escalate to Sonnet
        result = await orch.generate(
            task_type=TaskType.REVIEW_SENTIMENT.value,
            prompt="Analyze these reviews",
        )
        assert result.succeeded
        assert call_count == 2  # escalated from Haiku to Sonnet


# -------------------------------------------------------------------
# Streaming
# -------------------------------------------------------------------

@pytest.mark.asyncio
class TestStreamingGeneration:
    """Test streaming generation through the orchestrator."""

    async def test_stream_yields_chunks(self, orchestrator: LLMOrchestrator):
        chunks = []
        async for chunk in orchestrator.generate_stream(
            task_type=TaskType.BLURB_AD_COPY.value,
            prompt="Write a blurb",
        ):
            chunks.append(chunk)
        assert len(chunks) > 0
        content = "".join(c.delta for c in chunks)
        assert len(content) > 0

    async def test_stream_fallback_on_failure(
        self, orchestrator_with_failing_primary: LLMOrchestrator
    ):
        chunks = []
        async for chunk in orchestrator_with_failing_primary.generate_stream(
            task_type=TaskType.BLURB_AD_COPY.value,
            prompt="Write a blurb",
        ):
            chunks.append(chunk)
        content = "".join(c.delta for c in chunks)
        assert len(content) > 0

    async def test_stream_budget_exceeded(self, orchestrator: LLMOrchestrator):
        org_id = "org-stream-broke"
        orchestrator._cost_tracker.set_budget(org_id, 0.0001)
        await orchestrator._cost_tracker.record_usage(
            org_id, ModelID.CLAUDE_OPUS.value, "test", 10000, 10000
        )
        opts = GenerationOptions(org_id=org_id)
        chunks = []
        async for chunk in orchestrator.generate_stream(
            task_type=TaskType.BLURB_AD_COPY.value,
            prompt="Should be blocked",
            options=opts,
        ):
            chunks.append(chunk)
        assert any(c.finish_reason == "budget_exceeded" for c in chunks)


# -------------------------------------------------------------------
# Provider registration
# -------------------------------------------------------------------

@pytest.mark.asyncio
class TestProviderRegistration:
    """Test dynamic provider registration."""

    async def test_register_and_use_provider(self, mock_redis: AsyncMock):
        orch = LLMOrchestrator(
            cache=SemanticCache(redis_client=mock_redis),
        )
        mock_provider = make_mock_provider("anthropic")
        orch.register_provider(ProviderName.ANTHROPIC, mock_provider)

        result = await orch.generate(
            task_type=TaskType.STYLE_FINGERPRINTING.value,
            prompt="Analyze this style",
        )
        assert result.succeeded

    async def test_missing_provider_skipped(self, mock_redis: AsyncMock):
        orch = LLMOrchestrator(
            providers={},
            cache=SemanticCache(redis_client=mock_redis),
        )
        result = await orch.generate(
            task_type=TaskType.BLURB_AD_COPY.value,
            prompt="Write a blurb",
        )
        assert not result.succeeded
        assert result.metadata.get("error") == "all_models_failed"
