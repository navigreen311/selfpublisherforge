"""
Unit tests for model routing configuration and logic.

Tests the task-to-model mapping, fallback chains, provider resolution,
max token limits, and cache TTL configuration.
"""

import pytest

from app.modules.llm_orchestration.router_config import (
    MODEL_PROVIDER_MAP,
    ROUTING_TABLE,
    ModelID,
    ModelRoute,
    ModelRouter,
    ProviderName,
    TaskType,
)

# -------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------

@pytest.fixture
def router() -> ModelRouter:
    return ModelRouter()


@pytest.fixture
def custom_router() -> ModelRouter:
    custom_table = {
        TaskType.LONG_FORM_WRITING: ModelRoute(
            primary=ModelID.CLAUDE_SONNET,
            fallbacks=[ModelID.GPT_4],
            max_tokens=2048,
        ),
    }
    return ModelRouter(routing_table=custom_table)


# -------------------------------------------------------------------
# Task type routing
# -------------------------------------------------------------------

class TestTaskTypeRouting:
    """Verify that each task type maps to the correct primary model."""

    def test_long_form_writing_routes_to_opus(self, router: ModelRouter):
        assert router.get_primary_model(TaskType.LONG_FORM_WRITING) == ModelID.CLAUDE_OPUS

    def test_blurb_ad_copy_routes_to_sonnet(self, router: ModelRouter):
        assert router.get_primary_model(TaskType.BLURB_AD_COPY) == ModelID.CLAUDE_SONNET

    def test_market_analysis_routes_to_sonnet(self, router: ModelRouter):
        assert router.get_primary_model(TaskType.MARKET_ANALYSIS) == ModelID.CLAUDE_SONNET

    def test_style_fingerprinting_routes_to_opus(self, router: ModelRouter):
        assert router.get_primary_model(TaskType.STYLE_FINGERPRINTING) == ModelID.CLAUDE_OPUS

    def test_review_sentiment_routes_to_haiku(self, router: ModelRouter):
        assert router.get_primary_model(TaskType.REVIEW_SENTIMENT) == ModelID.CLAUDE_HAIKU

    def test_quick_edits_routes_to_haiku(self, router: ModelRouter):
        assert router.get_primary_model(TaskType.QUICK_EDITS_GRAMMAR) == ModelID.CLAUDE_HAIKU


# -------------------------------------------------------------------
# Fallback chains
# -------------------------------------------------------------------

class TestFallbackChains:
    """Verify fallback model chains for each task type."""

    def test_long_form_falls_back_to_sonnet(self, router: ModelRouter):
        fallbacks = router.get_fallback_chain(TaskType.LONG_FORM_WRITING)
        assert fallbacks == [ModelID.CLAUDE_SONNET]

    def test_blurb_falls_back_to_gpt4(self, router: ModelRouter):
        fallbacks = router.get_fallback_chain(TaskType.BLURB_AD_COPY)
        assert fallbacks == [ModelID.GPT_4]

    def test_market_analysis_falls_back_to_gpt4(self, router: ModelRouter):
        fallbacks = router.get_fallback_chain(TaskType.MARKET_ANALYSIS)
        assert fallbacks == [ModelID.GPT_4]

    def test_style_fingerprinting_has_no_fallback(self, router: ModelRouter):
        fallbacks = router.get_fallback_chain(TaskType.STYLE_FINGERPRINTING)
        assert fallbacks == []

    def test_review_sentiment_falls_back_to_sonnet(self, router: ModelRouter):
        fallbacks = router.get_fallback_chain(TaskType.REVIEW_SENTIMENT)
        assert fallbacks == [ModelID.CLAUDE_SONNET]

    def test_quick_edits_falls_back_to_gpt4_mini(self, router: ModelRouter):
        fallbacks = router.get_fallback_chain(TaskType.QUICK_EDITS_GRAMMAR)
        assert fallbacks == [ModelID.GPT_4_MINI]

    def test_full_chain_includes_primary_and_fallbacks(self, router: ModelRouter):
        chain = router.get_full_chain(TaskType.LONG_FORM_WRITING)
        assert chain == [ModelID.CLAUDE_OPUS, ModelID.CLAUDE_SONNET]

    def test_full_chain_single_model_when_no_fallback(self, router: ModelRouter):
        chain = router.get_full_chain(TaskType.STYLE_FINGERPRINTING)
        assert chain == [ModelID.CLAUDE_OPUS]


