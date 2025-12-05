"""
Audio processing utilities
Normalize audio to standard format for ASR
"""

from pydub import AudioSegment
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Target audio format for ASR
TARGET_SAMPLE_RATE = 16000
TARGET_CHANNELS = 1
TARGET_SAMPLE_WIDTH = 2  # 16-bit


def normalize_audio_to_16k(input_path: str, output_path: str) -> str:
    """
    Normalize audio to 16kHz mono WAV format.

    Args:
        input_path: Path to input audio file (WAV, MP3, M4A, OGG, WEBM)
        output_path: Path for output normalized WAV file

    Returns:
        Path to normalized audio file
    """
    logger.info(f"Normalizing audio: {input_path} -> {output_path}")

    try:
        # Load audio file (pydub auto-detects format)
        audio = AudioSegment.from_file(input_path)

        # Log original format
        logger.info(
            f"Original: {audio.frame_rate}Hz, {audio.channels} channels, "
            f"{audio.sample_width * 8}-bit, {len(audio)}ms"
        )

        # Normalize to target format
        audio = audio.set_frame_rate(TARGET_SAMPLE_RATE)
        audio = audio.set_channels(TARGET_CHANNELS)
        audio = audio.set_sample_width(TARGET_SAMPLE_WIDTH)

        # Export as WAV
        audio.export(output_path, format="wav")

        logger.info(
            f"Normalized: {TARGET_SAMPLE_RATE}Hz, {TARGET_CHANNELS} channel, "
            f"{TARGET_SAMPLE_WIDTH * 8}-bit, {len(audio)}ms"
        )

        return output_path

    except Exception as e:
        logger.error(f"Audio normalization failed: {str(e)}")
        raise ValueError(f"Failed to normalize audio: {str(e)}")


def get_audio_duration(audio_path: str) -> float:
    """
    Get duration of audio file in seconds.
    """
    audio = AudioSegment.from_file(audio_path)
    return len(audio) / 1000.0  # Convert ms to seconds


def trim_audio(input_path: str, output_path: str, start_ms: int, end_ms: int) -> str:
    """
    Trim audio to specific time range.

    Useful for extracting segments for focused analysis.
    """
    audio = AudioSegment.from_file(input_path)
    trimmed = audio[start_ms:end_ms]
    trimmed.export(output_path, format="wav")
    return output_path


def get_audio_level(audio_path: str) -> dict:
    """
    Get audio level statistics for quality checking.
    """
    audio = AudioSegment.from_file(audio_path)

    return {
        "duration_ms": len(audio),
        "dBFS": audio.dBFS,  # Average loudness
        "max_dBFS": audio.max_dBFS,
        "rms": audio.rms,
        "is_too_quiet": audio.dBFS < -40,
        "is_too_loud": audio.max_dBFS > -1,
    }


def check_audio_quality(audio_path: str) -> dict:
    """
    Check audio quality and return recommendations.
    """
    stats = get_audio_level(audio_path)

    issues = []
    if stats["is_too_quiet"]:
        issues.append("Audio is too quiet. Please speak closer to the microphone.")
    if stats["is_too_loud"]:
        issues.append(
            "Audio is clipping. Please speak softer or move away from microphone."
        )
    if stats["duration_ms"] < 500:
        issues.append("Recording is too short. Please record at least 1 second.")
    if stats["duration_ms"] > 120000:
        issues.append("Recording is too long. Maximum duration is 2 minutes.")

    return {"is_acceptable": len(issues) == 0, "issues": issues, "stats": stats}
