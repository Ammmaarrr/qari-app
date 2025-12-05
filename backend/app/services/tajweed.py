"""
Tajweed Analysis Service
Rule-based and ML-based tajweed error detection
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TajweedErrorType(str, Enum):
    """Types of tajweed errors"""

    SUBSTITUTED_LETTER = "substituted_letter"
    MISSING_WORD = "missing_word"
    MADD_SHORT = "madd_short"
    MADD_LONG = "madd_long"
    GHUNNAH_MISSING = "ghunnah_missing"
    GHUNNAH_SHORT = "ghunnah_short"
    QALQALAH_MISSING = "qalqalah_missing"
    QALQALAH_WEAK = "qalqalah_weak"
    IDGHAM_MISSING = "idgham_missing"
    IKHFA_MISSING = "ikhfa_missing"
    IQLAB_MISSING = "iqlab_missing"


@dataclass
class TajweedError:
    """Represents a detected tajweed error"""

    type: TajweedErrorType
    letter: Optional[str]
    expected: Optional[str]
    detected: Optional[str]
    start_time: float
    end_time: float
    confidence: float
    suggestion: str
    correction_audio_url: str
    word_index: Optional[int] = None
    severity: str = "medium"  # low, medium, high


# Letters that require specific tajweed rules
MADD_LETTERS = {"ا", "و", "ي", "ى"}
GHUNNAH_LETTERS = {"ن", "م"}
QALQALAH_LETTERS = {"ق", "ط", "ب", "ج", "د"}
HEAVY_LETTERS = {"خ", "ص", "ض", "غ", "ط", "ق", "ظ"}  # Tafkheem
LIGHT_LETTERS = set("بتثجحدذرزسشعفكلمنهوي")  # Tarqeeq

# Common letter confusions (for substitution detection)
SIMILAR_LETTERS = {
    "ق": ["ك", "غ"],
    "ط": ["ت", "د"],
    "ص": ["س", "ز"],
    "ض": ["د", "ظ"],
    "ظ": ["ذ", "ض"],
    "ع": ["ا", "ء"],
    "ح": ["ه", "خ"],
    "ذ": ["ز", "ظ"],
    "ث": ["س", "ت"],
}

# Suggestion templates
SUGGESTIONS = {
    TajweedErrorType.SUBSTITUTED_LETTER: "The letter '{expected}' was pronounced as '{detected}'. {tip}",
    TajweedErrorType.MISSING_WORD: "The word '{expected}' was not detected in your recitation.",
    TajweedErrorType.MADD_SHORT: "The madd (elongation) is too short. Hold the sound for {duration} counts.",
    TajweedErrorType.MADD_LONG: "The madd is too long. Reduce the elongation slightly.",
    TajweedErrorType.GHUNNAH_MISSING: "Ghunnah (nasalization) is required on '{letter}'. Let the sound resonate in the nose.",
    TajweedErrorType.GHUNNAH_SHORT: "The ghunnah is too short. Extend the nasal sound for 2 counts.",
    TajweedErrorType.QALQALAH_MISSING: "Qalqalah (echoing bounce) is required on '{letter}'. Add a slight bounce/echo.",
    TajweedErrorType.QALQALAH_WEAK: "The qalqalah on '{letter}' is too weak. Make the bounce clearer.",
}

# Letter pronunciation tips
LETTER_TIPS = {
    "ق": "Press back of tongue against soft palate. Different from ك which uses middle of tongue.",
    "ط": "Press tongue tip behind upper teeth with full mouth (heavy). Different from ت which is light.",
    "ص": "Same position as س but with full/heavy mouth.",
    "ض": "Unique to Arabic. Press tongue sides against upper molars.",
    "ظ": "Like ذ but heavy/thick sound.",
    "ع": "Deep throat sound from pharynx. Not a glottal stop like ء.",
    "ح": "Voiceless pharyngeal. Deeper than ه, not as deep as ع.",
}


def analyze_tajweed(
    audio_path: str, matched_ayah: Dict[str, Any], segments: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Main tajweed analysis function.

    Runs all detectors and aggregates results.

    Args:
        audio_path: Path to normalized audio file
        matched_ayah: Matched ayah info from alignment service
        segments: ASR segments with word timestamps

    Returns:
        Dict with errors, score, and recommendation
    """
    logger.info(
        f"Analyzing tajweed for Surah {matched_ayah['surah']}, Ayah {matched_ayah['ayah']}"
    )

    errors = []

    # Get expected text and words
    expected_text = matched_ayah.get("text", "")
    expected_words = expected_text.split()

    # Get transcribed words with timestamps
    transcribed_words = []
    for seg in segments:
        for word_info in seg.get("words", []):
            transcribed_words.append(word_info)

    # Run detectors

    # 1. Substituted letter detection (comparing transcription vs expected)
    substitution_errors = detect_substituted_letters(
        transcribed_words, expected_words, segments
    )
    errors.extend(substitution_errors)

    # 2. Missing word detection
    missing_errors = detect_missing_words(transcribed_words, expected_words, segments)
    errors.extend(missing_errors)

    # 3. Madd detection (requires audio analysis)
    madd_errors = detect_madd_errors(audio_path, expected_text, segments)
    errors.extend(madd_errors)

    # 4. Ghunnah detection
    ghunnah_errors = detect_ghunnah_errors(audio_path, expected_text, segments)
    errors.extend(ghunnah_errors)

    # 5. Qalqalah detection
    qalqalah_errors = detect_qalqalah_errors(audio_path, expected_text, segments)
    errors.extend(qalqalah_errors)

    # Calculate overall score
    score = calculate_score(errors, len(expected_words))

    # Generate recommendation
    recommendation = generate_recommendation(errors, score)

    return {
        "errors": [error_to_dict(e) for e in errors],
        "score": score,
        "recommendation": recommendation,
        "analysis_details": {
            "expected_words": len(expected_words),
            "detected_errors": len(errors),
            "match_confidence": matched_ayah.get("confidence", 0),
        },
    }


