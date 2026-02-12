# VF06: Configuration, Docker Services & Dependencies

## Task
Add VoiceForge configuration settings, Docker services, and Python/JS dependencies.

## Files to Modify

### 1. `backend/app/config.py` — Add VoiceForge settings to the Settings class

Add these fields AFTER the existing Chrome Extension section (~line 99):

```python
    # VoiceForge — TTS Providers
    COQUI_XTTS_ENDPOINT: str = "http://localhost:8501"
    COQUI_XTTS_MODEL: str = "xtts_v2"
    PIPER_ENDPOINT: str = "http://localhost:8502"
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_DEFAULT_MODEL: str = "eleven_multilingual_v2"

    # VoiceForge — ASR Providers
    FASTER_WHISPER_ENDPOINT: str = "http://localhost:8503"
    FASTER_WHISPER_MODEL: str = "large-v3"
    FASTER_WHISPER_DEVICE: str = "cuda"
    DEEPGRAM_API_KEY: str = ""

    # VoiceForge — Audio Processing
    FFMPEG_PATH: str = "/usr/bin/ffmpeg"
    AUDIO_TEMP_DIR: str = "/tmp/voiceforge/audio"
    AUDIO_STORAGE_BUCKET: str = "selfpublisherforge-audio"

    # VoiceForge — Limits
    TTS_MAX_CONCURRENT_JOBS: int = 10
    TTS_MAX_CHAPTER_LENGTH_WORDS: int = 25000
    ASR_MAX_SESSION_DURATION_MINUTES: int = 120
    VOICE_CLONE_MAX_SAMPLES: int = 10
    VOICE_CLONE_MIN_AUDIO_SECONDS: int = 180
    VOICE_CLONE_MAX_AUDIO_SECONDS: int = 600
```

Also add to `_log_startup_config_warnings()` in `backend/app/main.py`:
```python
"VoiceForge TTS (Coqui)": bool(s.COQUI_XTTS_ENDPOINT),
"VoiceForge TTS (ElevenLabs)": bool(s.ELEVENLABS_API_KEY),
"VoiceForge ASR (Whisper)": bool(s.FASTER_WHISPER_ENDPOINT),
```

### 2. `backend/.env.example` — Add VoiceForge variables
Append the new variables with placeholder values and comments.

### 3. `docker-compose.yml` — Add 3 new services

Add after the existing services but before the `volumes:` and `networks:` sections:

```yaml
  coqui-xtts:
    image: ghcr.io/coqui-ai/xtts-streaming-server:latest
    ports:
      - "8501:8501"
    volumes:
      - xtts-models:/app/models
      - xtts-speakers:/app/speakers
    environment:
      - COQUI_TOS_AGREED=1
    restart: unless-stopped
    networks:
      - spf-network
    profiles:
      - voiceforge

  piper-tts:
    image: rhasspy/piper:latest
    ports:
      - "8502:8502"
    volumes:
      - piper-voices:/app/voices
    restart: unless-stopped
    networks:
      - spf-network
    profiles:
      - voiceforge

  faster-whisper:
    image: fedirz/faster-whisper-server:latest
    ports:
      - "8503:8000"
    environment:
      - WHISPER__MODEL=large-v3
      - WHISPER__DEVICE=cuda
    restart: unless-stopped
    networks:
      - spf-network
    profiles:
      - voiceforge
```

Add to the volumes section:
```yaml
  xtts-models:
  xtts-speakers:
  piper-voices:
```

NOTE: Use `profiles: [voiceforge]` so these services only start when explicitly requested with `docker compose --profile voiceforge up`.

### 4. `backend/requirements.txt` — Add dependencies
Append:
```
# VoiceForge Integration
pydub>=0.25.1
pyloudnorm>=0.1.1
soundfile>=0.12.1
numpy>=1.26.0
scipy>=1.12.0
websockets>=12.0
httpx>=0.27.0
python-multipart>=0.0.9
mutagen>=1.47.0
ffmpeg-python>=0.2.0
```

Check if any of these already exist in requirements.txt before adding.

### 5. `frontend/package.json` — Add frontend dependencies
Add to dependencies:
```json
"wavesurfer.js": "^7.0.0",
"recordrtc": "^5.6.2"
```

## Conventions
- Read existing files first and make targeted edits
- Use `profiles` in Docker to keep VoiceForge services opt-in
- Don't duplicate existing dependencies
