"""Unit tests for AudioProcessor service.

Tests cover instantiation, ACX validation, loudness measurement,
normalization, waveform generation, silence detection, and format conversion.

The module is loaded directly from the file path to avoid triggering the
package __init__.py import chain which requires the full app to be wired up.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import soundfile as sf

# ---------------------------------------------------------------------------
# Direct module import — bypass app.services.voiceforge.__init__.py
# ---------------------------------------------------------------------------

_MODULE_PATH = Path(__file__).resolve().parents[2] / "app" / "services" / "voiceforge" / "audio_processor.py"

# Pre-register a stub for app.config so the module-level `from app.config
# import get_settings` inside AudioProcessor.__init__ works at import time.
_config_stub = type(sys)("app.config")
_config_stub.get_settings = MagicMock  # will be overridden per-test via fixture
sys.modules.setdefault("app.config", _config_stub)

_spec = importlib.util.spec_from_file_location(
    "app.services.voiceforge.audio_processor",
    str(_MODULE_PATH),
    submodule_search_locations=[],
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["app.services.voiceforge.audio_processor"] = _mod
_spec.loader.exec_module(_mod)

AudioProcessor = _mod.AudioProcessor
ACXValidationResult = _mod.ACXValidationResult
LoudnessMetrics = _mod.LoudnessMetrics
ProcessedAudio = _mod.ProcessedAudio
SilenceSegment = _mod.SilenceSegment
WaveformData = _mod.WaveformData

_ACX_SAMPLE_RATE: int = _mod._ACX_SAMPLE_RATE
_ACX_PEAK_DB_MAX: float = _mod._ACX_PEAK_DB_MAX
_ACX_RMS_DB_MIN: float = _mod._ACX_RMS_DB_MIN
_ACX_RMS_DB_MAX: float = _mod._ACX_RMS_DB_MAX
_ACX_NOISE_FLOOR_DB_MAX: float = _mod._ACX_NOISE_FLOOR_DB_MAX
_ACX_BITRATE_KBPS: int = _mod._ACX_BITRATE_KBPS

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def _mock_settings():
    """Patch get_settings so AudioProcessor can be instantiated without app config."""
    settings = MagicMock()
    settings.AUDIO_TEMP_DIR = str(Path(tempfile.gettempdir()) / "voiceforge_test_audio")
    # Patch directly on the loaded module object and on app.config stub
    original = getattr(_mod, "get_settings", None)
    _mock_fn = MagicMock(return_value=settings)
    _config_stub.get_settings = _mock_fn
    try:
        yield settings
    finally:
        if original is not None:
            _config_stub.get_settings = original


@pytest.fixture
def processor(_mock_settings) -> AudioProcessor:
    """Return an AudioProcessor with mocked settings."""
    return AudioProcessor()


@pytest.fixture
def sample_audio_data():
    """Generate a 1-second 440 Hz sine wave at 44100 Hz (mono, float32)."""
    sample_rate = _ACX_SAMPLE_RATE
    t = np.linspace(0, 1, sample_rate, dtype=np.float32)
    audio = 0.5 * np.sin(2 * np.pi * 440 * t)
    return audio, sample_rate


@pytest.fixture
def sample_wav(sample_audio_data, tmp_path) -> Path:
    """Write sample audio to a temporary WAV file and return its path."""
    audio, rate = sample_audio_data
    path = tmp_path / "test_audio.wav"
    sf.write(str(path), audio, rate)
    return path


@pytest.fixture
def silent_wav(tmp_path) -> Path:
    """Write a 2-second silent WAV file."""
    rate = _ACX_SAMPLE_RATE
    audio = np.zeros(rate * 2, dtype=np.float32)
    path = tmp_path / "silence.wav"
    sf.write(str(path), audio, rate)
    return path


@pytest.fixture
def loud_wav(tmp_path) -> Path:
    """Write a WAV that exceeds ACX peak and RMS limits (clipping-level sine)."""
    rate = _ACX_SAMPLE_RATE
    t = np.linspace(0, 1, rate, dtype=np.float32)
    # Full-scale sine (peak = 0 dB, RMS ~ -3 dB) — fails ACX peak/RMS
    audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    path = tmp_path / "loud.wav"
    sf.write(str(path), audio, rate)
    return path


@pytest.fixture
def quiet_wav(tmp_path) -> Path:
    """Write a very quiet WAV (RMS well below -23 dB)."""
    rate = _ACX_SAMPLE_RATE
    t = np.linspace(0, 1, rate, dtype=np.float32)
    audio = 0.001 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
    path = tmp_path / "quiet.wav"
    sf.write(str(path), audio, rate)
    return path


@pytest.fixture
def audio_with_silence(tmp_path) -> Path:
    """Audio with a clear silence gap in the middle.

    Structure: 0.5 s tone | 1 s silence | 0.5 s tone
    """
    rate = _ACX_SAMPLE_RATE
    t_tone = np.linspace(0, 0.5, rate // 2, dtype=np.float32)
    tone = 0.5 * np.sin(2 * np.pi * 440 * t_tone)
    silence = np.zeros(rate, dtype=np.float32)
    audio = np.concatenate([tone, silence, tone])
    path = tmp_path / "with_silence.wav"
    sf.write(str(path), audio, rate)
    return path


@pytest.fixture
def stereo_wav(tmp_path) -> Path:
    """Write a stereo WAV file to test mono conversion."""
    rate = _ACX_SAMPLE_RATE
    t = np.linspace(0, 1, rate, dtype=np.float32)
    left = 0.5 * np.sin(2 * np.pi * 440 * t)
    right = 0.3 * np.sin(2 * np.pi * 880 * t)
    stereo = np.column_stack([left, right])
    path = tmp_path / "stereo.wav"
    sf.write(str(path), stereo, rate)
    return path


@pytest.fixture
def short_wav(tmp_path) -> Path:
    """Write a very short WAV (50 ms) to test edge cases."""
    rate = _ACX_SAMPLE_RATE
    n_samples = int(rate * 0.05)
    t = np.linspace(0, 0.05, n_samples, dtype=np.float32)
    audio = 0.5 * np.sin(2 * np.pi * 440 * t)
    path = tmp_path / "short.wav"
    sf.write(str(path), audio, rate)
    return path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ffmpeg_available() -> bool:
    """Check whether ffmpeg is available on the system."""
    return shutil.which("ffmpeg") is not None


# ---------------------------------------------------------------------------
# Test: Instantiation
# ---------------------------------------------------------------------------


class TestAudioProcessorInit:
    """AudioProcessor instantiation."""

    def test_audio_processor_init(self, processor: AudioProcessor):
        """AudioProcessor can be instantiated with mocked settings."""
        assert processor is not None
        assert processor._temp_dir.exists()

    def test_temp_dir_created(self, processor: AudioProcessor):
        """Temp directory is created on init."""
        assert processor._temp_dir.is_dir()


# ---------------------------------------------------------------------------
# Test: ACX validation
# ---------------------------------------------------------------------------


class TestValidateACXSpecs:
    """ACX validation checks correct thresholds."""

    def test_validate_acx_specs(self, processor: AudioProcessor, sample_wav: Path):
        """validate_acx returns an ACXValidationResult with the expected checks."""
        result = processor.validate_acx(sample_wav)

        assert isinstance(result, ACXValidationResult)
        assert isinstance(result.overall_pass, bool)
        assert 0 <= result.score <= 100
        assert isinstance(result.checks, list)
        assert len(result.checks) >= 7

        # Verify all expected check names are present
        check_names = [c["name"] for c in result.checks]
        assert any("Format" in n for n in check_names)
        assert any("Sample Rate" in n for n in check_names)
        assert any("Channels" in n or "Mono" in n for n in check_names)
        assert any("Peak" in n for n in check_names)
        assert any("RMS" in n for n in check_names)
        assert any("Noise Floor" in n for n in check_names)
        assert any("Duration" in n for n in check_names)

    def test_validate_acx_check_structure(self, processor: AudioProcessor, sample_wav: Path):
        """Each check dict has the required keys."""
        result = processor.validate_acx(sample_wav)

        for check in result.checks:
            assert "name" in check
            assert "passed" in check
            assert "actual" in check
            assert "expected" in check
            assert "auto_fixable" in check
            assert check["passed"] is True or check["passed"] is False or isinstance(check["passed"], bool | np.bool_)

    def test_validate_acx_thresholds_peak(self, processor: AudioProcessor, loud_wav: Path):
        """Peak must be <= -3 dB — loud audio should fail."""
        result = processor.validate_acx(loud_wav)
        peak_check = next(c for c in result.checks if "Peak" in c["name"])
        # Full-scale sine has peak ~0 dB, which exceeds -3 dB
        assert not peak_check["passed"]

    def test_validate_acx_thresholds_rms_range(self, processor: AudioProcessor, quiet_wav: Path):
        """RMS must be between -23 and -18 dB — very quiet audio should fail."""
        result = processor.validate_acx(quiet_wav)
        rms_check = next(c for c in result.checks if "RMS" in c["name"])
        assert not rms_check["passed"]

    def test_validate_acx_thresholds_noise_floor(self, processor: AudioProcessor, sample_wav: Path):
        """Noise floor must be < -60 dB."""
        result = processor.validate_acx(sample_wav)
        nf_check = next(c for c in result.checks if "Noise Floor" in c["name"])
        assert isinstance(nf_check["passed"], bool | np.bool_)

    def test_validate_acx_thresholds_sample_rate(self, processor: AudioProcessor, sample_wav: Path):
        """Sample rate must be 44100 Hz."""
        result = processor.validate_acx(sample_wav)
        sr_check = next(c for c in result.checks if "Sample Rate" in c["name"])
        assert sr_check["passed"]
        assert sr_check["actual"] == str(_ACX_SAMPLE_RATE)

    def test_validate_acx_thresholds_mono(self, processor: AudioProcessor, sample_wav: Path):
        """Channels must be mono (1)."""
        result = processor.validate_acx(sample_wav)
        ch_check = next(c for c in result.checks if "Mono" in c["name"] or "Channel" in c["name"])
        assert ch_check["passed"]

    def test_validate_acx_format_wav_not_mp3(self, processor: AudioProcessor, sample_wav: Path):
        """WAV file should fail the MP3 format check."""
        result = processor.validate_acx(sample_wav)
        fmt_check = next(c for c in result.checks if "Format" in c["name"])
        assert not fmt_check["passed"]
        assert fmt_check["auto_fixable"]


class TestValidateACXPassFail:
    """Overall pass/fail behavior."""

    def test_validate_acx_failing(self, processor: AudioProcessor, loud_wav: Path):
        """Loud WAV should fail ACX validation with issues listed."""
        result = processor.validate_acx(loud_wav)
        assert not result.overall_pass
        assert result.score < 100
        # At minimum, format check fails (WAV not MP3) and peak exceeds -3 dB
        failing = [c for c in result.checks if not c["passed"]]
        assert len(failing) >= 2

    def test_validate_acx_auto_fixable_issues(self, processor: AudioProcessor, sample_wav: Path):
        """Auto-fixable issues should be listed for failing checks that support remediation."""
        result = processor.validate_acx(sample_wav)
        # WAV format is not MP3 — that is auto-fixable
        if not result.overall_pass:
            assert isinstance(result.auto_fixable_issues, list)
            assert any("Format" in issue for issue in result.auto_fixable_issues)


# ---------------------------------------------------------------------------
# Test: Normalization
# ---------------------------------------------------------------------------


class TestNormalize:
    """Normalize function behavior."""

    def test_normalize_returns_processed_audio(self, processor: AudioProcessor, sample_wav: Path):
        """normalize() returns a ProcessedAudio with a valid output path."""
        result = processor.normalize(sample_wav)
        assert isinstance(result, ProcessedAudio)
        assert result.audio_path.exists()
        assert result.sample_rate == _ACX_SAMPLE_RATE
        assert result.channels == 1

    def test_normalize_target_lufs(self, processor: AudioProcessor, sample_wav: Path):
        """Normalized audio should be close to the target RMS level."""
        target_rms = -20.0
        result = processor.normalize(sample_wav, target_rms=target_rms, target_peak=_ACX_PEAK_DB_MAX)

        # Read back the normalized audio and measure
        data, rate = sf.read(str(result.audio_path))
        rms = float(np.sqrt(np.mean(data**2)))
        rms_db = 20.0 * np.log10(rms) if rms > 0 else -100.0

        # Allow 3 dB tolerance (LUFS normalization isn't exact RMS)
        assert abs(rms_db - target_rms) < 3.0, f"Expected RMS ~{target_rms} dB, got {rms_db:.1f} dB"

    def test_normalize_peak_limiting(self, processor: AudioProcessor, loud_wav: Path):
        """Normalized audio should have peaks limited to target_peak."""
        target_peak = _ACX_PEAK_DB_MAX
        result = processor.normalize(loud_wav, target_rms=-20.0, target_peak=target_peak)

        data, rate = sf.read(str(result.audio_path))
        peak = float(np.max(np.abs(data)))
        peak_db = 20.0 * np.log10(peak) if peak > 0 else -100.0

        assert peak_db <= target_peak + 0.1, f"Peak {peak_db:.1f} dB exceeds target {target_peak} dB"

    def test_normalize_silent_audio(self, processor: AudioProcessor, silent_wav: Path):
        """Normalizing silent audio should not crash (LUFS = -inf edge case)."""
        result = processor.normalize(silent_wav)
        assert isinstance(result, ProcessedAudio)
        assert result.audio_path.exists()

    def test_normalize_stereo_input(self, processor: AudioProcessor, stereo_wav: Path):
        """Stereo input should be converted to mono during normalization."""
        result = processor.normalize(stereo_wav)
        data, rate = sf.read(str(result.audio_path))
        assert data.ndim == 1, "Normalized output should be mono"


# ---------------------------------------------------------------------------
# Test: Loudness measurement
# ---------------------------------------------------------------------------


class TestMeasureLoudness:
    """measure_loudness returns correct structure and reasonable values."""

    def test_loudness_metrics_structure(self, processor: AudioProcessor, sample_wav: Path):
        """measure_loudness returns a LoudnessMetrics with all fields."""
        metrics = processor.measure_loudness(sample_wav)

        assert isinstance(metrics, LoudnessMetrics)
        assert isinstance(metrics.rms_db, float)
        assert isinstance(metrics.peak_db, float)
        assert isinstance(metrics.noise_floor_db, float)
        assert isinstance(metrics.lufs, float)
        assert isinstance(metrics.dynamic_range_db, float)

    def test_loudness_metrics_values_reasonable(self, processor: AudioProcessor, sample_wav: Path):
        """Values for a 0.5-amplitude sine should be in expected ranges."""
        metrics = processor.measure_loudness(sample_wav)

        # 0.5 amplitude sine: peak ~-6 dB, RMS ~-9 dB
        assert -10.0 < metrics.peak_db < 0.0
        assert -15.0 < metrics.rms_db < -3.0
        assert metrics.dynamic_range_db > 0.0

    def test_loudness_metrics_silent_audio(self, processor: AudioProcessor, silent_wav: Path):
        """Silent audio should have very low metrics."""
        metrics = processor.measure_loudness(silent_wav)

        assert metrics.peak_db <= -90.0
        assert metrics.rms_db <= -90.0
        assert metrics.lufs <= -90.0

    def test_loudness_metrics_loud_audio(self, processor: AudioProcessor, loud_wav: Path):
        """Full-scale sine should have peak near 0 dB."""
        metrics = processor.measure_loudness(loud_wav)

        assert metrics.peak_db > -1.0  # Full-scale, very near 0 dB
        assert metrics.rms_db > -5.0

    def test_loudness_noise_floor_clean_sine(self, processor: AudioProcessor, sample_wav: Path):
        """A pure sine wave's noise floor tracks the quietest 10% of frames.

        For a continuous 0.5-amplitude sine at 440 Hz, even the quietest
        100 ms frames have substantial energy (~RMS of the signal), so
        the noise floor is close to the overall RMS rather than near silence.
        """
        metrics = processor.measure_loudness(sample_wav)
        # Noise floor should be finite and below or near the overall RMS
        assert metrics.noise_floor_db <= metrics.rms_db + 1.0
        assert metrics.noise_floor_db > -100.0


# ---------------------------------------------------------------------------
# Test: Waveform generation
# ---------------------------------------------------------------------------


class TestGenerateWaveform:
    """generate_waveform returns waveform data arrays."""

    def test_generate_waveform_returns_data(self, processor: AudioProcessor, sample_wav: Path):
        """generate_waveform returns a WaveformData with peaks."""
        waveform = processor.generate_waveform(sample_wav, resolution=100)

        assert isinstance(waveform, WaveformData)
        assert isinstance(waveform.peaks, list)
        assert len(waveform.peaks) == 100
        assert waveform.duration_seconds > 0
        assert waveform.sample_rate == _ACX_SAMPLE_RATE
        assert waveform.resolution == 100

    def test_generate_waveform_peak_range(self, processor: AudioProcessor, sample_wav: Path):
        """All peaks should be between 0 and 1 for normalized audio."""
        waveform = processor.generate_waveform(sample_wav, resolution=50)

        for peak in waveform.peaks:
            assert 0.0 <= peak <= 1.0, f"Peak {peak} out of [0, 1] range"

    def test_generate_waveform_silent_audio(self, processor: AudioProcessor, silent_wav: Path):
        """Silent audio should produce near-zero peaks."""
        waveform = processor.generate_waveform(silent_wav, resolution=50)

        for peak in waveform.peaks:
            assert peak < 0.001

    def test_generate_waveform_resolution(self, processor: AudioProcessor, sample_wav: Path):
        """Different resolutions produce different numbers of peaks."""
        wf_lo = processor.generate_waveform(sample_wav, resolution=50)
        wf_hi = processor.generate_waveform(sample_wav, resolution=500)

        assert wf_lo.resolution == 50
        assert wf_hi.resolution == 500
        assert len(wf_lo.peaks) < len(wf_hi.peaks)

    def test_generate_waveform_short_audio(self, processor: AudioProcessor, short_wav: Path):
        """Very short audio should still produce waveform data."""
        waveform = processor.generate_waveform(short_wav, resolution=10)
        assert isinstance(waveform, WaveformData)
        assert len(waveform.peaks) > 0


# ---------------------------------------------------------------------------
# Test: Silence detection
# ---------------------------------------------------------------------------


class TestSilenceDetection:
    """detect_silence finds silence segments correctly."""

    def test_silence_detection_finds_gap(self, processor: AudioProcessor, audio_with_silence: Path):
        """Detects the silent gap in audio_with_silence fixture."""
        segments = processor.detect_silence(audio_with_silence, threshold_db=-30.0, min_duration_seconds=0.5)

        assert isinstance(segments, list)
        assert len(segments) >= 1

        seg = segments[0]
        assert isinstance(seg, SilenceSegment)
        assert seg.duration_seconds >= 0.5

    def test_silence_detection_timing(self, processor: AudioProcessor, audio_with_silence: Path):
        """Silence segment start/end times are in the expected range."""
        segments = processor.detect_silence(audio_with_silence, threshold_db=-30.0, min_duration_seconds=0.5)

        assert len(segments) >= 1
        seg = segments[0]

        # Silence is in the middle: starts around 0.5 s, ends around 1.5 s
        assert 0.3 < seg.start_seconds < 0.7
        assert 1.3 < seg.end_seconds < 1.7

    def test_silence_detection_no_silence_in_tone(self, processor: AudioProcessor, sample_wav: Path):
        """Continuous tone should have no silence segments."""
        segments = processor.detect_silence(sample_wav, threshold_db=-40.0, min_duration_seconds=0.5)

        assert len(segments) == 0

    def test_silence_detection_all_silent(self, processor: AudioProcessor, silent_wav: Path):
        """Fully silent audio should detect the entire file as silence."""
        segments = processor.detect_silence(silent_wav, threshold_db=-40.0, min_duration_seconds=0.5)

        assert len(segments) >= 1
        total_silence = sum(s.duration_seconds for s in segments)
        # Should cover nearly the entire 2-second file
        assert total_silence > 1.5

    def test_silence_detection_min_duration_filter(self, processor: AudioProcessor, audio_with_silence: Path):
        """Short min_duration finds gaps; long min_duration may filter them out."""
        short_min = processor.detect_silence(
            audio_with_silence,
            threshold_db=-30.0,
            min_duration_seconds=0.3,
        )
        long_min = processor.detect_silence(
            audio_with_silence,
            threshold_db=-30.0,
            min_duration_seconds=5.0,
        )

        assert len(short_min) >= 1
        assert len(long_min) == 0

    def test_silence_detection_short_audio(self, processor: AudioProcessor, short_wav: Path):
        """Very short audio (50 ms tone) should not crash."""
        segments = processor.detect_silence(short_wav, threshold_db=-40.0, min_duration_seconds=0.01)
        assert isinstance(segments, list)


# ---------------------------------------------------------------------------
# Test: Format conversion
# ---------------------------------------------------------------------------


class TestFormatConversion:
    """convert_format converts between audio formats."""

    @pytest.mark.skipif(
        not _ffmpeg_available(),
        reason="ffmpeg not available in test environment",
    )
    def test_format_conversion_wav_to_mp3(self, processor: AudioProcessor, sample_wav: Path):
        """WAV can be converted to MP3."""
        result = processor.convert_format(sample_wav, target_format="mp3")

        assert isinstance(result, ProcessedAudio)
        assert result.audio_path.suffix == ".mp3"
        assert result.audio_path.exists()

    @pytest.mark.skipif(
        not _ffmpeg_available(),
        reason="ffmpeg not available in test environment",
    )
    def test_format_conversion_preserves_sample_rate(self, processor: AudioProcessor, sample_wav: Path):
        """Converted file should have the target sample rate."""
        result = processor.convert_format(
            sample_wav,
            target_format="mp3",
            sample_rate=_ACX_SAMPLE_RATE,
        )
        assert result.sample_rate == _ACX_SAMPLE_RATE

    def test_format_conversion_ffmpeg_error(self, processor: AudioProcessor, sample_wav: Path):
        """convert_format raises RuntimeError when ffmpeg fails."""
        import ffmpeg as _ffmpeg_mod

        mock_ffmpeg = MagicMock()
        mock_ffmpeg.input.return_value = MagicMock()
        mock_ffmpeg.output.return_value = MagicMock()
        mock_ffmpeg.run.side_effect = _ffmpeg_mod.Error("ffmpeg", b"", b"conversion failed")
        mock_ffmpeg.Error = _ffmpeg_mod.Error

        with patch.dict("sys.modules", {"ffmpeg": mock_ffmpeg}):
            with pytest.raises(RuntimeError, match="Audio format conversion failed"):
                processor.convert_format(sample_wav, target_format="mp3")


# ---------------------------------------------------------------------------
# Test: Other pipeline steps
# ---------------------------------------------------------------------------


class TestNoiseGate:
    """apply_noise_gate behavior."""

    def test_noise_gate_returns_processed_audio(self, processor: AudioProcessor, sample_wav: Path):
        result = processor.apply_noise_gate(sample_wav)
        assert isinstance(result, ProcessedAudio)
        assert result.audio_path.exists()

    def test_noise_gate_attenuates_quiet_sections(
        self,
        processor: AudioProcessor,
        audio_with_silence: Path,
    ):
        """Gated audio should have quieter silent sections than original."""
        result = processor.apply_noise_gate(
            audio_with_silence,
            threshold_db=-30.0,
        )
        original, _ = sf.read(str(audio_with_silence))
        gated, _ = sf.read(str(result.audio_path))

        # Measure energy in the silence region (samples 22050 to 66150 = 0.5s-1.5s)
        rate = _ACX_SAMPLE_RATE
        start = int(0.5 * rate)
        end = int(1.5 * rate)

        orig_rms = float(np.sqrt(np.mean(original[start:end] ** 2)))
        gated_rms = float(np.sqrt(np.mean(gated[start:end] ** 2)))

        # Gated silence should be no louder than original (already near zero)
        assert gated_rms <= orig_rms + 1e-6


class TestCompression:
    """apply_compression behavior."""

    def test_compression_returns_processed_audio(self, processor: AudioProcessor, sample_wav: Path):
        result = processor.apply_compression(sample_wav)
        assert isinstance(result, ProcessedAudio)
        assert result.audio_path.exists()

    def test_compression_reduces_dynamic_range(self, processor: AudioProcessor, loud_wav: Path):
        """Compression should reduce peak relative to RMS."""
        result = processor.apply_compression(loud_wav, ratio=4.0, threshold_db=-20.0)

        original, _ = sf.read(str(loud_wav))
        compressed, _ = sf.read(str(result.audio_path))

        orig_peak = float(np.max(np.abs(original)))
        comp_peak = float(np.max(np.abs(compressed)))

        # Compression should reduce (or at least not increase) peak
        assert comp_peak <= orig_peak + 1e-6


class TestEQ:
    """apply_eq behavior."""

    def test_eq_returns_processed_audio(self, processor: AudioProcessor, sample_wav: Path):
        result = processor.apply_eq(sample_wav)
        assert isinstance(result, ProcessedAudio)
        assert result.audio_path.exists()


class TestRoomTone:
    """add_room_tone behavior."""

    def test_room_tone_extends_duration(self, processor: AudioProcessor, sample_wav: Path):
        """Adding room tone should increase total duration."""
        head = 0.75
        tail = 3.0
        result = processor.add_room_tone(sample_wav, head_seconds=head, tail_seconds=tail)

        original, rate = sf.read(str(sample_wav))
        processed, _ = sf.read(str(result.audio_path))

        orig_dur = len(original) / rate
        proc_dur = len(processed) / rate

        expected_increase = head + tail
        assert proc_dur > orig_dur
        assert abs(proc_dur - orig_dur - expected_increase) < 0.01


# ---------------------------------------------------------------------------
# Test: Data class construction
# ---------------------------------------------------------------------------


class TestDataClasses:
    """Verify data class fields."""

    def test_processed_audio_fields(self):
        pa = ProcessedAudio(
            audio_path=Path("/tmp/test.wav"),
            duration_seconds=10.0,
            sample_rate=44100,
            channels=1,
            bit_rate=192,
            file_size_bytes=1000,
            rms_db=-20.0,
            peak_db=-3.0,
            noise_floor_db=-70.0,
        )
        assert pa.duration_seconds == 10.0
        assert pa.channels == 1
        assert pa.bit_rate == 192

    def test_loudness_metrics_fields(self):
        lm = LoudnessMetrics(
            rms_db=-20.0,
            peak_db=-3.0,
            noise_floor_db=-60.0,
            lufs=-19.0,
            dynamic_range_db=17.0,
        )
        assert lm.lufs == -19.0
        assert lm.dynamic_range_db == 17.0

    def test_acx_validation_result_fields(self):
        avr = ACXValidationResult(
            overall_pass=True,
            score=100,
            checks=[],
            auto_fixable_issues=[],
        )
        assert avr.overall_pass is True
        assert avr.score == 100

    def test_waveform_data_fields(self):
        wd = WaveformData(peaks=[0.1, 0.5, 0.3], duration_seconds=1.0, sample_rate=44100, resolution=3)
        assert len(wd.peaks) == 3
        assert wd.resolution == 3

    def test_silence_segment_fields(self):
        ss = SilenceSegment(start_seconds=1.0, end_seconds=2.0, duration_seconds=1.0)
        assert ss.duration_seconds == 1.0
