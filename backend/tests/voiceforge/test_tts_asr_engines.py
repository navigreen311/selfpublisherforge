"""Unit tests for TTS Engine and ASR Engine services."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import AppException
from app.services.voiceforge.asr_engine import ASREngine, ASRSession
from app.services.voiceforge.tts_engine import CostEstimate, TTSEngine

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.COQUI_XTTS_ENDPOINT = "http://localhost:8501"
    settings.PIPER_ENDPOINT = "http://localhost:8502"
    settings.ELEVENLABS_API_KEY = "test-key"
    settings.FASTER_WHISPER_ENDPOINT = "http://localhost:8503"
    settings.FASTER_WHISPER_MODEL = "large-v3"
    settings.DEEPGRAM_API_KEY = "test-key"
    return settings


@pytest.fixture
def tts_engine(mock_settings):
    with patch("app.services.voiceforge.tts_engine.get_settings", return_value=mock_settings):
        engine = TTSEngine()
    yield engine


@pytest.fixture
def asr_engine(mock_settings):
    with patch("app.services.voiceforge.asr_engine.get_settings", return_value=mock_settings):
        engine = ASREngine()
    yield engine


# ===========================================================================
# TTSEngine tests
# ===========================================================================


class TestTTSEngineInit:
    """TTSEngine instantiation."""

    def test_tts_engine_init(self, tts_engine):
        assert tts_engine is not None
        assert tts_engine.WORDS_PER_MINUTE == 150
        assert tts_engine._http_client is not None


class TestTTSEstimateCost:
    """Cost estimation across providers."""

    def test_estimate_cost_coqui(self, tts_engine):
        text = " ".join(["word"] * 150)  # 150 words = 1 minute
        estimate = tts_engine.estimate_cost(text, "coqui_xtts")

        assert isinstance(estimate, CostEstimate)
        assert estimate.provider == "coqui_xtts"
        assert estimate.word_count == 150
        assert estimate.estimated_duration_minutes == 1.0
        assert estimate.cost_per_minute == 0.001
        assert estimate.total_cost == pytest.approx(0.001, abs=1e-6)

    def test_estimate_cost_elevenlabs(self, tts_engine):
        text = " ".join(["word"] * 150)  # 150 words = 1 minute
        estimate = tts_engine.estimate_cost(text, "elevenlabs")

        assert estimate.provider == "elevenlabs"
        assert estimate.cost_per_minute == 0.03
        assert estimate.total_cost == pytest.approx(0.03, abs=1e-6)
        # ElevenLabs should be more expensive than Coqui
        coqui_est = tts_engine.estimate_cost(text, "coqui_xtts")
        assert estimate.total_cost > coqui_est.total_cost

    def test_estimate_cost_piper(self, tts_engine):
        text = " ".join(["word"] * 150)  # 150 words = 1 minute
        estimate = tts_engine.estimate_cost(text, "piper")

        assert estimate.provider == "piper"
        assert estimate.cost_per_minute == 0.0001
        assert estimate.total_cost == pytest.approx(0.0001, abs=1e-7)
        # Piper should be the cheapest
        coqui_est = tts_engine.estimate_cost(text, "coqui_xtts")
        elevenlabs_est = tts_engine.estimate_cost(text, "elevenlabs")
        assert estimate.total_cost < coqui_est.total_cost
        assert estimate.total_cost < elevenlabs_est.total_cost


class TestTTSGenerateSpeech:
    """Speech generation provider routing."""

    @pytest.mark.asyncio
    async def test_generate_speech_invalid_provider(self, tts_engine):
        with pytest.raises(AppException) as exc_info:
            await tts_engine.generate_speech(
                text="Hello world",
                voice_id="default",
                provider="nonexistent_provider",
            )
        assert exc_info.value.code == "TTS_UNKNOWN_PROVIDER"
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_provider_selection(self, tts_engine):
        """Correct provider method is called based on the provider argument."""
        tts_engine._generate_coqui = AsyncMock()
        tts_engine._generate_elevenlabs = AsyncMock()
        tts_engine._generate_piper = AsyncMock()

        await tts_engine.generate_speech("Hello", "voice1", "coqui_xtts")
        tts_engine._generate_coqui.assert_called_once_with("Hello", "voice1", {})
        tts_engine._generate_elevenlabs.assert_not_called()
        tts_engine._generate_piper.assert_not_called()

        tts_engine._generate_coqui.reset_mock()
        await tts_engine.generate_speech("Hello", "voice2", "elevenlabs")
        tts_engine._generate_elevenlabs.assert_called_once_with("Hello", "voice2", {})
        tts_engine._generate_coqui.assert_not_called()

        tts_engine._generate_elevenlabs.reset_mock()
        await tts_engine.generate_speech("Hello", "voice3", "piper")
        tts_engine._generate_piper.assert_called_once_with("Hello", "voice3", {})


# ===========================================================================
# ASREngine tests
# ===========================================================================


class TestASREngineInit:
    """ASREngine instantiation."""

    def test_asr_engine_init(self, asr_engine):
        assert asr_engine is not None
        assert asr_engine.SAMPLE_RATE == 16000
        assert asr_engine._sessions == {}
        assert asr_engine._http_client is not None


class TestASRStartSession:
    """Session creation."""

    @pytest.mark.asyncio
    async def test_start_session(self, asr_engine):
        session = await asr_engine.start_session("test-session-1")

        assert isinstance(session, ASRSession)
        assert session.session_id == "test-session-1"
        assert session.language == "en"  # default
        assert session.is_active is True
        assert session.total_audio_seconds == 0.0
        assert len(session.buffer) == 0
        assert "test-session-1" in asr_engine._sessions

    @pytest.mark.asyncio
    async def test_start_session_with_language(self, asr_engine):
        session = await asr_engine.start_session("test-session-2", language="es")

        assert session.language == "es"


class TestASRVoiceCommands:
    """Voice command detection."""

    def test_detect_voice_commands(self):
        result = ASREngine.detect_voice_commands("new paragraph")
        assert result == ("new paragraph", "new_paragraph")

        result = ASREngine.detect_voice_commands("period")
        assert result == ("period", "insert_period")

        result = ASREngine.detect_voice_commands("stop dictation")
        assert result == ("stop dictation", "stop_dictation")

    def test_detect_voice_commands_case_insensitive(self):
        result = ASREngine.detect_voice_commands("New Paragraph")
        assert result == ("new paragraph", "new_paragraph")

        result = ASREngine.detect_voice_commands("STOP DICTATION")
        assert result == ("stop dictation", "stop_dictation")

    def test_detect_voice_commands_with_surrounding_text(self):
        # Command at the end
        result = ASREngine.detect_voice_commands("some text new paragraph")
        assert result == ("new paragraph", "new_paragraph")

        # Command at the start with trailing text
        result = ASREngine.detect_voice_commands("period something else")
        assert result == ("period", "insert_period")

    def test_detect_voice_commands_none(self):
        result = ASREngine.detect_voice_commands("hello world this is regular speech")
        assert result is None

        result = ASREngine.detect_voice_commands("")
        assert result is None

        result = ASREngine.detect_voice_commands("   ")
        assert result is None


class TestASRSupportedLanguages:
    """Supported language listing."""

    def test_supported_languages(self):
        languages = ASREngine.get_supported_languages()

        assert isinstance(languages, list)
        assert len(languages) == 10

        codes = [lang["code"] for lang in languages]
        assert "en" in codes
        assert "es" in codes
        assert "de" in codes
        assert "fr" in codes

        # Verify structure
        for lang in languages:
            assert "code" in lang
            assert "name" in lang

    def test_supported_languages_returns_copy(self):
        """Ensure the method returns a copy, not the internal list."""
        langs1 = ASREngine.get_supported_languages()
        langs2 = ASREngine.get_supported_languages()
        assert langs1 is not langs2
