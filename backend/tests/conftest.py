# Backend Tests Configuration
import pytest
import os
from pathlib import Path

@pytest.fixture
def temp_audio_dir(tmp_path):
    """Create a temporary directory for audio files"""
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    return audio_dir

@pytest.fixture
def sample_audio_path(temp_audio_dir):
    """Create a sample WAV file for testing"""
    import numpy as np
    from scipy.io import wavfile
    
    # Generate 1 second of silence at 16kHz
    sample_rate = 16000
    duration = 1  # seconds
    samples = np.zeros(sample_rate * duration, dtype=np.int16)
    
    audio_path = temp_audio_dir / "sample.wav"
    wavfile.write(str(audio_path), sample_rate, samples)
    
    return str(audio_path)

@pytest.fixture
def sample_mp3_path(temp_audio_dir):
    """Create a sample MP3 file for testing"""
    from pydub import AudioSegment
    from pydub.generators import Sine
    
    # Generate 1 second tone
    tone = Sine(440).to_audio_segment(duration=1000)
    mp3_path = temp_audio_dir / "sample.mp3"
    tone.export(str(mp3_path), format="mp3")
    
    return str(mp3_path)
