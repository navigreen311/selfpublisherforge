# VF11: Provider Router Service

## Task
Create the intelligent provider routing service for TTS/ASR request routing with health monitoring and cost tracking.

## Files to Create

### `backend/app/services/voiceforge/provider_router.py`

```python
"""
Intelligent Provider Router

Routes TTS and ASR requests to the optimal provider based on:
- User's plan tier (free → self-hosted only, pro → choose, enterprise → all)
- Request type (preview → fastest, production → highest quality)
- Cost budget remaining for the org
- Provider availability (health checks, rate limits)
- Voice compatibility (cloned voices locked to their provider)

Provider health monitoring:
- Periodic health checks every 60 seconds
- Automatic failover: if primary is down, route to fallback
- Circuit breaker: 3 failures in 5 minutes → open for 60 seconds

Cost tracking:
- Per-org running cost counter in Redis (reset monthly)
- Alert at 50%, 75%, 90%, 100% of budget
- Hard stop at 100% unless override
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

class RequestType(str, Enum):
    PREVIEW = "preview"
    DRAFT = "draft"
    PRODUCTION = "production"
    CLONE = "clone"

class ProviderHealth(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"

@dataclass
class ProviderSelection:
    provider: str
    reason: str
    estimated_cost: float
    fallback: str | None = None

@dataclass
class CostUsage:
    org_id: str
    current_month_cost: float
    budget_limit: float
    percent_used: float
    alert_level: str | None = None  # "50%", "75%", "90%", "100%"

@dataclass
class CircuitBreaker:
    failures: int = 0
    last_failure: float = 0.0
    open_until: float = 0.0

    @property
    def is_open(self) -> bool:
        return time.time() < self.open_until

    def record_failure(self):
        self.failures += 1
        self.last_failure = time.time()
        if self.failures >= 3:
            self.open_until = time.time() + 60  # open for 60s
            logger.warning("Circuit breaker opened")

    def record_success(self):
        self.failures = 0
        self.open_until = 0.0

class ProviderRouter:
    TTS_PROVIDERS = ["coqui_xtts", "elevenlabs", "piper"]
    ASR_PROVIDERS = ["faster_whisper", "deepgram"]

    # Tier access mapping
    TIER_ACCESS = {
        "free": ["piper", "coqui_xtts"],
        "starter": ["piper", "coqui_xtts"],
        "pro": ["piper", "coqui_xtts", "elevenlabs"],
        "business": ["piper", "coqui_xtts", "elevenlabs"],
        "enterprise": ["piper", "coqui_xtts", "elevenlabs"],
    }

    def __init__(self):
        self.settings = get_settings()
        self._health: dict[str, ProviderHealth] = {}
        self._circuits: dict[str, CircuitBreaker] = {p: CircuitBreaker() for p in self.TTS_PROVIDERS + self.ASR_PROVIDERS}
        self._http = httpx.AsyncClient(timeout=10.0)
        self._last_health_check = 0.0

    async def route_tts(self, text: str, voice_config: dict, org_id: str, request_type: RequestType, tier: str = "pro") -> ProviderSelection:
        """Select optimal TTS provider."""
        await self._maybe_health_check()

        # If voice is locked to a provider (cloned voice), use that
        if voice_config.get("provider"):
            provider = voice_config["provider"]
            if self._is_available(provider):
                return ProviderSelection(provider=provider, reason="voice locked to provider", estimated_cost=self._estimate(text, provider))

        # Get tier-accessible providers
        accessible = self.TIER_ACCESS.get(tier, self.TIER_ACCESS["free"])
        available = [p for p in accessible if self._is_available(p)]

        if not available:
            raise RuntimeError("No TTS providers available")

        # Route by request type
        if request_type == RequestType.PREVIEW:
            provider = "piper" if "piper" in available else available[0]
        elif request_type == RequestType.PRODUCTION:
            provider = "elevenlabs" if "elevenlabs" in available else "coqui_xtts" if "coqui_xtts" in available else available[0]
        elif request_type == RequestType.CLONE:
            provider = "elevenlabs" if "elevenlabs" in available else "coqui_xtts"
        else:  # DRAFT
            provider = "coqui_xtts" if "coqui_xtts" in available else available[0]

        fallback = next((p for p in available if p != provider), None)
        return ProviderSelection(
            provider=provider,
            reason=f"{request_type.value} request, tier={tier}",
            estimated_cost=self._estimate(text, provider),
            fallback=fallback,
        )

    async def route_asr(self, audio_config: dict, org_id: str) -> ProviderSelection:
        """Select ASR provider."""
        if self._is_available("faster_whisper"):
            return ProviderSelection(provider="faster_whisper", reason="primary ASR", estimated_cost=0.0, fallback="deepgram")
        if self._is_available("deepgram"):
            return ProviderSelection(provider="deepgram", reason="fallback ASR", estimated_cost=0.005)
        raise RuntimeError("No ASR providers available")

    async def check_provider_health(self, provider: str) -> ProviderHealth:
        """Health check a single provider."""
        endpoints = {
            "coqui_xtts": f"{self.settings.COQUI_XTTS_ENDPOINT}/health",
            "piper": f"{self.settings.PIPER_ENDPOINT}/health",
            "faster_whisper": f"{self.settings.FASTER_WHISPER_ENDPOINT}/health",
            "elevenlabs": "https://api.elevenlabs.io/v1/voices",
            "deepgram": "https://api.deepgram.com/v1/projects",
        }
        try:
            url = endpoints.get(provider)
            if not url:
                return ProviderHealth.DOWN
            headers = {}
            if provider == "elevenlabs" and self.settings.ELEVENLABS_API_KEY:
                headers["xi-api-key"] = self.settings.ELEVENLABS_API_KEY
            if provider == "deepgram" and self.settings.DEEPGRAM_API_KEY:
                headers["Authorization"] = f"Token {self.settings.DEEPGRAM_API_KEY}"
            resp = await self._http.get(url, headers=headers)
            return ProviderHealth.HEALTHY if resp.status_code < 400 else ProviderHealth.DEGRADED
        except Exception:
            return ProviderHealth.DOWN

    async def get_cost_usage(self, org_id: str) -> CostUsage:
        """Get current month cost usage for an org from Redis."""
        # Import Redis client lazily
        import redis.asyncio as aioredis
        r = aioredis.from_url(self.settings.REDIS_URL)
        key = f"voiceforge:cost:{org_id}:{time.strftime('%Y-%m')}"
        cost = float(await r.get(key) or 0)
        budget = 100.0  # default budget, should come from org settings
        percent = (cost / budget * 100) if budget > 0 else 0
        alert = None
        if percent >= 100: alert = "100%"
        elif percent >= 90: alert = "90%"
        elif percent >= 75: alert = "75%"
        elif percent >= 50: alert = "50%"
        await r.aclose()
        return CostUsage(org_id=org_id, current_month_cost=cost, budget_limit=budget, percent_used=percent, alert_level=alert)

    async def update_cost(self, org_id: str, cost_usd: float, provider: str, request_type: str) -> None:
        """Record cost in Redis."""
        import redis.asyncio as aioredis
        r = aioredis.from_url(self.settings.REDIS_URL)
        key = f"voiceforge:cost:{org_id}:{time.strftime('%Y-%m')}"
        await r.incrbyfloat(key, cost_usd)
        await r.expire(key, 60 * 60 * 24 * 35)  # expire after 35 days
        await r.aclose()

    async def get_provider_status(self) -> dict[str, str]:
        """Get health status of all providers."""
        await self._maybe_health_check()
        return {p: h.value for p, h in self._health.items()}

    def _is_available(self, provider: str) -> bool:
        circuit = self._circuits.get(provider)
        if circuit and circuit.is_open:
            return False
        return self._health.get(provider, ProviderHealth.DOWN) != ProviderHealth.DOWN

    def _estimate(self, text: str, provider: str) -> float:
        words = len(text.split())
        minutes = words / 150
        rates = {"coqui_xtts": 0.001, "piper": 0.0001, "elevenlabs": 0.03}
        return minutes * rates.get(provider, 0.01)

    async def _maybe_health_check(self):
        if time.time() - self._last_health_check < 60:
            return
        for provider in self.TTS_PROVIDERS + self.ASR_PROVIDERS:
            self._health[provider] = await self.check_provider_health(provider)
        self._last_health_check = time.time()

    async def close(self):
        await self._http.aclose()
```

## Conventions
- Use Redis for cost tracking (already available in project)
- Circuit breaker pattern for resilience
- Health checks are cached for 60 seconds