def detect_substituted_letters(
    transcribed_words: List[Dict], expected_words: List[str], segments: List[Dict]
) -> List[TajweedError]:
    """
    Detect letter substitutions by comparing transcription to expected.
    """
    errors = []

    # Simple word-level comparison for MVP
    # In production, use phoneme-level alignment
    transcribed_texts = [w.get("word", "") for w in transcribed_words]

    for i, expected_word in enumerate(expected_words):
        if i >= len(transcribed_texts):
            continue

        transcribed = transcribed_texts[i]

        # Check for character differences
        for j, (exp_char, trans_char) in enumerate(zip(expected_word, transcribed)):
            # Skip diacritics
            if is_diacritic(exp_char) or is_diacritic(trans_char):
                continue

            if exp_char != trans_char:
                # Check if it's a known confusion
                if exp_char in SIMILAR_LETTERS and trans_char in SIMILAR_LETTERS.get(
                    exp_char, []
                ):
                    tip = LETTER_TIPS.get(exp_char, "Practice this letter carefully.")

                    # Get timing from transcribed word
                    word_info = (
                        transcribed_words[i] if i < len(transcribed_words) else {}
                    )

                    errors.append(
                        TajweedError(
                            type=TajweedErrorType.SUBSTITUTED_LETTER,
                            letter=exp_char,
                            expected=exp_char,
                            detected=trans_char,
                            start_time=word_info.get("start", 0),
                            end_time=word_info.get("end", 0),
                            confidence=0.75,
                            suggestion=SUGGESTIONS[
                                TajweedErrorType.SUBSTITUTED_LETTER
                            ].format(expected=exp_char, detected=trans_char, tip=tip),
                            correction_audio_url=get_correction_url(exp_char),
                            word_index=i,
                            severity="high",
                        )
                    )

    return errors


def detect_missing_words(
    transcribed_words: List[Dict], expected_words: List[str], segments: List[Dict]
) -> List[TajweedError]:
    """
    Detect words that are missing from the recitation.
    """
    errors = []

    transcribed_texts = [w.get("word", "") for w in transcribed_words]

    # Simple check: if expected word count > transcribed word count
    if len(expected_words) > len(transcribed_texts):
        for i in range(len(transcribed_texts), len(expected_words)):
            errors.append(
                TajweedError(
                    type=TajweedErrorType.MISSING_WORD,
                    letter=None,
                    expected=expected_words[i],
                    detected=None,
                    start_time=0,
                    end_time=0,
                    confidence=0.8,
                    suggestion=SUGGESTIONS[TajweedErrorType.MISSING_WORD].format(
                        expected=expected_words[i]
                    ),
                    correction_audio_url="",
                    word_index=i,
                    severity="high",
                )
            )

    return errors


