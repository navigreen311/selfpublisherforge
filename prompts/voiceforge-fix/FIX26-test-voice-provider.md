# FIX26: Unit Tests for VoiceManager & ProviderRouter

## Task
Create unit tests for VoiceManager and ProviderRouter services.

## File to Create: `backend/tests/voiceforge/test_voice_provider.py`

### Tests for VoiceManager (`backend/app/services/voiceforge/voice_manager.py`)
Read the source file first, then test:

1. `test_voice_manager_init` — Can be instantiated
2. `test_get_system_voices` — Returns only system voices (is_system_voice=True)
3. `test_get_org_voices` — Returns system + org-specific voices
4. `test_create_clone` — Creates a cloned voice record
5. `test_delete_clone_system_voice` — Cannot delete system voices
6. `test_detect_characters` — Detects dialogue characters in text

### Tests for ProviderRouter (`backend/app/services/voiceforge/provider_router.py`)
Read the source file first, then test:

1. `test_provider_router_init` — Can be instantiated
2. `test_route_tts_coqui` — Routes to Coqui for standard requests
3. `test_route_tts_elevenlabs` — Routes to ElevenLabs for premium voices
4. `test_circuit_breaker_opens` — Circuit breaker opens after failures
5. `test_circuit_breaker_half_open` — Allows test request after cooldown
6. `test_cost_tracking` — Tracks and returns cost usage correctly
7. `test_provider_health_check` — Returns provider health status

### Mocking
- Mock `AsyncSession` for database queries
- Mock `httpx.AsyncClient` for health checks
- Mock Redis for cost tracking

## Conventions
- Use pytest, pytest-asyncio
- Mock all external dependencies
