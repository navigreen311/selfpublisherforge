# FIX25: Unit Tests for AudioProcessor

## Task
Create unit tests for the AudioProcessor service.

## File to Create: `backend/tests/voiceforge/test_audio_processor.py`

### Tests for AudioProcessor (`backend/app/services/voiceforge/audio_processor.py`)
Read the source file first, then test:

1. `test_audio_processor_init` — Can be instantiated
2. `test_validate_acx_specs` — ACX validation checks correct thresholds:
   - Peak level <= -3dB
   - RMS between -23 and -18 dB
   - Noise floor < -60dB
   - Sample rate 44100Hz
   - MP3 CBR 192kbps
   - Mono channel
3. `test_validate_acx_passing` — Returns passed=True for compliant audio
4. `test_validate_acx_failing` — Returns passed=False with issues list
5. `test_normalize_target_lufs` — Normalize function targets correct LUFS
6. `test_loudness_metrics` — Measure loudness returns correct structure
7. `test_generate_waveform` — Returns waveform data array
8. `test_silence_detection` — Detects silence segments correctly
9. `test_format_conversion` — Converts between audio formats

### Mocking Strategy
- Create small test audio files using numpy (sine waves)
- Mock file I/O where needed
- Use `@pytest.mark.asyncio` for async tests

```python
import numpy as np
import pytest

@pytest.fixture
def sample_audio_data():
    """Generate a 1-second 440Hz sine wave at 44100Hz."""
    sample_rate = 44100
    t = np.linspace(0, 1, sample_rate, dtype=np.float32)
    audio = 0.5 * np.sin(2 * np.pi * 440 * t)
    return audio, sample_rate
```

## Conventions
- Use pytest
- Mock external dependencies
- Test edge cases (empty audio, very short audio, silence)