# -------------------------------------------------------------------
# Provider resolution
# -------------------------------------------------------------------

class TestProviderResolution:
    """Verify model-to-provider mapping."""

    def test_claude_models_map_to_anthropic(self, router: ModelRouter):
        assert router.get_provider(ModelID.CLAUDE_OPUS) == ProviderName.ANTHROPIC
        assert router.get_provider(ModelID.CLAUDE_SONNET) == ProviderName.ANTHROPIC
        assert router.get_provider(ModelID.CLAUDE_HAIKU) == ProviderName.ANTHROPIC

    def test_gpt_models_map_to_openai(self, router: ModelRouter):
        assert router.get_provider(ModelID.GPT_4) == ProviderName.OPENAI
        assert router.get_provider(ModelID.GPT_4_MINI) == ProviderName.OPENAI

    def test_all_models_have_providers(self):
        for model_id in ModelID:
            assert model_id in MODEL_PROVIDER_MAP


# -------------------------------------------------------------------
# Max tokens & cache TTLs
# -------------------------------------------------------------------

class TestMaxTokensAndTTL:
    """Verify task-specific max_tokens and cache TTL settings."""

    def test_long_form_has_high_max_tokens(self, router: ModelRouter):
        assert router.get_max_tokens(TaskType.LONG_FORM_WRITING) == 8192

    def test_review_sentiment_has_low_max_tokens(self, router: ModelRouter):
        assert router.get_max_tokens(TaskType.REVIEW_SENTIMENT) == 1024

    def test_long_form_has_no_caching(self, router: ModelRouter):
        assert router.get_cache_ttl(TaskType.LONG_FORM_WRITING) == 0

    def test_market_analysis_has_24h_cache(self, router: ModelRouter):
        assert router.get_cache_ttl(TaskType.MARKET_ANALYSIS) == 86400

    def test_style_fingerprinting_has_7d_cache(self, router: ModelRouter):
        assert router.get_cache_ttl(TaskType.STYLE_FINGERPRINTING) == 604800

    def test_quick_edits_has_no_caching(self, router: ModelRouter):
        assert router.get_cache_ttl(TaskType.QUICK_EDITS_GRAMMAR) == 0


# -------------------------------------------------------------------
# Custom routing tables
# -------------------------------------------------------------------

class TestCustomRouting:
    """Verify custom routing table overrides."""

    def test_custom_primary_model(self, custom_router: ModelRouter):
        assert custom_router.get_primary_model(TaskType.LONG_FORM_WRITING) == ModelID.CLAUDE_SONNET

    def test_custom_fallback(self, custom_router: ModelRouter):
        assert custom_router.get_fallback_chain(TaskType.LONG_FORM_WRITING) == [ModelID.GPT_4]

    def test_custom_max_tokens(self, custom_router: ModelRouter):
        assert custom_router.get_max_tokens(TaskType.LONG_FORM_WRITING) == 2048

    def test_unknown_task_type_raises(self, custom_router: ModelRouter):
        with pytest.raises(ValueError, match="Unknown task type"):
            custom_router.get_route(TaskType.MARKET_ANALYSIS)


# -------------------------------------------------------------------
# Routing table completeness
# -------------------------------------------------------------------

class TestRoutingTableCompleteness:
    """Ensure the default routing table covers all task types."""

    def test_all_task_types_have_routes(self):
        for task_type in TaskType:
            assert task_type in ROUTING_TABLE, f"Missing route for {task_type}"

    def test_all_routes_have_valid_primary(self):
        for task_type, route in ROUTING_TABLE.items():
            assert route.primary in ModelID, f"Invalid primary for {task_type}"

    def test_all_fallbacks_are_valid_models(self):
        for task_type, route in ROUTING_TABLE.items():
            for fb in route.fallbacks:
                assert fb in ModelID, f"Invalid fallback {fb} for {task_type}"

    def test_max_tokens_are_positive(self):
        for task_type, route in ROUTING_TABLE.items():
            assert route.max_tokens > 0, f"Invalid max_tokens for {task_type}"

    def test_cache_ttl_non_negative(self):
        for task_type, route in ROUTING_TABLE.items():
            assert route.cache_ttl_seconds >= 0, f"Negative TTL for {task_type}"
