"""
Unit tests for the semantic caching layer.

Tests cache key generation, hit/miss behaviour, TTL configuration,
and task-type-specific caching rules.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.llm_orchestration.cache import (
    CACHE_KEY_PREFIX,
    DEFAULT_CACHE_TTLS,
    SemanticCache,
)
from app.modules.llm_orchestration.router_config import TaskType

# -------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------


@pytest.fixture
def mock_redis() -> AsyncMock:
    """In-memory mock of an async Redis client."""
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

    async def _scan_iter(match=None, count=None):
        import fnmatch

        for key in list(redis._store.keys()):
            if match is None or fnmatch.fnmatch(key, match):
                yield key

    redis.get = AsyncMock(side_effect=_get)
    redis.set = AsyncMock(side_effect=_set)
    redis.delete = AsyncMock(side_effect=_delete)
    redis.scan_iter = MagicMock(side_effect=_scan_iter)

    return redis


@pytest.fixture
def cache(mock_redis: AsyncMock) -> SemanticCache:
    return SemanticCache(redis_client=mock_redis)


# -------------------------------------------------------------------
# Cache key generation
# -------------------------------------------------------------------


class TestCacheKeyGeneration:
    """Verify deterministic, collision-resistant cache keys."""

    def test_key_starts_with_prefix(self, cache: SemanticCache):
        key = cache.build_cache_key(TaskType.MARKET_ANALYSIS, "test prompt", "claude-sonnet")
        assert key.startswith(CACHE_KEY_PREFIX)

    def test_key_embeds_task_type(self, cache: SemanticCache):
        key = cache.build_cache_key(TaskType.MARKET_ANALYSIS, "test prompt", "claude-sonnet")
        # Key format: "llm_cache:<task_type>:<64-char hex digest>"
        assert key.startswith(CACHE_KEY_PREFIX)
        remainder = key[len(CACHE_KEY_PREFIX) :]
        task_segment, hex_part = remainder.split(":", 1)
        assert task_segment == TaskType.MARKET_ANALYSIS.value
        assert len(hex_part) == 64
        assert all(c in "0123456789abcdef" for c in hex_part)

    def test_same_inputs_same_key(self, cache: SemanticCache):
        key1 = cache.build_cache_key(TaskType.BLURB_AD_COPY, "hello", "model-a")
        key2 = cache.build_cache_key(TaskType.BLURB_AD_COPY, "hello", "model-a")
        assert key1 == key2

    def test_different_prompts_different_keys(self, cache: SemanticCache):
        key1 = cache.build_cache_key(TaskType.BLURB_AD_COPY, "hello", "model-a")
        key2 = cache.build_cache_key(TaskType.BLURB_AD_COPY, "world", "model-a")
        assert key1 != key2

    def test_different_models_different_keys(self, cache: SemanticCache):
        key1 = cache.build_cache_key(TaskType.BLURB_AD_COPY, "hello", "model-a")
        key2 = cache.build_cache_key(TaskType.BLURB_AD_COPY, "hello", "model-b")
        assert key1 != key2

    def test_different_task_types_different_keys(self, cache: SemanticCache):
        key1 = cache.build_cache_key(TaskType.BLURB_AD_COPY, "hello", "model-a")
        key2 = cache.build_cache_key(TaskType.MARKET_ANALYSIS, "hello", "model-a")
        assert key1 != key2

    def test_system_prompt_affects_key(self, cache: SemanticCache):
        key1 = cache.build_cache_key(TaskType.BLURB_AD_COPY, "hello", "model-a", system_prompt="sys1")
        key2 = cache.build_cache_key(TaskType.BLURB_AD_COPY, "hello", "model-a", system_prompt="sys2")
        assert key1 != key2

    def test_whitespace_normalization(self, cache: SemanticCache):
        key1 = cache.build_cache_key(TaskType.BLURB_AD_COPY, "  hello  ", "m")
        key2 = cache.build_cache_key(TaskType.BLURB_AD_COPY, "hello", "m")
        assert key1 == key2


# -------------------------------------------------------------------
# TTL configuration
# -------------------------------------------------------------------


class TestTTLConfiguration:
    """Verify task-type-specific TTL settings."""

    def test_long_form_writing_no_cache(self, cache: SemanticCache):
        assert cache.get_ttl(TaskType.LONG_FORM_WRITING) == 0

    def test_market_analysis_24h(self, cache: SemanticCache):
        assert cache.get_ttl(TaskType.MARKET_ANALYSIS) == 86400

    def test_style_fingerprinting_7d(self, cache: SemanticCache):
        assert cache.get_ttl(TaskType.STYLE_FINGERPRINTING) == 604800

    def test_quick_edits_no_cache(self, cache: SemanticCache):
        assert cache.get_ttl(TaskType.QUICK_EDITS_GRAMMAR) == 0

    def test_custom_ttl_override(self, mock_redis: AsyncMock):
        custom = SemanticCache(
            redis_client=mock_redis,
            ttl_overrides={TaskType.LONG_FORM_WRITING: 3600},
        )
        assert custom.get_ttl(TaskType.LONG_FORM_WRITING) == 3600

    def test_default_ttls_cover_all_task_types(self):
        for task_type in TaskType:
            assert task_type in DEFAULT_CACHE_TTLS


# -------------------------------------------------------------------
# Cache hit / miss
# -------------------------------------------------------------------


@pytest.mark.asyncio
class TestCacheHitMiss:
    """Test get/set operations on the cache."""

    async def test_miss_returns_none(self, cache: SemanticCache):
        result = await cache.get(TaskType.BLURB_AD_COPY, "nonexistent", "model-a")
        assert result is None

    async def test_set_then_get_returns_data(self, cache: SemanticCache, mock_redis: AsyncMock):
        data = {"content": "Hello world", "model_id": "model-a", "input_tokens": 10}
        await cache.set(TaskType.BLURB_AD_COPY, "test", "model-a", data)
        result = await cache.get(TaskType.BLURB_AD_COPY, "test", "model-a")
        assert result is not None
        assert result["content"] == "Hello world"

    async def test_no_cache_for_zero_ttl_task_get(self, cache: SemanticCache):
        # LONG_FORM_WRITING has TTL=0, so get should always return None
        result = await cache.get(TaskType.LONG_FORM_WRITING, "some prompt", "model-a")
        assert result is None

    async def test_no_cache_for_zero_ttl_task_set(self, cache: SemanticCache, mock_redis: AsyncMock):
        # set should return False and not write
        result = await cache.set(
            TaskType.LONG_FORM_WRITING,
            "prompt",
            "model-a",
            {"content": "data"},
        )
        assert result is False
        assert len(mock_redis._store) == 0

    async def test_set_stores_with_correct_ttl(self, cache: SemanticCache, mock_redis: AsyncMock):
        await cache.set(
            TaskType.MARKET_ANALYSIS,
            "prompt",
            "model-a",
            {"content": "analysis result"},
        )
        # Verify TTL was set to 86400 (24h)
        stored_ttls = mock_redis._ttls
        assert len(stored_ttls) == 1
        ttl = next(iter(stored_ttls.values()))
        assert ttl == 86400

    async def test_invalidate_removes_entry(self, cache: SemanticCache, mock_redis: AsyncMock):
        data = {"content": "to be deleted"}
        await cache.set(TaskType.BLURB_AD_COPY, "del-test", "model-a", data)
        assert len(mock_redis._store) == 1

        removed = await cache.invalidate(TaskType.BLURB_AD_COPY, "del-test", "model-a")
        assert removed is True

        result = await cache.get(TaskType.BLURB_AD_COPY, "del-test", "model-a")
        assert result is None

    async def test_invalidate_nonexistent_returns_false(self, cache: SemanticCache):
        removed = await cache.invalidate(TaskType.BLURB_AD_COPY, "never-stored", "model-a")
        assert removed is False


# -------------------------------------------------------------------
# Flush by task type
# -------------------------------------------------------------------


@pytest.mark.asyncio
class TestFlushByTaskType:
    """Test bulk cache invalidation."""

    async def test_flush_deletes_matching_keys(self, cache: SemanticCache, mock_redis: AsyncMock):
        await cache.set(TaskType.MARKET_ANALYSIS, "p1", "m", {"content": "a"})
        await cache.set(TaskType.MARKET_ANALYSIS, "p2", "m", {"content": "b"})
        await cache.set(TaskType.BLURB_AD_COPY, "p3", "m", {"content": "c"})
        assert len(mock_redis._store) == 3

        deleted = await cache.flush_task_type(TaskType.MARKET_ANALYSIS)
        assert deleted == 2

        # Blurb entry should still exist
        assert len(mock_redis._store) == 1
