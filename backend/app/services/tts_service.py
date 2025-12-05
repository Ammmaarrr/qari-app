"""
Text-to-Speech service for generating correction audio
Uses gTTS for Arabic speech synthesis
"""

import os
import hashlib
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Audio cache directory
AUDIO_CACHE_DIR = Path("audio_cache")
AUDIO_CACHE_DIR.mkdir(exist_ok=True)


def get_cache_path(text: str, lang: str = "ar") -> Path:
    """Generate cache file path based on text hash."""
    text_hash = hashlib.md5(f"{text}_{lang}".encode()).hexdigest()
    return AUDIO_CACHE_DIR / f"{text_hash}.mp3"


def generate_audio(text: str, lang: str = "ar") -> Optional[str]:
    """
    Generate audio file from text using gTTS.
    Returns the file path or None if generation fails.
    """
    cache_path = get_cache_path(text, lang)

    # Return cached file if exists
    if cache_path.exists():
        return str(cache_path)

    try:
        from gtts import gTTS

        tts = gTTS(text=text, lang=lang, slow=True)
        tts.save(str(cache_path))
        logger.info(f"Generated audio for: {text[:50]}...")
        return str(cache_path)

    except ImportError:
        logger.warning("gTTS not installed, using mock audio")
        return None
    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        return None


def generate_correction_audio(
    error_type: str,
    correct_text: str,
    explanation: str,
) -> dict:
    """
    Generate correction audio with explanation.
    Returns dict with audio URLs for different parts.
    """
    result = {
        "correct_pronunciation": None,
        "explanation": None,
        "full_correction": None,
    }

    # Generate correct pronunciation
    result["correct_pronunciation"] = generate_audio(correct_text, "ar")

    # Generate explanation in Arabic
    result["explanation"] = generate_audio(explanation, "ar")

    # Generate full correction (combined)
    full_text = f"{explanation}. {correct_text}"
    result["full_correction"] = generate_audio(full_text, "ar")

    return result


# Pre-defined correction phrases for common errors
CORRECTION_PHRASES = {
    "substituted_letter": {
        "ق": {
            "correct": "قُلْ",
            "explanation": "حرف القاف يخرج من أقصى اللسان مع أعلى الحنك",
        },
        "ض": {
            "correct": "الضَّالِّين",
            "explanation": "حرف الضاد يخرج من إحدى حافتي اللسان مع ما يليها من الأضراس",
        },
        "ع": {
            "correct": "أَعُوذُ",
            "explanation": "حرف العين يخرج من وسط الحلق",
        },
        "ح": {
            "correct": "الرَّحْمَن",
            "explanation": "حرف الحاء يخرج من وسط الحلق",
        },
        "ط": {
            "correct": "طَرِيق",
            "explanation": "حرف الطاء يخرج من طرف اللسان مع أصول الثنايا العليا",
        },
    },
    "madd_short": {
        "explanation": "المد الطبيعي مقداره حركتان",
        "example": "قَالُوا",
    },
    "madd_long": {
        "explanation": "المد المتصل أو المنفصل يمد أربع إلى ست حركات",
        "example": "جَاءَ",
    },
    "ghunnah_missing": {
        "explanation": "الغنة صوت يخرج من الخيشوم مقداره حركتان",
        "example": "إِنَّ",
    },
    "qalqalah_missing": {
        "explanation": "القلقلة هي اضطراب صوت الحرف عند النطق به ساكناً",
        "letters": "ق ط ب ج د",
        "example": "يَجْعَل",
    },
    "idgham_missing": {
        "explanation": "الإدغام هو إدخال حرف ساكن في حرف متحرك",
        "example": "مِن رَّبِّهِم",
    },
}


def get_correction_for_error(error_type: str, details: dict = None) -> dict:
    """
    Get correction audio and text for a specific error type.
    """
    correction = {
        "text": "",
        "audio_url": None,
        "explanation": "",
        "example": "",
    }

    if error_type == "substituted_letter" and details:
        letter = details.get("expected", "")
        if letter in CORRECTION_PHRASES["substituted_letter"]:
            phrase = CORRECTION_PHRASES["substituted_letter"][letter]
            correction["text"] = phrase["correct"]
            correction["explanation"] = phrase["explanation"]

            # Generate audio
            audio_path = generate_audio(phrase["correct"], "ar")
            if audio_path:
                correction["audio_url"] = (
                    f"/api/v1/audio/{os.path.basename(audio_path)}"
                )

    elif error_type in CORRECTION_PHRASES:
        phrase = CORRECTION_PHRASES[error_type]
        correction["explanation"] = phrase.get("explanation", "")
        correction["example"] = phrase.get("example", "")

        if correction["example"]:
            audio_path = generate_audio(correction["example"], "ar")
            if audio_path:
                correction["audio_url"] = (
                    f"/api/v1/audio/{os.path.basename(audio_path)}"
                )

    return correction


def pregenerate_common_corrections():
    """Pre-generate audio for common corrections."""
    logger.info("Pre-generating common correction audio...")

    for error_type, data in CORRECTION_PHRASES.items():
        if error_type == "substituted_letter":
            for letter, phrase in data.items():
                generate_audio(phrase["correct"], "ar")
                generate_audio(phrase["explanation"], "ar")
        else:
            if "explanation" in data:
                generate_audio(data["explanation"], "ar")
            if "example" in data:
                generate_audio(data["example"], "ar")

    logger.info("Pre-generation complete")
