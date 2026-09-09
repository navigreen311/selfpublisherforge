"""
Semantic Caching Layer

Hashes prompts and stores LLM responses with task-specific TTLs.
Primary storage is Redis; falls back to an in-memory LRU dict when
Redis is unavailable so that LLM calls are never blocked by cache failures.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import OrderedDict

import redis.asyncio as aioredis

from app.config import get_settings
from app.modules.llm_orchestration.router_config import TaskType

logger = logging.getLogger(__name__)

# Default TTLs per task type (seconds) — mirrors router_config but can be
# overridden independently for cache-only tuning.
DEFAULT_CACHE_TTLS: dict[TaskType, int] = {
    TaskType.LONG_FORM_WRITING: 0,  # no caching — creative work
    TaskType.BLURB_AD_COPY: 86_400,  # 24 hours
    TaskType.MARKET_ANALYSIS: 86_400,  # 24 hours
    TaskType.STYLE_FINGERPRINTING: 604_800,  # 7 days
    TaskType.REVIEW_SENTIMENT: 86_400,  # 24 hours
    TaskType.QUICK_EDITS_GRAMMAR: 0,  # no caching — unique input
}

CACHE_KEY_PREFIX = "llm_cache:"

# In-memory fallback settings
_DEFAULT_MEMORY_MAX_ENTRIES = 256


class _MemoryCache:
    """Simple in-memory LRU cache with per-entry TTL, used as fallback."""

    def __init__(self, max_entries: int = _DEFAULT_MEMORY_MAX_ENTRIES) -> None:
        self._store: OrderedDict[str, tuple[float, dict]] = OrderedDict()
        self._max_entries = max_entries

    def get(self, key: str) -> dict | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, data = entry
        if expires_at and time.monotonic() > expires_at:
            self._store.pop(key, None)
            return None
        # Move to end (most recently used)
        self._store.move_to_end(key)
        return data

    def set(self, key: str, data: dict, ttl: int) -> None:
        expires_at = time.monotonic() + ttl if ttl > 0 else 0.0
        self._store[key] = (expires_at, data)
        self._store.move_to_end(key)
        # Evict oldest if over capacity
        while len(self._store) > self._max_entries:
            self._store.popitem(last=False)

    def delete(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    def clear(self) -> int:
        count = len(self._store)
        self._store.clear()
        return count


class SemanticCache:
    """Redis-backed semantic cache for LLM responses with in-memory fallback."""

    def __init__(
        self,
        redis_client: aioredis.Redis | None = None,
        ttl_overrides: dict[TaskType, int] | None = None,
        memory_max_entries: int = _DEFAULT_MEMORY_MAX_ENTRIES,
    ) -> None:
        self._redis = redis_client
        self._ttls = {**DEFAULT_CACHE_TTLS, **(ttl_overrides or {})}
        self._memory = _MemoryCache(max_entries=memory_max_entries)
        self._redis_available: bool = True  # optimistic; flipped on first failure

    async def _get_redis(self) -> aioredis.Redis | None:
        """Lazily initialize the Redis connection. Returns None if unavailable."""
        if self._redis is None:
            try:
                settings = get_settings()
                self._redis = aioredis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                )
                # Verify connectivity
                await self._redis.ping()
                self._redis_available = True
            except (aioredis.RedisError, ConnectionError, OSError):
                logger.warning(
                    "Redis connection unavailable — falling back to in-memory cache",
                    exc_info=True,
                )
                self._redis_available = False
                return None
        return self._redis

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_cache_key(
        self,
        task_type: TaskType,
        prompt: str,
        model_id: str,
        system_prompt: str | None = None,
    ) -> str:
        """Deterministic cache key from prompt content and model.

        Key format: ``llm_cache:<task_type>:<sha256hex>`` so that
        ``flush_task_type`` can target keys by task type via scan pattern.
        """
        raw = json.dumps(
            {
                "task_type": task_type.value,
                "model_id": model_id,
                "prompt": prompt.strip(),
                "system_prompt": (system_prompt or "").strip(),
            },
            sort_keys=True,
        )
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return f"{CACHE_KEY_PREFIX}{task_type.value}:{digest}"

    def get_ttl(self, task_type: TaskType) -> int:
        """Return TTL in seconds for a task type (0 = no caching)."""
        return self._ttls.get(task_type, 0)

    async def get(
        self,
        task_type: TaskType,
        prompt: str,
        model_id: str,
        system_prompt: str | None = None,
    ) -> dict | None:
        """Look up a cached response. Returns None on miss or if caching disabled."""
        ttl = self.get_ttl(task_type)
        if ttl <= 0:
            return None

        key = self.build_cache_key(task_type, prompt, model_id, system_prompt)

        # Try Redis first
        try:
            client = await self._get_redis()
            if client is not None:
                raw = await client.get(key)
                if raw is not None:
                    logger.debug("Cache HIT (Redis) for key %s", key)
                    data = json.loads(raw)
                    # Populate memory cache for faster subsequent hits
                    self._memory.set(key, data, ttl)
                    return data
                logger.debug("Cache MISS (Redis) for key %s", key)
        except (ConnectionError, aioredis.RedisError, OSError):
            logger.warning(
                "Redis read failed for key %s — trying in-memory fallback",
                key,
                exc_info=True,
            )
            self._redis_available = False

        # Fallback to in-memory
        mem_result = self._memory.get(key)
        if mem_result is not None:
            logger.debug("Cache HIT (memory) for key %s", key)
            return mem_result

        logger.debug("Cache MISS (all layers) for key %s", key)
        return None

    async def set(
        self,
        task_type: TaskType,
        prompt: str,
        model_id: str,
        response_data: dict,
        system_prompt: str | None = None,
    ) -> bool:
        """Store a response in the cache. Returns True on success."""
        ttl = self.get_ttl(task_type)
        if ttl <= 0:
            return False

        key = self.build_cache_key(task_type, prompt, model_id, system_prompt)

        # Always write to in-memory cache
        self._memory.set(key, response_data, ttl)

        # Try Redis
        try:
            client = await self._get_redis()
            if client is not None:
                await client.set(key, json.dumps(response_data), ex=ttl)
                logger.debug("Cache SET (Redis) for key %s (TTL=%ds)", key, ttl)
                return True
        except (ConnectionError, aioredis.RedisError, OSError):
            logger.warning(
                "Redis write failed for key %s — stored in memory only",
                key,
                exc_info=True,
            )
            self._redis_available = False
        except (ValueError, TypeError):
            logger.warning(
                "Cache serialization failed for key %s",
                key,
                exc_info=True,
            )
            return False

        # Stored in memory even if Redis failed
        logger.debug("Cache SET (memory only) for key %s (TTL=%ds)", key, ttl)
        return True

    async def invalidate(
        self,
        task_type: TaskType,
        prompt: str,
        model_id: str,
        system_prompt: str | None = None,
    ) -> bool:
        """Remove a specific entry from the cache."""
        key = self.build_cache_key(task_type, prompt, model_id, system_prompt)
        removed = self._memory.delete(key)

        try:
            client = await self._get_redis()
            if client is not None:
                deleted = await client.delete(key)
                return deleted > 0 or removed
        except (ConnectionError, aioredis.RedisError, OSError):
            logger.warning(
                "Redis invalidation failed for key %s",
                key,
                exc_info=True,
            )
            self._redis_available = False

        return removed

    async def flush_task_type(self, task_type: TaskType) -> int:
        """Delete all cached entries for a given task type. Returns count deleted."""
        # Note: in-memory cache doesn't track task types separately,
        # so we clear all of memory to be safe.
        mem_count = self._memory.clear()

        pattern = f"{CACHE_KEY_PREFIX}{task_type.value}:*"
        try:
            client = await self._get_redis()
            if client is not None:
                redis_count = 0
                async for key in client.scan_iter(match=pattern, count=100):
                    await client.delete(key)
                    redis_count += 1
                return redis_count
        except (ConnectionError, aioredis.RedisError, OSError):
            logger.warning(
                "Redis flush failed for task type %s",
                task_type.value,
                exc_info=True,
            )
            self._redis_available = False

        return mem_count

    async def clear(self) -> int:
        """Flush the entire LLM cache (Redis + in-memory). Returns count deleted."""
        mem_count = self._memory.clear()

        pattern = f"{CACHE_KEY_PREFIX}*"
        try:
            client = await self._get_redis()
            if client is not None:
                redis_count = 0
                async for key in client.scan_iter(match=pattern, count=200):
                    await client.delete(key)
                    redis_count += 1
                logger.info(
                    "Cache cleared: %d Redis keys + %d memory entries",
                    redis_count,
                    mem_count,
                )
                return redis_count + mem_count
        except (ConnectionError, aioredis.RedisError, OSError):
            logger.warning(
                "Redis clear failed — only in-memory cache was flushed",
                exc_info=True,
            )
            self._redis_available = False

        logger.info("Cache cleared: %d memory entries (Redis unavailable)", mem_count)
        return mem_count
