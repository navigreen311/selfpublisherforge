"""
Semantic Caching Layer

Hashes prompts and stores LLM responses in Redis with task-specific TTLs.
Avoids redundant API calls for identical or near-identical prompts.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Optional

import redis.asyncio as aioredis

from app.config import get_settings
from app.modules.llm_orchestration.router_config import TaskType

logger = logging.getLogger(__name__)

# Default TTLs per task type (seconds) — mirrors router_config but can be
# overridden independently for cache-only tuning.
DEFAULT_CACHE_TTLS: dict[TaskType, int] = {
    TaskType.LONG_FORM_WRITING: 0,           # no caching — creative work
    TaskType.BLURB_AD_COPY: 86_400,          # 24 hours
    TaskType.MARKET_ANALYSIS: 86_400,        # 24 hours
    TaskType.STYLE_FINGERPRINTING: 604_800,  # 7 days
    TaskType.REVIEW_SENTIMENT: 86_400,       # 24 hours
    TaskType.QUICK_EDITS_GRAMMAR: 0,         # no caching — unique input
}

CACHE_KEY_PREFIX = "llm:cache:"


class SemanticCache:
    """Redis-backed semantic cache for LLM responses."""

    def __init__(
        self,
        redis_client: Optional[aioredis.Redis] = None,
        ttl_overrides: Optional[dict[TaskType, int]] = None,
    ) -> None:
        self._redis = redis_client
        self._ttls = {**DEFAULT_CACHE_TTLS, **(ttl_overrides or {})}

    async def _get_redis(self) -> aioredis.Redis:
        """Lazily initialize the Redis connection."""
        if self._redis is None:
            settings = get_settings()
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
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
        """Deterministic cache key from prompt content and model."""
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
    ) -> Optional[dict]:
        """Look up a cached response. Returns None on miss or if caching disabled."""
        ttl = self.get_ttl(task_type)
        if ttl <= 0:
            return None

        key = self.build_cache_key(task_type, prompt, model_id, system_prompt)
        try:
            client = await self._get_redis()
            raw = await client.get(key)
            if raw:
                logger.debug("Cache HIT for key %s", key)
                return json.loads(raw)
            logger.debug("Cache MISS for key %s", key)
            return None
        except (ConnectionError, aioredis.RedisError, OSError) as exc:
            logger.warning("Cache lookup failed for key %s: connection/redis error", key, exc_info=True)
            return None
        except (ValueError, json.JSONDecodeError) as exc:
            logger.warning("Cache lookup failed for key %s: corrupt cached data", key, exc_info=True)
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
        try:
            client = await self._get_redis()
            await client.set(key, json.dumps(response_data), ex=ttl)
            logger.debug("Cache SET for key %s (TTL=%ds)", key, ttl)
            return True
        except (ConnectionError, aioredis.RedisError, OSError) as exc:
            logger.warning("Cache write failed for key %s: connection/redis error", key, exc_info=True)
            return False
        except (ValueError, TypeError) as exc:
            logger.warning("Cache write failed for key %s: serialization error", key, exc_info=True)
            return False

    async def invalidate(
        self,
        task_type: TaskType,
        prompt: str,
        model_id: str,
        system_prompt: str | None = None,
    ) -> bool:
        """Remove a specific entry from the cache."""
        key = self.build_cache_key(task_type, prompt, model_id, system_prompt)
        try:
            client = await self._get_redis()
            deleted = await client.delete(key)
            return deleted > 0
        except (ConnectionError, aioredis.RedisError, OSError) as exc:
            logger.warning("Cache invalidation failed for key %s: connection/redis error", key, exc_info=True)
            return False

    async def flush_task_type(self, task_type: TaskType) -> int:
        """Delete all cached entries for a given task type. Returns count deleted."""
        pattern = f"{CACHE_KEY_PREFIX}{task_type.value}:*"
        try:
            client = await self._get_redis()
            count = 0
            async for key in client.scan_iter(match=pattern, count=100):
                await client.delete(key)
                count += 1
            return count
        except (ConnectionError, aioredis.RedisError, OSError) as exc:
            logger.warning("Cache flush failed for pattern %s: connection/redis error", pattern, exc_info=True)
            return 0
