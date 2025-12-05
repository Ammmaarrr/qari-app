from pathlib import Path
from pydub import AudioSegment

def normalize_audio(input_path: Path, output_path: Path) -> Path:
    """Normalize audio to single channel, 16kHz sample rate, 16-bit PCM WAV."""
    audio = AudioSegment.from_file(str(input_path))
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    audio.export(str(output_path), format="wav")
    return output_path

def get_audio_duration(audio_path: Path) -> float:
    """Get duration of audio file in seconds."""
    audio = AudioSegment.from_file(str(audio_path))
    return len(audio) / 1000.0
