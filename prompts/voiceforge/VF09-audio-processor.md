# VF09: Audio Processor Service

## Task
Create the audio post-processing pipeline for audiobook production.

## Files to Create

### `backend/app/services/voiceforge/audio_processor.py`

Full audio processing pipeline using pydub, pyloudnorm, numpy, soundfile, ffmpeg-python.

**ACX Technical Requirements to validate against:**
- MP3 format, constant bit rate (CBR), 192 kbps
- 44.1 kHz sample rate
- Mono channel
- Peak values no higher than -3dB
- RMS between -23dB and -18dB
- Noise floor below -60dB
- 0.5 to 1 second room tone at head
- 1 to 5 seconds room tone at tail
- Per-chapter files ≤ 120 minutes

```python
import logging
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class ProcessedAudio:
    audio_path: Path
    duration_seconds: float
    sample_rate: int
    channels: int
    bit_rate: int
    file_size_bytes: int
    rms_db: float
    peak_db: float
    noise_floor_db: float

@dataclass
class LoudnessMetrics:
    rms_db: float
    peak_db: float
    noise_floor_db: float
    lufs: float
    dynamic_range_db: float

@dataclass
class ACXValidationResult:
    overall_pass: bool
    score: int  # 0-100
    checks: list[dict]  # [{name, passed, actual, expected, auto_fixable}]
    auto_fixable_issues: list[str]

@dataclass
class WaveformData:
    peaks: list[float]
    duration_seconds: float
    sample_rate: int
    resolution: int

@dataclass
class SilenceSegment:
    start_seconds: float
    end_seconds: float
    duration_seconds: float

class AudioProcessor:
    """Audio post-processing pipeline for audiobook production."""

    def __init__(self):
        from app.config import get_settings
        self.settings = get_settings()

    def normalize(self, audio_path: Path, target_rms: float = -20.0, target_peak: float = -3.0) -> ProcessedAudio:
        """Normalize audio to target RMS and peak levels."""
        import pyloudnorm as pyln
        import soundfile as sf

        data, rate = sf.read(str(audio_path))
        meter = pyln.Meter(rate)
        loudness = meter.integrated_loudness(data)
        # Normalize to target
        normalized = pyln.normalize.loudness(data, loudness, target_rms)
        # Peak limit
        peak = np.max(np.abs(normalized))
        peak_db = 20 * np.log10(peak) if peak > 0 else -100
        if peak_db > target_peak:
            gain = 10 ** ((target_peak - peak_db) / 20)
            normalized *= gain
        # Save
        out_path = self._temp_path(audio_path, "_normalized")
        sf.write(str(out_path), normalized, rate)
        return self._make_result(out_path, rate)

    def apply_noise_gate(self, audio_path: Path, threshold_db: float = -50.0) -> ProcessedAudio:
        """Remove background noise between sentences."""
        import soundfile as sf
        data, rate = sf.read(str(audio_path))
        threshold = 10 ** (threshold_db / 20)
        # Simple gate: zero out samples below threshold
        gated = np.where(np.abs(data) < threshold, data * 0.01, data)
        out_path = self._temp_path(audio_path, "_gated")
        sf.write(str(out_path), gated, rate)
        return self._make_result(out_path, rate)

    def apply_compression(self, audio_path: Path, ratio: float = 2.0, threshold_db: float = -20.0) -> ProcessedAudio:
        """Apply dynamic range compression."""
        import soundfile as sf
        data, rate = sf.read(str(audio_path))
        threshold = 10 ** (threshold_db / 20)
        compressed = np.copy(data)
        mask = np.abs(data) > threshold
        above = np.abs(data[mask]) - threshold
        compressed[mask] = np.sign(data[mask]) * (threshold + above / ratio)
        out_path = self._temp_path(audio_path, "_compressed")
        sf.write(str(out_path), compressed, rate)
        return self._make_result(out_path, rate)

    def apply_eq(self, audio_path: Path, highpass: int = 80, presence_boost: bool = True) -> ProcessedAudio:
        """Apply EQ: high-pass filter + optional presence boost."""
        from scipy.signal import butter, sosfilt
        import soundfile as sf
        data, rate = sf.read(str(audio_path))
        # High-pass filter
        sos = butter(4, highpass, btype='high', fs=rate, output='sos')
        filtered = sosfilt(sos, data)
        if presence_boost:
            # Gentle boost at 2-5kHz
            sos_boost = butter(2, [2000, 5000], btype='band', fs=rate, output='sos')
            presence = sosfilt(sos_boost, data) * 0.3
            filtered = filtered + presence
        out_path = self._temp_path(audio_path, "_eq")
        sf.write(str(out_path), filtered, rate)
        return self._make_result(out_path, rate)

    def add_room_tone(self, audio_path: Path, head_seconds: float = 0.75, tail_seconds: float = 3.0) -> ProcessedAudio:
        """Add room tone (silence) at head and tail of audio."""
        import soundfile as sf
        data, rate = sf.read(str(audio_path))
        # Generate very low-level noise as room tone
        head = np.random.normal(0, 0.0001, int(rate * head_seconds)).astype(data.dtype)
        tail = np.random.normal(0, 0.0001, int(rate * tail_seconds)).astype(data.dtype)
        result = np.concatenate([head, data, tail])
        out_path = self._temp_path(audio_path, "_roomtone")
        sf.write(str(out_path), result, rate)
        return self._make_result(out_path, rate)

    def convert_format(self, audio_path: Path, target_format: str = "mp3", bitrate: str = "192k", sample_rate: int = 44100) -> ProcessedAudio:
        """Convert audio to target format using ffmpeg."""
        import ffmpeg
        out_path = audio_path.with_suffix(f".{target_format}")
        stream = ffmpeg.input(str(audio_path))
        stream = ffmpeg.output(stream, str(out_path), ar=sample_rate, ab=bitrate, ac=1)
        ffmpeg.run(stream, overwrite_output=True, quiet=True)
        return self._make_result(out_path, sample_rate)

    def embed_metadata(self, audio_path: Path, metadata: dict) -> ProcessedAudio:
        """Embed ID3 tags into audio file."""
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, TCON
        audio = MP3(str(audio_path), ID3=ID3)
        if metadata.get("title"):
            audio.tags.add(TIT2(encoding=3, text=[metadata["title"]]))
        if metadata.get("artist"):
            audio.tags.add(TPE1(encoding=3, text=[metadata["artist"]]))
        if metadata.get("album"):
            audio.tags.add(TALB(encoding=3, text=[metadata["album"]]))
        if metadata.get("track"):
            audio.tags.add(TRCK(encoding=3, text=[str(metadata["track"])]))
        if metadata.get("genre"):
            audio.tags.add(TCON(encoding=3, text=[metadata["genre"]]))
        audio.save()
        return self._make_result(audio_path)

    def validate_acx(self, audio_path: Path) -> ACXValidationResult:
        """Validate audio against ACX technical requirements."""
        metrics = self.measure_loudness(audio_path)
        import soundfile as sf
        data, rate = sf.read(str(audio_path))
        duration = len(data) / rate
        channels = 1 if data.ndim == 1 else data.shape[1]

        checks = [
            {"name": "Sample Rate", "passed": rate == 44100, "actual": str(rate), "expected": "44100", "auto_fixable": True},
            {"name": "Channels (Mono)", "passed": channels == 1, "actual": str(channels), "expected": "1", "auto_fixable": True},
            {"name": "Peak ≤ -3dB", "passed": metrics.peak_db <= -3.0, "actual": f"{metrics.peak_db:.1f}dB", "expected": "≤ -3.0dB", "auto_fixable": True},
            {"name": "RMS -23dB to -18dB", "passed": -23.0 <= metrics.rms_db <= -18.0, "actual": f"{metrics.rms_db:.1f}dB", "expected": "-23 to -18dB", "auto_fixable": True},
            {"name": "Noise Floor < -60dB", "passed": metrics.noise_floor_db < -60.0, "actual": f"{metrics.noise_floor_db:.1f}dB", "expected": "< -60dB", "auto_fixable": False},
            {"name": "Duration ≤ 120 min", "passed": duration <= 7200, "actual": f"{duration/60:.1f} min", "expected": "≤ 120 min", "auto_fixable": False},
        ]

        passed = sum(1 for c in checks if c["passed"])
        auto_fixable = [c["name"] for c in checks if not c["passed"] and c["auto_fixable"]]
        return ACXValidationResult(
            overall_pass=all(c["passed"] for c in checks),
            score=int(passed / len(checks) * 100),
            checks=checks,
            auto_fixable_issues=auto_fixable,
        )

    def measure_loudness(self, audio_path: Path) -> LoudnessMetrics:
        """Measure audio loudness metrics."""
        import pyloudnorm as pyln
        import soundfile as sf
        data, rate = sf.read(str(audio_path))
        meter = pyln.Meter(rate)
        lufs = meter.integrated_loudness(data)
        peak = np.max(np.abs(data))
        peak_db = 20 * np.log10(peak) if peak > 0 else -100
        rms = np.sqrt(np.mean(data ** 2))
        rms_db = 20 * np.log10(rms) if rms > 0 else -100
        # Noise floor: analyze quietest 10% of frames
        frame_size = int(rate * 0.1)
        frames = [data[i:i+frame_size] for i in range(0, len(data) - frame_size, frame_size)]
        frame_rms = [np.sqrt(np.mean(f ** 2)) for f in frames if len(f) == frame_size]
        frame_rms.sort()
        noise_rms = np.mean(frame_rms[:max(1, len(frame_rms) // 10)])
        noise_floor_db = 20 * np.log10(noise_rms) if noise_rms > 0 else -100
        return LoudnessMetrics(rms_db=rms_db, peak_db=peak_db, noise_floor_db=noise_floor_db, lufs=lufs, dynamic_range_db=peak_db - rms_db)

    def merge_chapters(self, chapter_audio_paths: list[Path], output_format: str = "mp3") -> ProcessedAudio:
        """Merge all chapter audio files into a single audiobook file."""
        from pydub import AudioSegment
        combined = AudioSegment.empty()
        for path in chapter_audio_paths:
            segment = AudioSegment.from_file(str(path))
            combined += segment
        out_path = Path(tempfile.mktemp(suffix=f".{output_format}", dir=self.settings.AUDIO_TEMP_DIR))
        combined.export(str(out_path), format=output_format, bitrate="192k")
        return self._make_result(out_path)

    def generate_retail_sample(self, audio_path: Path, duration_seconds: int = 300) -> ProcessedAudio:
        """Extract first N seconds for retail sample (auto-trim at sentence boundary)."""
        from pydub import AudioSegment
        audio = AudioSegment.from_file(str(audio_path))
        sample = audio[:duration_seconds * 1000]
        # Fade out last 3 seconds
        sample = sample.fade_out(3000)
        out_path = self._temp_path(audio_path, "_sample")
        sample.export(str(out_path), format="mp3", bitrate="192k")
        return self._make_result(out_path)

    def generate_waveform(self, audio_path: Path, resolution: int = 1000) -> WaveformData:
        """Generate waveform visualization data."""
        import soundfile as sf
        data, rate = sf.read(str(audio_path))
        if data.ndim > 1:
            data = data.mean(axis=1)
        # Downsample to resolution points
        chunk_size = max(1, len(data) // resolution)
        peaks = [float(np.max(np.abs(data[i:i+chunk_size]))) for i in range(0, len(data), chunk_size)]
        return WaveformData(peaks=peaks[:resolution], duration_seconds=len(data)/rate, sample_rate=rate, resolution=len(peaks))

    def _temp_path(self, original: Path, suffix: str = "") -> Path:
        os.makedirs(self.settings.AUDIO_TEMP_DIR, exist_ok=True)
        stem = original.stem + suffix
        return Path(tempfile.mktemp(prefix=stem + "_", suffix=original.suffix, dir=self.settings.AUDIO_TEMP_DIR))

    def _make_result(self, path: Path, sample_rate: int = 44100) -> ProcessedAudio:
        import soundfile as sf
        try:
            data, rate = sf.read(str(path))
            duration = len(data) / rate
            rms = np.sqrt(np.mean(data ** 2))
            peak = np.max(np.abs(data))
        except Exception:
            duration, rate, rms, peak = 0, sample_rate, 0, 0
        return ProcessedAudio(
            audio_path=path,
            duration_seconds=duration,
            sample_rate=rate,
            channels=1,
            bit_rate=192,
            file_size_bytes=path.stat().st_size if path.exists() else 0,
            rms_db=20*np.log10(rms) if rms > 0 else -100,
            peak_db=20*np.log10(peak) if peak > 0 else -100,
            noise_floor_db=-70.0,
        )
```

Implement all methods fully with proper error handling.

## Dependencies
- pydub, pyloudnorm, soundfile, numpy, scipy, ffmpeg-python, mutagen