def detect_madd_errors(
    audio_path: str, expected_text: str, segments: List[Dict]
) -> List[TajweedError]:
    """
    Detect madd (elongation) errors.

    Checks if madd letters are held for appropriate duration.
    - Natural madd: 2 counts (~0.18-0.25s)
    - Connected madd: 4-5 counts (~0.36-0.5s)
    - Required madd: 6 counts (~0.5-0.6s)
    
    Uses librosa to analyze vowel duration in the audio.
    """
    errors = []
    
    # Thresholds in seconds
    MADD_SHORT_THRESHOLD = 0.15  # Too short
    MADD_NORMAL_MIN = 0.18
    MADD_NORMAL_MAX = 0.50
    MADD_LONG_THRESHOLD = 0.60  # Too long
    
    try:
        import librosa
        import numpy as np
        
        # Load audio
        y, sr = librosa.load(audio_path, sr=16000)
        
        # Get word timings from segments
        word_timings = []
        for seg in segments:
            for word_info in seg.get("words", []):
                word_timings.append({
                    "word": word_info.get("word", ""),
                    "start": word_info.get("start", 0),
                    "end": word_info.get("end", 0)
                })
        
        # Find madd positions in expected text
        expected_words = expected_text.split()
        
        for word_idx, word in enumerate(expected_words):
            # Check each character for madd letters
            for char_idx, char in enumerate(word):
                if char in MADD_LETTERS:
                    # Get timing for this word if available
                    if word_idx < len(word_timings):
                        word_info = word_timings[word_idx]
                        start_time = word_info["start"]
                        end_time = word_info["end"]
                        
                        # Calculate the approximate position of madd within word
                        word_duration = end_time - start_time
                        if word_duration > 0 and len(word) > 0:
                            # Estimate madd position proportionally
                            char_ratio = char_idx / len(word)
                            madd_start = start_time + (word_duration * char_ratio)
                            madd_end = madd_start + (word_duration / len(word))
                            
                            # Extract audio segment for madd
                            start_sample = int(madd_start * sr)
                            end_sample = int(madd_end * sr)
                            
                            if start_sample < len(y) and end_sample <= len(y):
                                madd_audio = y[start_sample:end_sample]
                                
                                # Analyze vowel duration using energy
                                if len(madd_audio) > 0:
                                    # Calculate RMS energy
                                    rms = librosa.feature.rms(y=madd_audio, frame_length=256, hop_length=64)[0]
                                    
                                    # Find sustained vowel duration (frames above threshold)
                                    threshold = np.mean(rms) * 0.5
                                    voiced_frames = np.sum(rms > threshold)
                                    duration = (voiced_frames * 64) / sr  # Convert to seconds
                                    
                                    # Check against thresholds
                                    if duration < MADD_SHORT_THRESHOLD:
                                        errors.append(
                                            TajweedError(
                                                type=TajweedErrorType.MADD_SHORT,
                                                letter=char,
                                                expected=f"{MADD_NORMAL_MIN}-{MADD_NORMAL_MAX}s",
                                                detected=f"{duration:.2f}s",
                                                start_time=madd_start,
                                                end_time=madd_end,
                                                confidence=0.75,
                                                suggestion=SUGGESTIONS[TajweedErrorType.MADD_SHORT].format(
                                                    duration="2-4"
                                                ),
                                                correction_audio_url="/api/v1/correction/audio/madd_example",
                                                word_index=word_idx,
                                                severity="medium",
                                            )
                                        )
                                    elif duration > MADD_LONG_THRESHOLD:
                                        errors.append(
                                            TajweedError(
                                                type=TajweedErrorType.MADD_LONG,
                                                letter=char,
                                                expected=f"{MADD_NORMAL_MIN}-{MADD_NORMAL_MAX}s",
                                                detected=f"{duration:.2f}s",
                                                start_time=madd_start,
                                                end_time=madd_end,
                                                confidence=0.70,
                                                suggestion=SUGGESTIONS[TajweedErrorType.MADD_LONG],
                                                correction_audio_url="/api/v1/correction/audio/madd_example",
                                                word_index=word_idx,
                                                severity="low",
                                            )
                                        )
                                        
    except ImportError:
        logger.warning("librosa not available for madd detection")
    except Exception as e:
        logger.error(f"Madd detection error: {e}")

    return errors


