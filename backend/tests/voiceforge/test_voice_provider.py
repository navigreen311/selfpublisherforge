"""Unit tests for VoiceManager and ProviderRouter services."""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audiobook import AudiobookVoice
from app.services.voiceforge.provider_router import (
    CircuitBreaker,
    CostUsage,
    ProviderHealth,
    ProviderRouter,
    RequestType,
)
from app.services.voiceforge.voice_manager import SYSTEM_VOICES, VoiceManager

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
SYSTEM_ORG = uuid.UUID("00000000-0000-0000-0000-000000000000")


@pytest.fixture
def org_id() -> uuid.UUID:
    return ORG_ID


@pytest.fixture
def voice_manager() -> VoiceManager:
    with patch("app.services.voiceforge.voice_manager.get_settings") as mock_settings:
        settings = MagicMock()
        settings.VOICE_CLONE_MIN_AUDIO_SECONDS = 180
        mock_settings.return_value = settings
        return VoiceManager()


@pytest.fixture
def provider_router() -> ProviderRouter:
    with patch("app.services.voiceforge.provider_router.get_settings") as mock_settings:
        settings = MagicMock()
        settings.COQUI_XTTS_ENDPOINT = "http://localhost:8501"
        settings.PIPER_ENDPOINT = "http://localhost:8502"
        settings.FASTER_WHISPER_ENDPOINT = "http://localhost:8503"
        settings.ELEVENLABS_API_KEY = "test-key"
        settings.DEEPGRAM_API_KEY = "test-key"
        settings.REDIS_URL = "redis://localhost:6379/0"
        mock_settings.return_value = settings
        router = ProviderRouter()
        # Preset all providers as HEALTHY so routing tests work predictably
        for p in router.TTS_PROVIDERS + router.ASR_PROVIDERS:
            router._health[p] = ProviderHealth.HEALTHY
        # Mark health check as recent so _maybe_health_check is a no-op
        router._last_health_check = time.time()
        return router


async def _seed_voices(db: AsyncSession) -> list[AudiobookVoice]:
    """Helper: insert system voices into the test database."""
    voices = []
    for v in SYSTEM_VOICES:
        voice = AudiobookVoice(
            org_id=SYSTEM_ORG,
            is_system_voice=True,
            active=True,
            **v,
        )
        db.add(voice)
        voices.append(voice)
    await db.flush()
    return voices


async def _create_org_voice(
    db: AsyncSession, org_id: uuid.UUID, name: str = "My Custom Voice"
) -> AudiobookVoice:
    """Helper: insert a custom org voice."""
    voice = AudiobookVoice(
        org_id=org_id,
        name=name,
        provider="coqui_xtts",
        voice_type="custom",
        is_system_voice=False,
        active=True,
    )
    db.add(voice)
    await db.flush()
    return voice


# ===========================================================================
# VoiceManager Tests
# ===========================================================================


class TestVoiceManagerInit:
    """test_voice_manager_init — VoiceManager can be instantiated."""

    def test_voice_manager_init(self, voice_manager: VoiceManager) -> None:
        assert voice_manager is not None
        assert voice_manager.settings is not None


class TestGetSystemVoices:
    """test_get_system_voices — Returns only system voices (is_system_voice=True)."""

    @pytest.mark.asyncio
    async def test_get_system_voices_seeds_when_empty(
        self, voice_manager: VoiceManager, db_session: AsyncSession
    ) -> None:
        """When no system voices exist, get_system_voices seeds them."""
        voices = await voice_manager.get_system_voices(db_session)
        assert len(voices) == len(SYSTEM_VOICES)
        assert all(v.is_system_voice for v in voices)

    @pytest.mark.asyncio
    async def test_get_system_voices_returns_existing(
        self, voice_manager: VoiceManager, db_session: AsyncSession
    ) -> None:
        """When system voices already exist, returns them without re-seeding."""
        await _seed_voices(db_session)
        voices = await voice_manager.get_system_voices(db_session)
        assert len(voices) == len(SYSTEM_VOICES)
        assert all(v.is_system_voice for v in voices)

    @pytest.mark.asyncio
    async def test_get_system_voices_excludes_custom(
        self, voice_manager: VoiceManager, db_session: AsyncSession, org_id: uuid.UUID
    ) -> None:
        """Custom org voices should not appear in system voice listing."""
        await _seed_voices(db_session)
        await _create_org_voice(db_session, org_id)
        voices = await voice_manager.get_system_voices(db_session)
        assert all(v.is_system_voice for v in voices)
        assert not any(v.name == "My Custom Voice" for v in voices)


