# FIX24: Unit Tests for TTS Engine & ASR Engine

## Task
Create unit tests for the TTS and ASR engine services.

## File to Create: `backend/tests/voiceforge/test_tts_asr_engines.py`

### Tests for TTSEngine (`backend/app/services/voiceforge/tts_engine.py`)
Read the source file first, then test:

1. `test_tts_engine_init` — TTSEngine can be instantiated
2. `test_estimate_cost_coqui` — Cost estimation for Coqui provider
3. `test_estimate_cost_elevenlabs` — Cost estimation for ElevenLabs (higher cost)
4. `test_estimate_cost_piper` — Cost estimation for Piper (lowest cost)
5. `test_generate_speech_invalid_provider` — Raises error for unknown provider
6. `test_provider_selection` — Correct provider is selected based on voice config

### Tests for ASREngine (`backend/app/services/voiceforge/asr_engine.py`)
Read the source file first, then test:

1. `test_asr_engine_init` — ASREngine can be instantiated
2. `test_start_session` — Creates a session with correct defaults
3. `test_detect_voice_commands` — Detects "new paragraph", "period", "stop dictation"
4. `test_detect_voice_commands_none` — Returns None for regular speech
5. `test_supported_languages` — Returns list of supported languages

### How to Mock
- Mock `httpx.AsyncClient` for HTTP calls to TTS/ASR servers
- Mock `app.config.get_settings()` to return test settings
- Use `pytest.fixture` for common setup
- Use `@pytest.mark.asyncio` for async tests

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.COQUI_XTTS_ENDPOINT = "http://localhost:8501"
    settings.PIPER_ENDPOINT = "http://localhost:8502"
    settings.ELEVENLABS_API_KEY = "test-key"
    settings.FASTER_WHISPER_ENDPOINT = "http://localhost:8503"
    settings.DEEPGRAM_API_KEY = "test-key"
    return settings
```

## Conventions
- Use pytest, pytest-asyncio
- Create `backend/tests/voiceforge/__init__.py` (empty)
- Mock external dependencies, don't call real services
