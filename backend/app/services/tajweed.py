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
MADD_LETTERS = {'ا', 'و', 'ي', 'ى'}
GHUNNAH_LETTERS = {'ن', 'م'}
QALQALAH_LETTERS = {'ق', 'ط', 'ب', 'ج', 'د'}
HEAVY_LETTERS = {'خ', 'ص', 'ض', 'غ', 'ط', 'ق', 'ظ'}  # Tafkheem
LIGHT_LETTERS = set('بتثجحدذرزسشعفكلمنهوي')  # Tarqeeq

# Common letter confusions (for substitution detection)
SIMILAR_LETTERS = {
    'ق': ['ك', 'غ'],
    'ط': ['ت', 'د'],
    'ص': ['س', 'ز'],
    'ض': ['د', 'ظ'],
    'ظ': ['ذ', 'ض'],
    'ع': ['ا', 'ء'],
    'ح': ['ه', 'خ'],
    'ذ': ['ز', 'ظ'],
    'ث': ['س', 'ت'],
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
    'ق': "Press back of tongue against soft palate. Different from ك which uses middle of tongue.",
    'ط': "Press tongue tip behind upper teeth with full mouth (heavy). Different from ت which is light.",
    'ص': "Same position as س but with full/heavy mouth.",
    'ض': "Unique to Arabic. Press tongue sides against upper molars.",
    'ظ': "Like ذ but heavy/thick sound.",
    'ع': "Deep throat sound from pharynx. Not a glottal stop like ء.",
    'ح': "Voiceless pharyngeal. Deeper than ه, not as deep as ع.",
}


def analyze_tajweed(
    audio_path: str,
    matched_ayah: Dict[str, Any],
    segments: List[Dict[str, Any]]
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
    logger.info(f"Analyzing tajweed for Surah {matched_ayah['surah']}, Ayah {matched_ayah['ayah']}")
    
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
    missing_errors = detect_missing_words(
        transcribed_words, expected_words, segments
    )
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
            "match_confidence": matched_ayah.get("confidence", 0)
        }
    }


def detect_substituted_letters(
    transcribed_words: List[Dict],
    expected_words: List[str],
    segments: List[Dict]
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
        for j, (exp_char, trans_char) in enumerate(
            zip(expected_word, transcribed)
        ):
            # Skip diacritics
            if is_diacritic(exp_char) or is_diacritic(trans_char):
                continue
                
            if exp_char != trans_char:
                # Check if it's a known confusion
                if exp_char in SIMILAR_LETTERS and trans_char in SIMILAR_LETTERS.get(exp_char, []):
                    tip = LETTER_TIPS.get(exp_char, "Practice this letter carefully.")
                    
                    # Get timing from transcribed word
                    word_info = transcribed_words[i] if i < len(transcribed_words) else {}
                    
                    errors.append(TajweedError(
                        type=TajweedErrorType.SUBSTITUTED_LETTER,
                        letter=exp_char,
                        expected=exp_char,
                        detected=trans_char,
                        start_time=word_info.get("start", 0),
                        end_time=word_info.get("end", 0),
                        confidence=0.75,
                        suggestion=SUGGESTIONS[TajweedErrorType.SUBSTITUTED_LETTER].format(
                            expected=exp_char, detected=trans_char, tip=tip
                        ),
                        correction_audio_url=get_correction_url(exp_char),
                        word_index=i,
                        severity="high"
                    ))
    
    return errors


def detect_missing_words(
    transcribed_words: List[Dict],
    expected_words: List[str],
    segments: List[Dict]
) -> List[TajweedError]:
    """
    Detect words that are missing from the recitation.
    """
    errors = []
    
    transcribed_texts = [w.get("word", "") for w in transcribed_words]
    
    # Simple check: if expected word count > transcribed word count
    if len(expected_words) > len(transcribed_texts):
        for i in range(len(transcribed_texts), len(expected_words)):
            errors.append(TajweedError(
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
                severity="high"
            ))
    
    return errors


def detect_madd_errors(
    audio_path: str,
    expected_text: str,
    segments: List[Dict]
) -> List[TajweedError]:
    """
    Detect madd (elongation) errors.
    
    Checks if madd letters are held for appropriate duration.
    - Natural madd: 2 counts (~0.4-0.5s)
    - Connected madd: 4-5 counts
    - Required madd: 6 counts
    """
    errors = []
    
    # Find madd positions in expected text
    for i, char in enumerate(expected_text):
        if char in MADD_LETTERS:
            # Get corresponding segment timing
            # This is simplified - real implementation needs precise alignment
            
            # For MVP, we'll mark potential madd positions
            # Full implementation requires audio duration analysis
            pass
    
    # Mock error for demonstration
    # In production, analyze actual audio durations
    
    return errors


def detect_ghunnah_errors(
    audio_path: str,
    expected_text: str,
    segments: List[Dict]
) -> List[TajweedError]:
    """
    Detect ghunnah (nasalization) errors.
    
    Ghunnah is required on noon and meem in certain positions,
    especially with tashdeed (shadda).
    """
    errors = []
    
    # Find positions requiring ghunnah
    # Simplified: look for noon/meem with shadda
    
    return errors


def detect_qalqalah_errors(
    audio_path: str,
    expected_text: str,
    segments: List[Dict]
) -> List[TajweedError]:
    """
    Detect qalqalah errors.
    
    Qalqalah letters (ق ط ب ج د) require an echoing bounce
    when they have sukoon or at end of word.
    """
    errors = []
    
    # Find qalqalah positions
    # Simplified for MVP
    
    return errors


def is_diacritic(char: str) -> bool:
    """Check if character is an Arabic diacritic"""
    diacritics = set('\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0653\u0654\u0655\u0670')
    return char in diacritics


def get_correction_url(letter: str) -> str:
    """Get URL for correction audio for a letter"""
    letter_mapping = {
        'ق': 'qa_01',
        'ط': 'ta_emphatic_01',
        'ص': 'sad_01',
        'ض': 'dad_01',
        'ظ': 'dha_emphatic_01',
        'ع': 'ayn_01',
        'ح': 'ha_01',
    }
    
    correction_id = letter_mapping.get(letter, 'generic')
    return f"/api/v1/correction/audio/{correction_id}"


def calculate_score(errors: List[TajweedError], word_count: int) -> float:
    """
    Calculate overall score based on errors.
    
    Score is between 0.0 and 1.0.
    """
    if word_count == 0:
        return 0.0
    
    # Weight errors by severity
    severity_weights = {
        "high": 0.15,
        "medium": 0.08,
        "low": 0.03
    }
    
    total_penalty = sum(
        severity_weights.get(e.severity, 0.08) 
        for e in errors
    )
    
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
        return "Consider reviewing the basic rules of tajweed and practice with a teacher."


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
        "qalqalah_missing": "qalqalah bounce"
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
        "severity": error.severity
    }
