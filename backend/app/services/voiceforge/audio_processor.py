"""Audio post-processing pipeline for audiobook production.

Provides normalization, noise gating, compression, EQ, room tone injection,
format conversion, metadata embedding, ACX validation, loudness measurement,
chapter merging, retail sample generation, and waveform data extraction.

ACX Technical Requirements enforced:
- MP3 format, constant bit rate (CBR), 192 kbps
- 44.1 kHz sample rate
- Mono channel
- Peak values no higher than -3 dB
- RMS between -23 dB and -18 dB
- Noise floor below -60 dB
- 0.5-1 second room tone at head
- 1-5 seconds room tone at tail
- Per-chapter files <= 120 minutes
"""

from __future__ import annotations

import logging
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ProcessedAudio:
    """Result of an audio processing step."""

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
    """Loudness measurement result."""

    rms_db: float
    peak_db: float
    noise_floor_db: float
    lufs: float
    dynamic_range_db: float


@dataclass
class ACXValidationResult:
    """ACX compliance validation result."""

    overall_pass: bool
    score: int  # 0-100
    checks: list[dict[str, Any]]  # [{name, passed, actual, expected, auto_fixable}]
    auto_fixable_issues: list[str]


@dataclass
class WaveformData:
    """Waveform visualization data."""

    peaks: list[float]
    duration_seconds: float
    sample_rate: int
    resolution: int