def detect_ghunnah_errors(
    audio_path: str, expected_text: str, segments: List[Dict]
) -> List[TajweedError]:
    """
    Detect ghunnah (nasalization) errors.

    Ghunnah is required on noon and meem in certain positions,
    especially with tashdeed (shadda). Duration should be ~0.12-0.2s.
    
    Uses spectral analysis to detect nasal frequency bands (250-450 Hz).
    """
    errors = []
    
    # Ghunnah thresholds
    GHUNNAH_MIN_DURATION = 0.12  # seconds
    GHUNNAH_NASAL_RATIO_THRESHOLD = 0.3  # minimum ratio of nasal energy
    
    # Arabic diacritics
    SHADDA = '\u0651'  # ّ
    SUKUN = '\u0652'  # ْ
    
    try:
        import librosa
        import numpy as np
        
        # Load audio
        y, sr = librosa.load(audio_path, sr=16000)
        
        # Get word timings from segments
        word_timings = []
        for seg in segments:
            for word_info in seg.get("words", []):
                word_timings.append({
                    "word": word_info.get("word", ""),
                    "start": word_info.get("start", 0),
                    "end": word_info.get("end", 0)
                })
        
        # Find positions requiring ghunnah (noon/meem with shadda or specific contexts)
        expected_words = expected_text.split()
        
        for word_idx, word in enumerate(expected_words):
            for char_idx, char in enumerate(word):
                requires_ghunnah = False
                
                # Check if it's noon or meem
                if char in GHUNNAH_LETTERS:
                    # Check if followed by shadda (mushaddad)
                    if char_idx + 1 < len(word) and word[char_idx + 1] == SHADDA:
                        requires_ghunnah = True
                    # Check if at word end with sukun (implied)
                    elif char_idx == len(word) - 1:
                        requires_ghunnah = True
                    # Check if followed by sukun
                    elif char_idx + 1 < len(word) and word[char_idx + 1] == SUKUN:
                        requires_ghunnah = True
                
                if requires_ghunnah and word_idx < len(word_timings):
                    word_info = word_timings[word_idx]
                    start_time = word_info["start"]
                    end_time = word_info["end"]
                    
                    word_duration = end_time - start_time
                    if word_duration > 0 and len(word) > 0:
                        # Estimate position of ghunnah letter
                        char_ratio = char_idx / len(word)
                        ghunnah_start = start_time + (word_duration * char_ratio)
                        ghunnah_end = min(ghunnah_start + 0.3, end_time)  # Max 300ms window
                        
                        # Extract audio segment
                        start_sample = int(ghunnah_start * sr)
                        end_sample = int(ghunnah_end * sr)
                        
                        if start_sample < len(y) and end_sample <= len(y):
                            ghunnah_audio = y[start_sample:end_sample]
                            
                            if len(ghunnah_audio) > 0:
                                # Compute spectrogram
                                S = np.abs(librosa.stft(ghunnah_audio, n_fft=512, hop_length=128))
                                freqs = librosa.fft_frequencies(sr=sr, n_fft=512)
                                
                                # Nasal frequency band (250-450 Hz typical for nasalization)
                                nasal_band_mask = (freqs >= 250) & (freqs <= 450)
                                total_band_mask = (freqs >= 100) & (freqs <= 2000)
                                
                                # Calculate energy in nasal band vs total
                                nasal_energy = np.mean(S[nasal_band_mask, :])
                                total_energy = np.mean(S[total_band_mask, :])
                                
                                if total_energy > 0:
                                    nasal_ratio = nasal_energy / total_energy
                                    
                                    # Calculate voiced duration
                                    rms = librosa.feature.rms(y=ghunnah_audio, frame_length=256, hop_length=64)[0]
                                    threshold = np.mean(rms) * 0.4
                                    voiced_frames = np.sum(rms > threshold)
                                    duration = (voiced_frames * 64) / sr
                                    
                                    # Check for ghunnah errors
                                    if nasal_ratio < GHUNNAH_NASAL_RATIO_THRESHOLD:
                                        errors.append(
                                            TajweedError(
                                                type=TajweedErrorType.GHUNNAH_MISSING,
                                                letter=char,
                                                expected="nasalization",
                                                detected="no nasalization",
                                                start_time=ghunnah_start,
                                                end_time=ghunnah_end,
                                                confidence=0.70,
                                                suggestion=SUGGESTIONS[TajweedErrorType.GHUNNAH_MISSING].format(
                                                    letter=char
                                                ),
                                                correction_audio_url="/api/v1/correction/audio/ghunnah_example",
                                                word_index=word_idx,
                                                severity="medium",
                                            )
                                        )
                                    elif duration < GHUNNAH_MIN_DURATION:
                                        errors.append(
                                            TajweedError(
                                                type=TajweedErrorType.GHUNNAH_SHORT,
                                                letter=char,
                                                expected=f">={GHUNNAH_MIN_DURATION}s",
                                                detected=f"{duration:.2f}s",
                                                start_time=ghunnah_start,
                                                end_time=ghunnah_end,
                                                confidence=0.65,
                                                suggestion=SUGGESTIONS[TajweedErrorType.GHUNNAH_SHORT],
                                                correction_audio_url="/api/v1/correction/audio/ghunnah_example",
                                                word_index=word_idx,
                                                severity="low",
                                            )
                                        )
                                        
    except ImportError:
        logger.warning("librosa not available for ghunnah detection")
    except Exception as e:
        logger.error(f"Ghunnah detection error: {e}")

    return errors