class TestGetOrgVoices:
    """test_get_org_voices — Returns system + org-specific voices."""

    @pytest.mark.asyncio
    async def test_get_org_voices_includes_system(
        self, voice_manager: VoiceManager, db_session: AsyncSession, org_id: uuid.UUID
    ) -> None:
        """Org voices include system voices even with no custom voices."""
        await _seed_voices(db_session)
        voices = await voice_manager.get_org_voices(db_session, org_id)
        system_count = sum(1 for v in voices if v.is_system_voice)
        assert system_count == len(SYSTEM_VOICES)

    @pytest.mark.asyncio
    async def test_get_org_voices_includes_custom(
        self, voice_manager: VoiceManager, db_session: AsyncSession, org_id: uuid.UUID
    ) -> None:
        """Org voices include the org's own custom voices plus system voices."""
        await _seed_voices(db_session)
        await _create_org_voice(db_session, org_id, "Custom Narrator")
        voices = await voice_manager.get_org_voices(db_session, org_id)
        assert len(voices) == len(SYSTEM_VOICES) + 1
        custom = [v for v in voices if not v.is_system_voice]
        assert len(custom) == 1
        assert custom[0].name == "Custom Narrator"

    @pytest.mark.asyncio
    async def test_get_org_voices_excludes_inactive(
        self, voice_manager: VoiceManager, db_session: AsyncSession, org_id: uuid.UUID
    ) -> None:
        """Inactive voices are filtered out."""
        await _seed_voices(db_session)
        voice = await _create_org_voice(db_session, org_id, "Deactivated")
        voice.active = False
        await db_session.flush()
        voices = await voice_manager.get_org_voices(db_session, org_id)
        assert not any(v.name == "Deactivated" for v in voices)


class TestCreateClone:
    """test_create_clone — Creates a cloned voice record."""

    @pytest.mark.asyncio
    async def test_create_clone_success(
        self, voice_manager: VoiceManager, db_session: AsyncSession, org_id: uuid.UUID
    ) -> None:
        """Successfully creates a clone when audio is long enough."""
        mock_clone_result = {
            "voice_id": "cloned-voice-123",
            "source_url": "s3://bucket/audio.wav",
            "settings": {"stability": 0.5},
        }
        with (
            patch.object(voice_manager, "_get_duration", return_value=200.0),
            patch(
                "app.services.voiceforge.tts_engine.TTSEngine"
            ) as MockTTS,
        ):
            mock_tts = MockTTS.return_value
            mock_tts.clone_voice = AsyncMock(return_value=mock_clone_result)

            voice = await voice_manager.create_clone(
                db_session,
                org_id,
                "My Clone",
                [Path("/tmp/sample1.wav"), Path("/tmp/sample2.wav")],
                provider="coqui_xtts",
            )

        assert voice.name == "My Clone"
        assert voice.provider == "coqui_xtts"
        assert voice.provider_voice_id == "cloned-voice-123"
        assert voice.voice_type == "custom"
        assert voice.is_system_voice is False
        assert voice.active is True
        assert voice.org_id == org_id

    @pytest.mark.asyncio
    async def test_create_clone_insufficient_audio(
        self, voice_manager: VoiceManager, db_session: AsyncSession, org_id: uuid.UUID
    ) -> None:
        """Raises ValueError when audio samples are too short."""
        with patch.object(voice_manager, "_get_duration", return_value=30.0):
            with pytest.raises(ValueError, match="Need at least"):
                await voice_manager.create_clone(
                    db_session,
                    org_id,
                    "Short Clone",
                    [Path("/tmp/short.wav")],
                )


