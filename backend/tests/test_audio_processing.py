"""
Test audio processing utilities
"""

import pytest
import os
from pathlib import Path
from app.services.audio_processing import normalize_audio_to_16k


class TestAudioProcessing:
    """Test audio normalization and processing"""

    def test_normalize_audio_wav_to_wav(self, sample_audio_path, temp_audio_dir):
        """Test normalizing WAV file to 16kHz mono"""
        output_path = temp_audio_dir / "normalized.wav"

        # Normalize audio
        normalize_audio_to_16k(sample_audio_path, str(output_path))

        # Verify output exists
        assert output_path.exists()

        # Verify audio properties
        from pydub import AudioSegment

        audio = AudioSegment.from_wav(str(output_path))

        assert audio.frame_rate == 16000, "Sample rate should be 16kHz"
        assert audio.channels == 1, "Should be mono (single channel)"
        assert audio.sample_width == 2, "Should be 16-bit (2 bytes)"

    def test_normalize_audio_mp3_to_wav(self, sample_mp3_path, temp_audio_dir):
        """Test converting MP3 to normalized WAV"""
        output_path = temp_audio_dir / "normalized_from_mp3.wav"

        # Normalize audio
        normalize_audio_to_16k(sample_mp3_path, str(output_path))

        # Verify output exists and is WAV
        assert output_path.exists()

        from pydub import AudioSegment

        audio = AudioSegment.from_wav(str(output_path))

        assert audio.frame_rate == 16000
        assert audio.channels == 1

    def test_normalize_audio_preserves_content(self, sample_audio_path, temp_audio_dir):
        """Test that normalization preserves audio content (duration)"""
        output_path = temp_audio_dir / "normalized_preserve.wav"

        # Get original duration
        from pydub import AudioSegment

        original = AudioSegment.from_wav(sample_audio_path)
        original_duration = len(original)

        # Normalize
        normalize_audio_to_16k(sample_audio_path, str(output_path))

        # Check duration is similar (within 50ms tolerance)
        normalized = AudioSegment.from_wav(str(output_path))
        normalized_duration = len(normalized)

        assert (
            abs(normalized_duration - original_duration) < 50
        ), "Duration should be preserved within 50ms"

    def test_normalize_audio_invalid_input(self, temp_audio_dir):
        """Test handling of invalid input file"""
        invalid_path = temp_audio_dir / "nonexistent.wav"
        output_path = temp_audio_dir / "output.wav"

        with pytest.raises(Exception):
            normalize_audio_to_16k(str(invalid_path), str(output_path))