def detect_qalqalah_errors(
    audio_path: str, expected_text: str, segments: List[Dict]
) -> List[TajweedError]:
    """
    Detect qalqalah errors.

    Qalqalah letters (ق ط ب ج د) require an echoing bounce
    when they have sukoon or at end of word.
    
    Detects sudden amplitude rise/burst after the stop consonant.
    """
    errors = []
    
    # Qalqalah detection thresholds
    QALQALAH_BURST_THRESHOLD = 1.5  # Ratio of amplitude spike
    QALQALAH_MIN_ENERGY = 0.1  # Minimum energy for valid qalqalah
    
    # Arabic diacritics
    SUKUN = '\u0652'  # ْ
    
    try:
        import librosa
        import numpy as np
        
        # Load audio
        y, sr = librosa.load(audio_path, sr=16000)
        
        # Get word timings from segments
        word_timings = []
        for seg in segments:
            for word_info in seg.get("words", []):
                word_timings.append({
                    "word": word_info.get("word", ""),
                    "start": word_info.get("start", 0),
                    "end": word_info.get("end", 0)
                })
        
        expected_words = expected_text.split()
        
        for word_idx, word in enumerate(expected_words):
            for char_idx, char in enumerate(word):
                requires_qalqalah = False
                
                # Check if it's a qalqalah letter
                if char in QALQALAH_LETTERS:
                    # At end of word (sakin)
                    if char_idx == len(word) - 1:
                        requires_qalqalah = True
                    # Followed by sukun
                    elif char_idx + 1 < len(word) and word[char_idx + 1] == SUKUN:
                        requires_qalqalah = True
                    # Check if followed by another consonant (no vowel = implied sukun)
                    elif char_idx + 1 < len(word) and not is_diacritic(word[char_idx + 1]):
                        # Next char is consonant, check if there's a vowel between
                        requires_qalqalah = True
                
                if requires_qalqalah and word_idx < len(word_timings):
                    word_info = word_timings[word_idx]
                    start_time = word_info["start"]
                    end_time = word_info["end"]
                    
                    word_duration = end_time - start_time
                    if word_duration > 0 and len(word) > 0:
                        # Estimate position of qalqalah letter
                        char_ratio = char_idx / len(word)
                        qalqalah_start = start_time + (word_duration * char_ratio)
                        qalqalah_end = min(qalqalah_start + 0.15, end_time)  # 150ms window
                        
                        # Extract audio segment
                        start_sample = int(qalqalah_start * sr)
                        end_sample = int(qalqalah_end * sr)
                        
                        if start_sample < len(y) and end_sample <= len(y):
                            qalqalah_audio = y[start_sample:end_sample]
                            
                            if len(qalqalah_audio) > 256:  # Need enough samples
                                # Compute RMS envelope
                                rms = librosa.feature.rms(y=qalqalah_audio, frame_length=128, hop_length=32)[0]
                                
                                if len(rms) > 2:
                                    # Look for amplitude burst (sudden rise in energy)
                                    # Qalqalah creates a characteristic "bounce" pattern
                                    
                                    # Find peaks in the envelope
                                    peak_energy = np.max(rms)
                                    mean_energy = np.mean(rms)
                                    
                                    # Calculate onset strength (derivative of energy)
                                    onset_env = librosa.onset.onset_strength(y=qalqalah_audio, sr=sr, hop_length=32)
                                    onset_peak = np.max(onset_env) if len(onset_env) > 0 else 0
                                    onset_mean = np.mean(onset_env) if len(onset_env) > 0 else 1
                                    
                                    # Qalqalah should have sharp onset (bounce)
                                    burst_ratio = peak_energy / (mean_energy + 1e-6)
                                    onset_ratio = onset_peak / (onset_mean + 1e-6)
                                    
                                    # Check for missing qalqalah (no burst)
                                    if burst_ratio < QALQALAH_BURST_THRESHOLD and onset_ratio < 2.0:
                                        errors.append(
                                            TajweedError(
                                                type=TajweedErrorType.QALQALAH_MISSING,
                                                letter=char,
                                                expected="echoing bounce",
                                                detected="no bounce detected",
                                                start_time=qalqalah_start,
                                                end_time=qalqalah_end,
                                                confidence=0.65,
                                                suggestion=SUGGESTIONS[TajweedErrorType.QALQALAH_MISSING].format(
                                                    letter=char
                                                ),
                                                correction_audio_url="/api/v1/correction/audio/qalqalah_example",
                                                word_index=word_idx,
                                                severity="medium",
                                            )
                                        )
                                    elif peak_energy < QALQALAH_MIN_ENERGY:
                                        errors.append(
                                            TajweedError(
                                                type=TajweedErrorType.QALQALAH_WEAK,
                                                letter=char,
                                                expected="strong bounce",
                                                detected="weak bounce",
                                                start_time=qalqalah_start,
                                                end_time=qalqalah_end,
                                                confidence=0.60,
                                                suggestion=SUGGESTIONS[TajweedErrorType.QALQALAH_WEAK].format(
                                                    letter=char
                                                ),
                                                correction_audio_url="/api/v1/correction/audio/qalqalah_example",
                                                word_index=word_idx,
                                                severity="low",
                                            )
                                        )
                                        
    except ImportError:
        logger.warning("librosa not available for qalqalah detection")
    except Exception as e:
        logger.error(f"Qalqalah detection error: {e}")

    return errors