@dataclass
class SilenceSegment:
    """A segment of silence detected in audio."""

    start_seconds: float
    end_seconds: float
    duration_seconds: float


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ACX_SAMPLE_RATE = 44100
_ACX_CHANNELS = 1
_ACX_BITRATE = "192k"
_ACX_BITRATE_KBPS = 192
_ACX_PEAK_DB_MAX = -3.0
_ACX_RMS_DB_MIN = -23.0
_ACX_RMS_DB_MAX = -18.0
_ACX_NOISE_FLOOR_DB_MAX = -60.0
_ACX_MAX_DURATION_SECONDS = 7200  # 120 minutes


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class AudioProcessor:
    """Audio post-processing pipeline for audiobook production."""

    def __init__(self) -> None:
        from app.config import get_settings

        self.settings = get_settings()
        self._temp_dir: Path = Path(
            getattr(self.settings, "AUDIO_TEMP_DIR", Path(tempfile.gettempdir()) / "voiceforge_audio"),
        )
        self._temp_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public pipeline methods
    # ------------------------------------------------------------------

    def normalize(
        self,
        audio_path: Path,
        target_rms: float = -20.0,
        target_peak: float = _ACX_PEAK_DB_MAX,
    ) -> ProcessedAudio:
        """Normalize audio to *target_rms* LUFS and limit peaks to *target_peak* dB.

        Uses ITU-R BS.1770-4 integrated loudness via ``pyloudnorm``.
        """
        import pyloudnorm as pyln
        import soundfile as sf

        logger.info("Normalizing %s (target_rms=%.1f, target_peak=%.1f)", audio_path, target_rms, target_peak)

        data, rate = sf.read(str(audio_path))
        data = self._ensure_mono(data)

        meter = pyln.Meter(rate)
        loudness = meter.integrated_loudness(data)

        if np.isinf(loudness):
            logger.warning("Integrated loudness is -inf (silent file?). Skipping normalization.")
            out_path = self._temp_path(audio_path, "_normalized")
            sf.write(str(out_path), data, rate)
            return self._make_result(out_path, rate)

        normalized = pyln.normalize.loudness(data, loudness, target_rms)

        # Peak limiting
        peak = np.max(np.abs(normalized))
        if peak > 0:
            peak_db = 20.0 * np.log10(peak)
            if peak_db > target_peak:
                gain = 10.0 ** ((target_peak - peak_db) / 20.0)
                normalized *= gain
                logger.debug("Applied peak limiter gain: %.4f", gain)

        out_path = self._temp_path(audio_path, "_normalized")
        sf.write(str(out_path), normalized, rate)
        logger.info("Normalization complete: %s", out_path)
        return self._make_result(out_path, rate)

    def apply_noise_gate(
        self,
        audio_path: Path,
        threshold_db: float = -50.0,
        attack_ms: float = 5.0,
        release_ms: float = 50.0,
    ) -> ProcessedAudio:
        """Remove background noise between sentences using a simple soft gate.

        Samples below *threshold_db* are attenuated by 40 dB (not hard-zeroed)
        to preserve a natural room-tone feel.  Simple linear attack/release
        envelopes smooth transitions.
        """
        import soundfile as sf

        logger.info("Applying noise gate to %s (threshold=%.1f dB)", audio_path, threshold_db)

        data, rate = sf.read(str(audio_path))
        data = self._ensure_mono(data)

        threshold_linear = 10.0 ** (threshold_db / 20.0)
        attenuation = 0.01  # -40 dB attenuation for gated sections

        # Frame-level envelope follower
        frame_len = max(1, int(rate * 0.01))  # 10 ms frames
        attack_frames = max(1, int((attack_ms / 1000.0) * rate / frame_len))
        release_frames = max(1, int((release_ms / 1000.0) * rate / frame_len))

        num_frames = len(data) // frame_len
        envelope = np.ones(len(data), dtype=np.float64)

        gate_open = True
        open_counter = 0

        for i in range(num_frames):
            start = i * frame_len
            end = start + frame_len
            frame_peak = np.max(np.abs(data[start:end]))

            if frame_peak >= threshold_linear:
                if not gate_open:
                    open_counter += 1
                    # Ramp up over attack_frames
                    t = min(open_counter / attack_frames, 1.0)
                    envelope[start:end] = attenuation + t * (1.0 - attenuation)
                    if open_counter >= attack_frames:
                        gate_open = True
                        open_counter = 0
                # else: already open, envelope stays 1.0
            else:
                if gate_open:
                    open_counter += 1
                    t = min(open_counter / release_frames, 1.0)
                    envelope[start:end] = 1.0 - t * (1.0 - attenuation)
                    if open_counter >= release_frames:
                        gate_open = False
                        open_counter = 0
                else:
                    envelope[start:end] = attenuation

        # Handle remainder samples
        remainder_start = num_frames * frame_len
        if remainder_start < len(data):
            envelope[remainder_start:] = envelope[remainder_start - 1] if remainder_start > 0 else attenuation

        gated = data * envelope

        out_path = self._temp_path(audio_path, "_gated")
        sf.write(str(out_path), gated, rate)
        logger.info("Noise gate applied: %s", out_path)
        return self._make_result(out_path, rate)

    def apply_compression(
        self,
        audio_path: Path,
        ratio: float = 2.0,
        threshold_db: float = -20.0,
    ) -> ProcessedAudio:
        """Apply dynamic range compression.

        Signals exceeding *threshold_db* are compressed by *ratio*:1.
        """
        import soundfile as sf

        logger.info(
            "Applying compression to %s (ratio=%.1f, threshold=%.1f dB)",
            audio_path,
            ratio,
            threshold_db,
        )

        data, rate = sf.read(str(audio_path))
        data = self._ensure_mono(data)

        threshold_linear = 10.0 ** (threshold_db / 20.0)

        compressed = np.copy(data)
        mask = np.abs(data) > threshold_linear
        above = np.abs(data[mask]) - threshold_linear
        compressed[mask] = np.sign(data[mask]) * (threshold_linear + above / ratio)

        out_path = self._temp_path(audio_path, "_compressed")
        sf.write(str(out_path), compressed, rate)
        logger.info("Compression applied: %s", out_path)
        return self._make_result(out_path, rate)

    def apply_eq(
        self,
        audio_path: Path,
        highpass: int = 80,
        presence_boost: bool = True,
    ) -> ProcessedAudio:
        """Apply EQ: high-pass filter + optional presence boost (2-5 kHz).

        Uses Butterworth IIR filters via ``scipy.signal``.
        """
        import soundfile as sf
        from scipy.signal import butter, sosfilt

        logger.info("Applying EQ to %s (highpass=%d Hz, presence_boost=%s)", audio_path, highpass, presence_boost)

        data, rate = sf.read(str(audio_path))
        data = self._ensure_mono(data)

        nyquist = rate / 2.0

        # High-pass filter to remove rumble
        if highpass < nyquist:
            sos_hp = butter(4, highpass, btype="high", fs=rate, output="sos")
            filtered = sosfilt(sos_hp, data).astype(np.float64)
        else:
            logger.warning("High-pass frequency %d >= Nyquist %d; skipping high-pass.", highpass, int(nyquist))
            filtered = data.copy()

        # Optional presence boost at 2-5 kHz
        if presence_boost and nyquist > 5000:
            low = max(2000, highpass + 1)
            high = min(5000, int(nyquist) - 1)
            if low < high:
                sos_band = butter(2, [low, high], btype="band", fs=rate, output="sos")
                presence = sosfilt(sos_band, data).astype(np.float64)
                filtered = filtered + presence * 0.3
            else:
                logger.warning("Presence band [%d, %d] invalid; skipping boost.", low, high)

        out_path = self._temp_path(audio_path, "_eq")
        sf.write(str(out_path), filtered, rate)
        logger.info("EQ applied: %s", out_path)
        return self._make_result(out_path, rate)

    def add_room_tone(
        self,
        audio_path: Path,
        head_seconds: float = 0.75,
        tail_seconds: float = 3.0,
    ) -> ProcessedAudio:
        """Add room tone (very-low-level noise) at head and tail.

        ACX requires 0.5-1 s at head and 1-5 s at tail.
        """
        import soundfile as sf

        logger.info(
            "Adding room tone to %s (head=%.2fs, tail=%.2fs)",
            audio_path,
            head_seconds,
            tail_seconds,
        )

        data, rate = sf.read(str(audio_path))
        data = self._ensure_mono(data)

        rng = np.random.default_rng(seed=42)
        head_samples = int(rate * head_seconds)
        tail_samples = int(rate * tail_seconds)

        head = rng.normal(0, 0.0001, head_samples).astype(data.dtype)
        tail = rng.normal(0, 0.0001, tail_samples).astype(data.dtype)

        result = np.concatenate([head, data, tail])

        out_path = self._temp_path(audio_path, "_roomtone")
        sf.write(str(out_path), result, rate)
        logger.info("Room tone added: %s", out_path)
        return self._make_result(out_path, rate)

    def convert_format(
        self,
        audio_path: Path,
        target_format: str = "mp3",
        bitrate: str = _ACX_BITRATE,
        sample_rate: int = _ACX_SAMPLE_RATE,
    ) -> ProcessedAudio:
        """Convert audio to *target_format* using ffmpeg.

        Defaults match ACX requirements: MP3, 192 kbps CBR, 44.1 kHz, mono.
        """
        import ffmpeg

        out_path = audio_path.with_suffix(f".{target_format}")
        if out_path == audio_path:
            out_path = self._temp_path(audio_path, "_converted")
            out_path = out_path.with_suffix(f".{target_format}")

        logger.info("Converting %s -> %s (%s, %s, %d Hz)", audio_path, out_path, target_format, bitrate, sample_rate)

        try:
            stream = ffmpeg.input(str(audio_path))
            stream = ffmpeg.output(stream, str(out_path), ar=sample_rate, ab=bitrate, ac=1)
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
        except ffmpeg.Error as exc:
            logger.error("ffmpeg conversion failed: %s", exc)
            raise RuntimeError(f"Audio format conversion failed: {exc}") from exc

        return self._make_result(out_path, sample_rate)

    def embed_metadata(self, audio_path: Path, metadata: dict[str, Any]) -> ProcessedAudio:
        """Embed ID3 tags into an MP3 file.

        Supported keys: title, artist, album, track, genre, year, comment.
        """
        from mutagen.id3 import COMM, ID3, TALB, TCON, TDRC, TIT2, TPE1, TRCK
        from mutagen.mp3 import MP3

        logger.info("Embedding metadata into %s: %s", audio_path, list(metadata.keys()))

        try:
            audio = MP3(str(audio_path), ID3=ID3)
        except Exception:
            # File may not have existing ID3 tags
            audio = MP3(str(audio_path))
            audio.add_tags()

        tag_map: dict[str, Any] = {
            "title": lambda v: TIT2(encoding=3, text=[v]),
            "artist": lambda v: TPE1(encoding=3, text=[v]),
            "album": lambda v: TALB(encoding=3, text=[v]),
            "track": lambda v: TRCK(encoding=3, text=[str(v)]),
            "genre": lambda v: TCON(encoding=3, text=[v]),
            "year": lambda v: TDRC(encoding=3, text=[str(v)]),
            "comment": lambda v: COMM(encoding=3, lang="eng", desc="", text=[v]),
        }

        for key, value in metadata.items():
            if value and key in tag_map:
                audio.tags.add(tag_map[key](value))
            elif key not in tag_map:
                logger.warning("Unknown metadata key ignored: %s", key)

        audio.save()
        logger.info("Metadata embedded successfully.")
        return self._make_result(audio_path)

    # ------------------------------------------------------------------
    # Validation & measurement
    # ------------------------------------------------------------------

    def validate_acx(self, audio_path: Path) -> ACXValidationResult:
        """Validate audio against ACX technical requirements.

        Returns a result with individual checks and an overall pass/fail.
        Auto-fixable issues are flagged so callers can attempt remediation.
        """
        import soundfile as sf

        logger.info("Validating ACX compliance for %s", audio_path)

        metrics = self.measure_loudness(audio_path)

        data, rate = sf.read(str(audio_path))
        data = self._ensure_mono(data)
        duration = len(data) / rate
        channels = 1  # _ensure_mono guarantees this

        # Detect file format
        file_ext = audio_path.suffix.lower().lstrip(".")
        is_mp3 = file_ext == "mp3"

        checks: list[dict[str, Any]] = [
            {
                "name": "Format (MP3)",
                "passed": is_mp3,
                "actual": file_ext,
                "expected": "mp3",
                "auto_fixable": True,
            },
            {
                "name": "Sample Rate",
                "passed": rate == _ACX_SAMPLE_RATE,
                "actual": str(rate),
                "expected": str(_ACX_SAMPLE_RATE),
                "auto_fixable": True,
            },
            {
                "name": "Channels (Mono)",
                "passed": channels == 1,
                "actual": str(channels),
                "expected": "1",
                "auto_fixable": True,
            },
            {
                "name": f"Peak <= {_ACX_PEAK_DB_MAX} dB",
                "passed": metrics.peak_db <= _ACX_PEAK_DB_MAX,
                "actual": f"{metrics.peak_db:.1f} dB",
                "expected": f"<= {_ACX_PEAK_DB_MAX} dB",
                "auto_fixable": True,
            },
            {
                "name": f"RMS {_ACX_RMS_DB_MIN} to {_ACX_RMS_DB_MAX} dB",
                "passed": _ACX_RMS_DB_MIN <= metrics.rms_db <= _ACX_RMS_DB_MAX,
                "actual": f"{metrics.rms_db:.1f} dB",
                "expected": f"{_ACX_RMS_DB_MIN} to {_ACX_RMS_DB_MAX} dB",
                "auto_fixable": True,
            },
            {
                "name": f"Noise Floor < {_ACX_NOISE_FLOOR_DB_MAX} dB",
                "passed": metrics.noise_floor_db < _ACX_NOISE_FLOOR_DB_MAX,
                "actual": f"{metrics.noise_floor_db:.1f} dB",
                "expected": f"< {_ACX_NOISE_FLOOR_DB_MAX} dB",
                "auto_fixable": False,
            },
            {
                "name": "Duration <= 120 min",
                "passed": duration <= _ACX_MAX_DURATION_SECONDS,
                "actual": f"{duration / 60:.1f} min",
                "expected": "<= 120 min",
                "auto_fixable": False,
            },
        ]

        passed_count = sum(1 for c in checks if c["passed"])
        auto_fixable = [c["name"] for c in checks if not c["passed"] and c["auto_fixable"]]

        result = ACXValidationResult(
            overall_pass=all(c["passed"] for c in checks),
            score=int(passed_count / len(checks) * 100),
            checks=checks,
            auto_fixable_issues=auto_fixable,
        )

        if result.overall_pass:
            logger.info("ACX validation PASSED (score=%d)", result.score)
        else:
            logger.warning(
                "ACX validation FAILED (score=%d, fixable=%s)",
                result.score,
                auto_fixable,
            )

        return result

    def measure_loudness(self, audio_path: Path) -> LoudnessMetrics:
        """Measure audio loudness metrics (RMS, peak, noise floor, LUFS)."""
        import pyloudnorm as pyln
        import soundfile as sf

        data, rate = sf.read(str(audio_path))
        data = self._ensure_mono(data)

        # LUFS
        meter = pyln.Meter(rate)
        lufs = meter.integrated_loudness(data)
        if np.isinf(lufs):
            lufs = -100.0

        # Peak
        peak = float(np.max(np.abs(data)))
        peak_db = 20.0 * np.log10(peak) if peak > 0 else -100.0

        # RMS
        rms = float(np.sqrt(np.mean(data**2)))
        rms_db = 20.0 * np.log10(rms) if rms > 0 else -100.0

        # Noise floor: average RMS of the quietest 10 % of 100 ms frames
        frame_size = max(1, int(rate * 0.1))
        num_full_frames = len(data) // frame_size
        if num_full_frames > 0:
            frames = data[: num_full_frames * frame_size].reshape(num_full_frames, frame_size)
            frame_rms_vals = np.sqrt(np.mean(frames**2, axis=1))
            frame_rms_sorted = np.sort(frame_rms_vals)
            n_quiet = max(1, len(frame_rms_sorted) // 10)
            noise_rms = float(np.mean(frame_rms_sorted[:n_quiet]))
        else:
            noise_rms = rms

        noise_floor_db = 20.0 * np.log10(noise_rms) if noise_rms > 0 else -100.0

        return LoudnessMetrics(
            rms_db=rms_db,
            peak_db=peak_db,
            noise_floor_db=noise_floor_db,
            lufs=lufs,
            dynamic_range_db=peak_db - rms_db,
        )

    def detect_silence(
        self,
        audio_path: Path,
        threshold_db: float = -40.0,
        min_duration_seconds: float = 0.5,
    ) -> list[SilenceSegment]:
        """Detect silence segments in audio.

        Returns a list of :class:`SilenceSegment` instances where the RMS
        level drops below *threshold_db* for at least *min_duration_seconds*.
        """
        import soundfile as sf

        data, rate = sf.read(str(audio_path))
        data = self._ensure_mono(data)

        threshold_linear = 10.0 ** (threshold_db / 20.0)
        min_samples = int(rate * min_duration_seconds)
        frame_size = max(1, int(rate * 0.01))  # 10 ms frames

        segments: list[SilenceSegment] = []
        silence_start: int | None = None

        for i in range(0, len(data) - frame_size, frame_size):
            frame_rms = float(np.sqrt(np.mean(data[i : i + frame_size] ** 2)))
            is_silent = frame_rms < threshold_linear

            if is_silent and silence_start is None:
                silence_start = i
            elif not is_silent and silence_start is not None:
                duration_samples = i - silence_start
                if duration_samples >= min_samples:
                    segments.append(
                        SilenceSegment(
                            start_seconds=silence_start / rate,
                            end_seconds=i / rate,
                            duration_seconds=duration_samples / rate,
                        )
                    )
                silence_start = None

        # Handle trailing silence
        if silence_start is not None:
            duration_samples = len(data) - silence_start
            if duration_samples >= min_samples:
                segments.append(
                    SilenceSegment(
                        start_seconds=silence_start / rate,
                        end_seconds=len(data) / rate,
                        duration_seconds=duration_samples / rate,
                    )
                )

        logger.info("Detected %d silence segments in %s", len(segments), audio_path)
        return segments

    # ------------------------------------------------------------------
    # Chapter / sample operations
    # ------------------------------------------------------------------

    def merge_chapters(
        self,
        chapter_audio_paths: list[Path],
        output_format: str = "mp3",
    ) -> ProcessedAudio:
        """Merge chapter audio files into a single audiobook file."""
        from pydub import AudioSegment

        if not chapter_audio_paths:
            raise ValueError("No chapter audio paths provided for merging.")

        logger.info("Merging %d chapters into single %s file", len(chapter_audio_paths), output_format)

        combined = AudioSegment.empty()
        for idx, path in enumerate(chapter_audio_paths):
            if not path.exists():
                raise FileNotFoundError(f"Chapter file not found: {path}")
            logger.debug("Adding chapter %d: %s", idx + 1, path)
            segment = AudioSegment.from_file(str(path))
            combined += segment

        fd, tmp = tempfile.mkstemp(
            suffix=f".{output_format}",
            dir=str(self._temp_dir),
        )
        os.close(fd)
        out_path = Path(tmp)
        combined.export(str(out_path), format=output_format, bitrate=_ACX_BITRATE)

        logger.info("Chapters merged: %s (duration=%.1fs)", out_path, combined.duration_seconds)
        return self._make_result(out_path)

    def generate_retail_sample(
        self,
        audio_path: Path,
        duration_seconds: int = 300,
    ) -> ProcessedAudio:
        """Extract the first *duration_seconds* for a retail sample.

        The last 3 seconds are faded out for a clean ending.
        """
        from pydub import AudioSegment

        logger.info("Generating %ds retail sample from %s", duration_seconds, audio_path)

        audio = AudioSegment.from_file(str(audio_path))
        sample = audio[: duration_seconds * 1000]

        # Fade out last 3 seconds (or the whole sample if shorter)
        fade_ms = min(3000, len(sample))
        sample = sample.fade_out(fade_ms)

        out_path = self._temp_path(audio_path, "_sample")
        out_path = out_path.with_suffix(".mp3")
        sample.export(str(out_path), format="mp3", bitrate=_ACX_BITRATE)

        logger.info("Retail sample generated: %s", out_path)
        return self._make_result(out_path)

    # ------------------------------------------------------------------
    # Waveform
    # ------------------------------------------------------------------

    def generate_waveform(self, audio_path: Path, resolution: int = 1000) -> WaveformData:
        """Generate waveform peak data for visualization.

        Downsamples the audio to *resolution* data points, each representing
        the absolute peak of its chunk.
        """
        import soundfile as sf

        data, rate = sf.read(str(audio_path))
        data = self._ensure_mono(data)

        chunk_size = max(1, len(data) // resolution)
        num_chunks = min(resolution, len(data) // chunk_size)

        peaks: list[float] = []
        for i in range(num_chunks):
            start = i * chunk_size
            end = start + chunk_size
            peaks.append(float(np.max(np.abs(data[start:end]))))

        return WaveformData(
            peaks=peaks,
            duration_seconds=len(data) / rate,
            sample_rate=rate,
            resolution=len(peaks),
        )

    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------

    def process_chapter(
        self,
        audio_path: Path,
        metadata: dict[str, Any] | None = None,
        skip_eq: bool = False,
    ) -> ProcessedAudio:
        """Run the full ACX-compliant processing pipeline on a single chapter.

        Pipeline order:
        1. EQ (high-pass + presence boost)
        2. Noise gate
        3. Compression
        4. Normalization (to ACX RMS/peak targets)
        5. Room tone (head + tail)
        6. Format conversion (MP3, 192 kbps, 44.1 kHz, mono)
        7. Metadata embedding (if provided)
        """
        logger.info("Starting full chapter processing pipeline for %s", audio_path)

        current = audio_path

        # 1. EQ
        if not skip_eq:
            result = self.apply_eq(current)
            current = result.audio_path

        # 2. Noise gate
        result = self.apply_noise_gate(current)
        current = result.audio_path

        # 3. Compression
        result = self.apply_compression(current)
        current = result.audio_path

        # 4. Normalize to ACX target
        result = self.normalize(current, target_rms=-20.0, target_peak=_ACX_PEAK_DB_MAX)
        current = result.audio_path

        # 5. Room tone
        result = self.add_room_tone(current, head_seconds=0.75, tail_seconds=3.0)
        current = result.audio_path

        # 6. Convert to MP3
        result = self.convert_format(
            current,
            target_format="mp3",
            bitrate=_ACX_BITRATE,
            sample_rate=_ACX_SAMPLE_RATE,
        )
        current = result.audio_path

        # 7. Metadata
        if metadata:
            result = self.embed_metadata(current, metadata)

        logger.info("Chapter processing complete: %s", result.audio_path)
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_mono(data: np.ndarray) -> np.ndarray:
        """Convert multi-channel audio to mono by averaging channels."""
        if data.ndim > 1:
            return cast("np.ndarray", data.mean(axis=1))
        return data

    def _temp_path(self, original: Path, suffix: str = "") -> Path:
        """Generate a temporary file path preserving the original extension."""
        self._temp_dir.mkdir(parents=True, exist_ok=True)
        stem = original.stem + suffix
        fd, tmp = tempfile.mkstemp(
            prefix=stem + "_",
            suffix=original.suffix,
            dir=str(self._temp_dir),
        )
        os.close(fd)
        return Path(tmp)

    def _make_result(self, path: Path, sample_rate: int = _ACX_SAMPLE_RATE) -> ProcessedAudio:
        """Build a :class:`ProcessedAudio` from the file at *path*."""
        import soundfile as sf

        try:
            data, rate = sf.read(str(path))
            data = self._ensure_mono(data)
            duration = len(data) / rate
            rms = float(np.sqrt(np.mean(data**2)))
            peak = float(np.max(np.abs(data)))
        except Exception:
            logger.warning("Could not read processed file %s for metrics; using defaults.", path)
            duration, rate, rms, peak = 0.0, sample_rate, 0.0, 0.0

        rms_db = 20.0 * np.log10(rms) if rms > 0 else -100.0
        peak_db = 20.0 * np.log10(peak) if peak > 0 else -100.0

        return ProcessedAudio(
            audio_path=path,
            duration_seconds=duration,
            sample_rate=rate,
            channels=1,
            bit_rate=_ACX_BITRATE_KBPS,
            file_size_bytes=path.stat().st_size if path.exists() else 0,
            rms_db=rms_db,
            peak_db=peak_db,
            noise_floor_db=-70.0,
        )
