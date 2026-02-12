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

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & data classes
# ---------------------------------------------------------------------------


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
    """Track provider failures; open the circuit after 3 failures within 5 min."""

    failures: int = 0
    last_failure: float = 0.0
    open_until: float = 0.0
    _window: float = 300.0  # 5 minutes

    @property
    def is_open(self) -> bool:
        return time.time() < self.open_until

    def record_failure(self) -> None:
        now = time.time()
        # Reset counter if outside the failure window
        if now - self.last_failure > self._window:
            self.failures = 0
        self.failures += 1
        self.last_failure = now
        if self.failures >= 3:
            self.open_until = now + 60  # open for 60s
            logger.warning("Circuit breaker opened (failures=%d)", self.failures)

    def record_success(self) -> None:
        self.failures = 0
        self.open_until = 0.0


# ---------------------------------------------------------------------------
# Provider Router
# ---------------------------------------------------------------------------


class ProviderRouter:
    """Select the best TTS/ASR provider per request context."""

    TTS_PROVIDERS: ClassVar[list[str]] = ["coqui_xtts", "elevenlabs", "piper"]
    ASR_PROVIDERS: ClassVar[list[str]] = ["faster_whisper", "deepgram"]

    # Tier -> allowed providers
    TIER_ACCESS: ClassVar[dict[str, list[str]]] = {
        "free": ["piper", "coqui_xtts"],
        "starter": ["piper", "coqui_xtts"],
        "pro": ["piper", "coqui_xtts", "elevenlabs"],
        "business": ["piper", "coqui_xtts", "elevenlabs"],
        "enterprise": ["piper", "coqui_xtts", "elevenlabs"],
    }

    # Estimated cost per minute of generated audio (USD)
    _COST_PER_MINUTE: ClassVar[dict[str, float]] = {
        "coqui_xtts": 0.001,
        "piper": 0.0001,
        "elevenlabs": 0.03,
    }

    # Default monthly budget (USD) - should ultimately come from org settings
    _DEFAULT_BUDGET: ClassVar[float] = 100.0

    def __init__(self) -> None:
        self.settings = get_settings()
        self._health: dict[str, ProviderHealth] = {}
        self._circuits: dict[str, CircuitBreaker] = {
            p: CircuitBreaker() for p in self.TTS_PROVIDERS + self.ASR_PROVIDERS
        }
        self._http = httpx.AsyncClient(timeout=10.0)
        self._last_health_check: float = 0.0

    # ------------------------------------------------------------------
    # TTS routing
    # ------------------------------------------------------------------

    async def route_tts(
        self,
        text: str,
        voice_config: dict,
        org_id: str,
        request_type: RequestType,
        tier: str = "pro",
    ) -> ProviderSelection:
        """Select the optimal TTS provider."""
        await self._maybe_health_check()

        # Check cost budget before routing
        usage = await self.get_cost_usage(org_id)
        if usage.percent_used >= 100:
            raise RuntimeError(f"Cost budget exceeded for org {org_id}")

        # Cloned voices are locked to their originating provider
        if voice_config.get("provider"):
            provider = voice_config["provider"]
            if self._is_available(provider):
                return ProviderSelection(
                    provider=provider,
                    reason="voice locked to provider",
                    estimated_cost=self._estimate(text, provider),
                )

        # Filter to tier-accessible + currently healthy providers
        accessible = self.TIER_ACCESS.get(tier, self.TIER_ACCESS["free"])
        available = [p for p in accessible if self._is_available(p)]

        if not available:
            raise RuntimeError("No TTS providers available")

        # Route by request type
        if request_type == RequestType.PREVIEW:
            provider = "piper" if "piper" in available else available[0]
        elif request_type in (RequestType.PRODUCTION, RequestType.CLONE):
            provider = self._first_of(["elevenlabs", "coqui_xtts"], available)
        else:  # DRAFT
            provider = self._first_of(["coqui_xtts"], available)

        fallback = next((p for p in available if p != provider), None)
        return ProviderSelection(
            provider=provider,
            reason=f"{request_type.value} request, tier={tier}",
            estimated_cost=self._estimate(text, provider),
            fallback=fallback,
        )

    # ------------------------------------------------------------------
    # ASR routing
    # ------------------------------------------------------------------

    async def route_asr(self, audio_config: dict, org_id: str) -> ProviderSelection:
        """Select the best ASR provider.

        Args:
            audio_config: Audio configuration (format, sample rate, etc.).
            org_id: Organisation ID for cost tracking.
        """
        await self._maybe_health_check()

        # Prefer local faster_whisper (zero cost), fall back to deepgram
        if self._is_available("faster_whisper"):
            return ProviderSelection(
                provider="faster_whisper",
                reason=f"primary ASR for org={org_id}, format={audio_config.get('format', 'wav')}",
                estimated_cost=0.0,
                fallback="deepgram",
            )
        if self._is_available("deepgram"):
            return ProviderSelection(
                provider="deepgram",
                reason=f"fallback ASR for org={org_id}",
                estimated_cost=0.005,
            )
        raise RuntimeError("No ASR providers available")

    # ------------------------------------------------------------------
    # Health checking
    # ------------------------------------------------------------------

    async def check_provider_health(self, provider: str) -> ProviderHealth:
        """Probe a single provider's health endpoint."""
        endpoints: dict[str, str] = {
            "coqui_xtts": f"{self.settings.COQUI_XTTS_ENDPOINT}/health",
            "piper": f"{self.settings.PIPER_ENDPOINT}/health",
            "faster_whisper": f"{self.settings.FASTER_WHISPER_ENDPOINT}/health",
            "elevenlabs": "https://api.elevenlabs.io/v1/voices",
            "deepgram": "https://api.deepgram.com/v1/projects",
        }
        url = endpoints.get(provider)
        if not url:
            return ProviderHealth.DOWN

        try:
            headers: dict[str, str] = {}
            if provider == "elevenlabs" and self.settings.ELEVENLABS_API_KEY:
                headers["xi-api-key"] = self.settings.ELEVENLABS_API_KEY
            if provider == "deepgram" and self.settings.DEEPGRAM_API_KEY:
                headers["Authorization"] = f"Token {self.settings.DEEPGRAM_API_KEY}"

            resp = await self._http.get(url, headers=headers)
            if resp.status_code < 400:
                self._circuits[provider].record_success()
                return ProviderHealth.HEALTHY
            self._circuits[provider].record_failure()
            return ProviderHealth.DEGRADED
        except Exception:
            self._circuits[provider].record_failure()
            return ProviderHealth.DOWN

    async def get_provider_status(self) -> dict[str, str]:
        """Return the cached health status of every provider."""
        await self._maybe_health_check()
        return {p: h.value for p, h in self._health.items()}

    # ------------------------------------------------------------------
    # Cost tracking (Redis)
    # ------------------------------------------------------------------

    async def get_cost_usage(self, org_id: str) -> CostUsage:
        """Get current-month cost usage for an organisation."""
        import redis.asyncio as aioredis

        r = aioredis.from_url(self.settings.REDIS_URL)
        try:
            key = f"voiceforge:cost:{org_id}:{time.strftime('%Y-%m')}"
            cost = float(await r.get(key) or 0)
            budget = self._DEFAULT_BUDGET
            percent = (cost / budget * 100) if budget > 0 else 0

            alert: str | None = None
            if percent >= 100:
                alert = "100%"
            elif percent >= 90:
                alert = "90%"
            elif percent >= 75:
                alert = "75%"
            elif percent >= 50:
                alert = "50%"

            return CostUsage(
                org_id=org_id,
                current_month_cost=cost,
                budget_limit=budget,
                percent_used=percent,
                alert_level=alert,
            )
        finally:
            await r.aclose()

    async def update_cost(self, org_id: str, cost_usd: float, provider: str, request_type: str) -> None:
        """Increment the running cost counter for *org_id* in Redis."""
        import redis.asyncio as aioredis

        logger.info(
            "Recording cost: org=%s provider=%s type=%s amount=%.6f",
            org_id,
            provider,
            request_type,
            cost_usd,
        )

        r = aioredis.from_url(self.settings.REDIS_URL)
        try:
            key = f"voiceforge:cost:{org_id}:{time.strftime('%Y-%m')}"
            await r.incrbyfloat(key, cost_usd)
            await r.expire(key, 60 * 60 * 24 * 35)  # expire after ~35 days
        finally:
            await r.aclose()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _is_available(self, provider: str) -> bool:
        circuit = self._circuits.get(provider)
        if circuit and circuit.is_open:
            return False
        return self._health.get(provider, ProviderHealth.DOWN) != ProviderHealth.DOWN

    def _estimate(self, text: str, provider: str) -> float:
        """Rough cost estimate based on word count → audio minutes."""
        words = len(text.split())
        minutes = words / 150  # ~150 wpm average narration speed
        return minutes * self._COST_PER_MINUTE.get(provider, 0.01)

    @staticmethod
    def _first_of(preferred: list[str], available: list[str]) -> str:
        """Return the first preferred provider that is available, else fallback."""
        for p in preferred:
            if p in available:
                return p
        return available[0]

    async def _maybe_health_check(self) -> None:
        """Run health checks at most once per 60 seconds."""
        if time.time() - self._last_health_check < 60:
            return
        for provider in self.TTS_PROVIDERS + self.ASR_PROVIDERS:
            self._health[provider] = await self.check_provider_health(provider)
        self._last_health_check = time.time()

    async def close(self) -> None:
        """Shut down the underlying HTTP client."""
        await self._http.aclose()