def is_diacritic(char: str) -> bool:
    """Check if character is an Arabic diacritic"""
    diacritics = set(
        "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0653\u0654\u0655\u0670"
    )
    return char in diacritics


def get_correction_url(letter: str) -> str:
    """Get URL for correction audio for a letter"""
    letter_mapping = {
        "ق": "qa_01",
        "ط": "ta_emphatic_01",
        "ص": "sad_01",
        "ض": "dad_01",
        "ظ": "dha_emphatic_01",
        "ع": "ayn_01",
        "ح": "ha_01",
    }

    correction_id = letter_mapping.get(letter, "generic")
    return f"/api/v1/correction/audio/{correction_id}"


def calculate_score(errors: List[TajweedError], word_count: int) -> float:
    """
    Calculate overall score based on errors.

    Score is between 0.0 and 1.0.
    """
    if word_count == 0:
        return 0.0

    # Weight errors by severity
    severity_weights = {"high": 0.15, "medium": 0.08, "low": 0.03}

    total_penalty = sum(severity_weights.get(e.severity, 0.08) for e in errors)

    # Ensure score is between 0 and 1
    score = max(0.0, min(1.0, 1.0 - total_penalty))

    return round(score, 2)


def generate_recommendation(errors: List[TajweedError], score: float) -> str:
    """
    Generate actionable recommendation based on analysis.
    """
    if score >= 0.95:
        return "Excellent recitation! Keep up the great work."
    elif score >= 0.85:
        return "Very good! Minor improvements possible."
    elif score >= 0.7:
        focus_areas = get_focus_areas(errors)
        return f"Good effort. Focus on: {focus_areas}"
    elif score >= 0.5:
        focus_areas = get_focus_areas(errors)
        return f"Needs practice. Key areas to improve: {focus_areas}"
    else:
        return (
            "Consider reviewing the basic rules of tajweed and practice with a teacher."
        )


def get_focus_areas(errors: List[TajweedError]) -> str:
    """Get main areas needing focus"""
    error_types = [e.type.value for e in errors]

    # Get most common error types
    from collections import Counter

    common = Counter(error_types).most_common(3)

    type_names = {
        "substituted_letter": "letter pronunciation",
        "missing_word": "complete recitation",
        "madd_short": "elongation (madd)",
        "ghunnah_missing": "nasalization (ghunnah)",
        "qalqalah_missing": "qalqalah bounce",
    }

    areas = [type_names.get(t, t) for t, _ in common]
    return ", ".join(areas) if areas else "general practice"


def error_to_dict(error: TajweedError) -> Dict[str, Any]:
    """Convert TajweedError to dictionary for JSON response"""
    return {
        "type": error.type.value,
        "letter": error.letter,
        "expected": error.expected,
        "detected": error.detected,
        "start_time": error.start_time,
        "end_time": error.end_time,
        "confidence": error.confidence,
        "suggestion": error.suggestion,
        "correction_audio_url": error.correction_audio_url,
        "word_index": error.word_index,
        "severity": error.severity,
    }