class TestDeleteCloneSystemVoice:
    """test_delete_clone_system_voice — Cannot delete system voices."""

    @pytest.mark.asyncio
    async def test_delete_system_voice_returns_false(
        self, voice_manager: VoiceManager, db_session: AsyncSession
    ) -> None:
        """Deleting a system voice returns False (query filters is_system_voice=False)."""
        voices = await _seed_voices(db_session)
        system_voice = voices[0]
        result = await voice_manager.delete_clone(
            db_session, system_voice.id, SYSTEM_ORG
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_custom_voice_success(
        self, voice_manager: VoiceManager, db_session: AsyncSession, org_id: uuid.UUID
    ) -> None:
        """Deleting a custom voice returns True and deactivates it."""
        voice = await _create_org_voice(db_session, org_id, "Deletable Voice")
        result = await voice_manager.delete_clone(db_session, voice.id, org_id)
        assert result is True
        await db_session.refresh(voice)
        assert voice.active is False

    @pytest.mark.asyncio
    async def test_delete_nonexistent_voice_returns_false(
        self, voice_manager: VoiceManager, db_session: AsyncSession, org_id: uuid.UUID
    ) -> None:
        """Deleting a voice that does not exist returns False."""
        result = await voice_manager.delete_clone(
            db_session, uuid.uuid4(), org_id
        )
        assert result is False


class TestDetectCharacters:
    """test_detect_characters — Detects dialogue characters in text."""

    @pytest.mark.asyncio
    async def test_detect_characters_returns_sorted(
        self, voice_manager: VoiceManager
    ) -> None:
        """Characters are returned sorted by dialogue_count descending."""
        mock_segments = [
            {"character": "Alice", "text": "Hello!"},
            {"character": "Bob", "text": "Hi there!"},
            {"character": "Alice", "text": "How are you?"},
            {"character": "Alice", "text": "I'm fine."},
            {"character": "narrator", "text": "She said."},
        ]
        with patch(
            "app.services.voiceforge.ssml_generator.SSMLGenerator"
        ) as MockSSML:
            mock_gen = MockSSML.return_value
            mock_gen.detect_dialogue = AsyncMock(return_value=mock_segments)

            chars = await voice_manager.detect_characters("some chapter text")

        assert len(chars) == 2
        assert chars[0]["name"] == "Alice"
        assert chars[0]["dialogue_count"] == 3
        assert chars[1]["name"] == "Bob"
        assert chars[1]["dialogue_count"] == 1

    @pytest.mark.asyncio
    async def test_detect_characters_excludes_narrator(
        self, voice_manager: VoiceManager
    ) -> None:
        """Narrator segments are not included in character results."""
        mock_segments = [
            {"character": "narrator", "text": "Once upon a time."},
            {"character": "narrator", "text": "The end."},
        ]
        with patch(
            "app.services.voiceforge.ssml_generator.SSMLGenerator"
        ) as MockSSML:
            mock_gen = MockSSML.return_value
            mock_gen.detect_dialogue = AsyncMock(return_value=mock_segments)

            chars = await voice_manager.detect_characters("narrator only text")

        assert chars == []

    @pytest.mark.asyncio
    async def test_detect_characters_empty_segments(
        self, voice_manager: VoiceManager
    ) -> None:
        """Empty segment list returns empty character list."""
        with patch(
            "app.services.voiceforge.ssml_generator.SSMLGenerator"
        ) as MockSSML:
            mock_gen = MockSSML.return_value
            mock_gen.detect_dialogue = AsyncMock(return_value=[])

            chars = await voice_manager.detect_characters("")

        assert chars == []


# ===========================================================================
# ProviderRouter Tests
# ===========================================================================


class TestProviderRouterInit:
    """test_provider_router_init — ProviderRouter can be instantiated."""

    def test_provider_router_init(self, provider_router: ProviderRouter) -> None:
        assert provider_router is not None
        assert provider_router.settings is not None
        assert "coqui_xtts" in provider_router._circuits
        assert "elevenlabs" in provider_router._circuits
        assert "piper" in provider_router._circuits

    def test_provider_router_class_vars(self) -> None:
        assert "coqui_xtts" in ProviderRouter.TTS_PROVIDERS
        assert "elevenlabs" in ProviderRouter.TTS_PROVIDERS
        assert "piper" in ProviderRouter.TTS_PROVIDERS
        assert "faster_whisper" in ProviderRouter.ASR_PROVIDERS
        assert "deepgram" in ProviderRouter.ASR_PROVIDERS


class TestRouteTTSCoqui:
    """test_route_tts_coqui — Routes to Coqui for standard requests."""

    @pytest.mark.asyncio
    async def test_route_tts_draft_selects_coqui(
        self, provider_router: ProviderRouter
    ) -> None:
        """DRAFT requests should prefer coqui_xtts."""
        with patch.object(
            provider_router, "get_cost_usage", new_callable=AsyncMock
        ) as mock_cost:
            mock_cost.return_value = CostUsage(
                org_id="org1", current_month_cost=5.0,
                budget_limit=100.0, percent_used=5.0, alert_level=None,
            )
            result = await provider_router.route_tts(
                text="This is a draft text for testing purposes.",
                voice_config={},
                org_id="org1",
                request_type=RequestType.DRAFT,
                tier="pro",
            )

        assert result.provider == "coqui_xtts"
        assert result.estimated_cost > 0

    @pytest.mark.asyncio
    async def test_route_tts_preview_selects_piper(
        self, provider_router: ProviderRouter
    ) -> None:
        """PREVIEW requests should prefer piper (fastest/cheapest)."""
        with patch.object(
            provider_router, "get_cost_usage", new_callable=AsyncMock
        ) as mock_cost:
            mock_cost.return_value = CostUsage(
                org_id="org1", current_month_cost=0.0,
                budget_limit=100.0, percent_used=0.0, alert_level=None,
            )
            result = await provider_router.route_tts(
                text="Quick preview.",
                voice_config={},
                org_id="org1",
                request_type=RequestType.PREVIEW,
                tier="pro",
            )

        assert result.provider == "piper"


class TestRouteTTSElevenLabs:
    """test_route_tts_elevenlabs — Routes to ElevenLabs for premium voices."""

    @pytest.mark.asyncio
    async def test_route_tts_production_selects_elevenlabs(
        self, provider_router: ProviderRouter
    ) -> None:
        """PRODUCTION requests should prefer elevenlabs for best quality."""
        with patch.object(
            provider_router, "get_cost_usage", new_callable=AsyncMock
        ) as mock_cost:
            mock_cost.return_value = CostUsage(
                org_id="org1", current_month_cost=10.0,
                budget_limit=100.0, percent_used=10.0, alert_level=None,
            )
            result = await provider_router.route_tts(
                text="Final production narration for the book.",
                voice_config={},
                org_id="org1",
                request_type=RequestType.PRODUCTION,
                tier="pro",
            )

        assert result.provider == "elevenlabs"
        assert result.fallback is not None

    @pytest.mark.asyncio
    async def test_route_tts_locked_voice(
        self, provider_router: ProviderRouter
    ) -> None:
        """Voice locked to a provider overrides routing logic."""
        with patch.object(
            provider_router, "get_cost_usage", new_callable=AsyncMock
        ) as mock_cost:
            mock_cost.return_value = CostUsage(
                org_id="org1", current_month_cost=0.0,
                budget_limit=100.0, percent_used=0.0, alert_level=None,
            )
            result = await provider_router.route_tts(
                text="Cloned voice narration.",
                voice_config={"provider": "elevenlabs"},
                org_id="org1",
                request_type=RequestType.DRAFT,
                tier="pro",
            )

        assert result.provider == "elevenlabs"
        assert result.reason == "voice locked to provider"

    @pytest.mark.asyncio
    async def test_route_tts_free_tier_no_elevenlabs(
        self, provider_router: ProviderRouter
    ) -> None:
        """Free tier should not have access to elevenlabs."""
        with patch.object(
            provider_router, "get_cost_usage", new_callable=AsyncMock
        ) as mock_cost:
            mock_cost.return_value = CostUsage(
                org_id="org1", current_month_cost=0.0,
                budget_limit=100.0, percent_used=0.0, alert_level=None,
            )
            result = await provider_router.route_tts(
                text="Free tier production text.",
                voice_config={},
                org_id="org1",
                request_type=RequestType.PRODUCTION,
                tier="free",
            )

        assert result.provider != "elevenlabs"

    @pytest.mark.asyncio
    async def test_route_tts_budget_exceeded_raises(
        self, provider_router: ProviderRouter
    ) -> None:
        """Exceeding budget should raise RuntimeError."""
        with patch.object(
            provider_router, "get_cost_usage", new_callable=AsyncMock
        ) as mock_cost:
            mock_cost.return_value = CostUsage(
                org_id="org1", current_month_cost=100.0,
                budget_limit=100.0, percent_used=100.0, alert_level="100%",
            )
            with pytest.raises(RuntimeError, match="Cost budget exceeded"):
                await provider_router.route_tts(
                    text="Over budget.",
                    voice_config={},
                    org_id="org1",
                    request_type=RequestType.DRAFT,
                    tier="pro",
                )


class TestCircuitBreakerOpens:
    """test_circuit_breaker_opens — Circuit breaker opens after failures."""

    def test_circuit_opens_after_three_failures(self) -> None:
        """After 3 failures within the window, circuit should be open."""
        cb = CircuitBreaker()
        assert not cb.is_open

        cb.record_failure()
        assert not cb.is_open
        cb.record_failure()
        assert not cb.is_open
        cb.record_failure()
        assert cb.is_open

    def test_circuit_stays_open_for_duration(self) -> None:
        """Circuit should remain open until the cooldown expires."""
        cb = CircuitBreaker()
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open
        assert cb.open_until > time.time()

    def test_provider_unavailable_when_circuit_open(
        self, provider_router: ProviderRouter
    ) -> None:
        """A provider with an open circuit is not available for routing."""
        circuit = provider_router._circuits["coqui_xtts"]
        circuit.record_failure()
        circuit.record_failure()
        circuit.record_failure()
        assert not provider_router._is_available("coqui_xtts")


class TestCircuitBreakerHalfOpen:
    """test_circuit_breaker_half_open — Allows test request after cooldown."""

    def test_circuit_closes_after_cooldown(self) -> None:
        """After the cooldown period, the circuit should be closed (half-open)."""
        cb = CircuitBreaker()
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open

        # Simulate cooldown expiry
        cb.open_until = time.time() - 1
        assert not cb.is_open

    def test_success_resets_circuit(self) -> None:
        """A successful request after half-open resets the circuit."""
        cb = CircuitBreaker()
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open

        # Simulate cooldown
        cb.open_until = time.time() - 1
        cb.record_success()
        assert cb.failures == 0
        assert cb.open_until == 0.0
        assert not cb.is_open

    def test_failure_window_reset(self) -> None:
        """Failures outside the window should reset the counter."""
        cb = CircuitBreaker()
        cb.record_failure()
        cb.record_failure()
        # Simulate that the last failure was more than 5 minutes ago
        cb.last_failure = time.time() - 400
        cb.record_failure()
        # Counter should have been reset, so only 1 failure now
        assert cb.failures == 1
        assert not cb.is_open


class TestCostTracking:
    """test_cost_tracking — Tracks and returns cost usage correctly."""

    @pytest.mark.asyncio
    async def test_get_cost_usage(self, provider_router: ProviderRouter) -> None:
        """Returns correct cost usage data from Redis."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=b"45.50")
        mock_redis.aclose = AsyncMock()

        with patch("redis.asyncio.from_url", return_value=mock_redis):
            usage = await provider_router.get_cost_usage("org-123")

        assert usage.org_id == "org-123"
        assert usage.current_month_cost == 45.50
        assert usage.budget_limit == 100.0
        assert usage.percent_used == 45.50
        assert usage.alert_level is None

    @pytest.mark.asyncio
    async def test_get_cost_usage_no_data(
        self, provider_router: ProviderRouter
    ) -> None:
        """Returns zero cost when no Redis data exists."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.aclose = AsyncMock()

        with patch("redis.asyncio.from_url", return_value=mock_redis):
            usage = await provider_router.get_cost_usage("org-new")

        assert usage.current_month_cost == 0.0
        assert usage.percent_used == 0.0
        assert usage.alert_level is None

    @pytest.mark.asyncio
    async def test_get_cost_usage_alert_levels(
        self, provider_router: ProviderRouter
    ) -> None:
        """Alert levels are set at correct thresholds."""
        mock_redis = AsyncMock()
        mock_redis.aclose = AsyncMock()

        # 50% threshold
        mock_redis.get = AsyncMock(return_value=b"50.0")
        with patch("redis.asyncio.from_url", return_value=mock_redis):
            usage = await provider_router.get_cost_usage("org1")
        assert usage.alert_level == "50%"

        # 75% threshold
        mock_redis.get = AsyncMock(return_value=b"75.0")
        with patch("redis.asyncio.from_url", return_value=mock_redis):
            usage = await provider_router.get_cost_usage("org1")
        assert usage.alert_level == "75%"

        # 90% threshold
        mock_redis.get = AsyncMock(return_value=b"90.0")
        with patch("redis.asyncio.from_url", return_value=mock_redis):
            usage = await provider_router.get_cost_usage("org1")
        assert usage.alert_level == "90%"

        # 100% threshold
        mock_redis.get = AsyncMock(return_value=b"100.0")
        with patch("redis.asyncio.from_url", return_value=mock_redis):
            usage = await provider_router.get_cost_usage("org1")
        assert usage.alert_level == "100%"

    @pytest.mark.asyncio
    async def test_update_cost(self, provider_router: ProviderRouter) -> None:
        """update_cost increments the Redis counter and sets expiry."""
        mock_redis = AsyncMock()
        mock_redis.incrbyfloat = AsyncMock()
        mock_redis.expire = AsyncMock()
        mock_redis.aclose = AsyncMock()

        with patch("redis.asyncio.from_url", return_value=mock_redis):
            await provider_router.update_cost("org1", 0.03, "elevenlabs", "production")

        mock_redis.incrbyfloat.assert_called_once()
        mock_redis.expire.assert_called_once()


class TestProviderHealthCheck:
    """test_provider_health_check — Returns provider health status."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(
        self, provider_router: ProviderRouter
    ) -> None:
        """Returns HEALTHY when provider responds with 2xx."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        provider_router._http = AsyncMock()
        provider_router._http.get = AsyncMock(return_value=mock_response)

        result = await provider_router.check_provider_health("coqui_xtts")
        assert result == ProviderHealth.HEALTHY

    @pytest.mark.asyncio
    async def test_health_check_degraded(
        self, provider_router: ProviderRouter
    ) -> None:
        """Returns DEGRADED when provider responds with 4xx/5xx."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        provider_router._http = AsyncMock()
        provider_router._http.get = AsyncMock(return_value=mock_response)

        result = await provider_router.check_provider_health("coqui_xtts")
        assert result == ProviderHealth.DEGRADED

    @pytest.mark.asyncio
    async def test_health_check_down(
        self, provider_router: ProviderRouter
    ) -> None:
        """Returns DOWN when provider raises an exception."""
        provider_router._http = AsyncMock()
        provider_router._http.get = AsyncMock(side_effect=Exception("Connection refused"))

        result = await provider_router.check_provider_health("coqui_xtts")
        assert result == ProviderHealth.DOWN

    @pytest.mark.asyncio
    async def test_health_check_unknown_provider(
        self, provider_router: ProviderRouter
    ) -> None:
        """Returns DOWN for an unknown provider name."""
        result = await provider_router.check_provider_health("nonexistent_provider")
        assert result == ProviderHealth.DOWN

    @pytest.mark.asyncio
    async def test_get_provider_status(
        self, provider_router: ProviderRouter
    ) -> None:
        """get_provider_status returns cached status for all providers."""
        status = await provider_router.get_provider_status()
        # All providers were set HEALTHY in the fixture
        assert all(v == "healthy" for v in status.values())
        assert "coqui_xtts" in status
        assert "elevenlabs" in status
        assert "piper" in status

    @pytest.mark.asyncio
    async def test_no_providers_available_raises(
        self, provider_router: ProviderRouter
    ) -> None:
        """RuntimeError when all providers are down."""
        for p in provider_router.TTS_PROVIDERS:
            provider_router._health[p] = ProviderHealth.DOWN

        with patch.object(
            provider_router, "get_cost_usage", new_callable=AsyncMock
        ) as mock_cost:
            mock_cost.return_value = CostUsage(
                org_id="org1", current_month_cost=0.0,
                budget_limit=100.0, percent_used=0.0, alert_level=None,
            )
            with pytest.raises(RuntimeError, match="No TTS providers available"):
                await provider_router.route_tts(
                    text="Test",
                    voice_config={},
                    org_id="org1",
                    request_type=RequestType.DRAFT,
                    tier="pro",
                )
