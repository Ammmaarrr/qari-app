"""
Phoneme Utilities for Arabic Text Processing
Provides phoneme-level comparison for tajweed error detection
"""
from typing import List, Tuple, Dict
import difflib


# Arabic to phoneme mapping (simplified SAMPA-like representation)
ARABIC_PHONEMES = {
    # Consonants
    'ب': 'b',
    'ت': 't',
    'ث': 'th',
    'ج': 'j',
    'ح': 'H',
    'خ': 'x',
    'د': 'd',
    'ذ': 'dh',
    'ر': 'r',
    'ز': 'z',
    'س': 's',
    'ش': 'S',
    'ص': 's_',  # emphatic s
    'ض': 'd_',  # emphatic d
    'ط': 't_',  # emphatic t
    'ظ': 'dh_', # emphatic dh
    'ع': '?',   # pharyngeal
    'غ': 'G',
    'ف': 'f',
    'ق': 'q',
    'ك': 'k',
    'ل': 'l',
    'م': 'm',
    'ن': 'n',
    'ه': 'h',
    'و': 'w',
    'ي': 'y',
    'ء': "'",   # glottal stop
    'ئ': "'y",
    'ؤ': "'w",
    'أ': "'a",
    'إ': "'i",
    'آ': "'aa",
    # Vowels (as diacritics)
    'ا': 'aa',  # long a
    'ى': 'aa',  # alef maksura
    'ة': 'h',   # ta marbuta
}

# Arabic diacritics to vowel phonemes
DIACRITIC_PHONEMES = {
    '\u064e': 'a',   # fatha
    '\u064f': 'u',   # damma
    '\u0650': 'i',   # kasra
    '\u064b': 'an',  # fathatan
    '\u064c': 'un',  # dammatan
    '\u064d': 'in',  # kasratan
    '\u0651': ':',   # shadda (gemination)
    '\u0652': '',    # sukun (no vowel)
    '\u0653': 'aa',  # maddah
    '\u0670': 'aa',  # superscript alef
}


def arabic_to_phonemes(text: str) -> List[str]:
    """
    Convert Arabic text to a list of phonemes.
    
    Args:
        text: Arabic text with or without diacritics
        
    Returns:
        List of phoneme strings
    """
    phonemes = []
    i = 0
    
    while i < len(text):
        char = text[i]
        
        # Skip whitespace
        if char.isspace():
            phonemes.append(' ')
            i += 1
            continue
        
        # Check for consonant
        if char in ARABIC_PHONEMES:
            phoneme = ARABIC_PHONEMES[char]
            
            # Check for following shadda (gemination)
            if i + 1 < len(text) and text[i + 1] == '\u0651':
                phoneme = phoneme + phoneme  # Double the consonant
                i += 1
            
            phonemes.append(phoneme)
            
        # Check for diacritic
        elif char in DIACRITIC_PHONEMES:
            phoneme = DIACRITIC_PHONEMES[char]
            if phoneme:  # Skip empty (sukun)
                phonemes.append(phoneme)
        
        i += 1
    
    return phonemes


def phoneme_levenshtein(phonemes1: List[str], phonemes2: List[str]) -> Tuple[int, List[Dict]]:
    """
    Compute Levenshtein distance between two phoneme sequences.
    Also returns the list of operations (substitutions, insertions, deletions).
    
    Returns:
        Tuple of (distance, operations_list)
    """
    m, n = len(phonemes1), len(phonemes2)
    
    # Create distance matrix
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Initialize base cases
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    
    # Fill the matrix
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if phonemes1[i-1] == phonemes2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(
                    dp[i-1][j],      # deletion
                    dp[i][j-1],      # insertion
                    dp[i-1][j-1]     # substitution
                )
    
    # Backtrack to find operations
    operations = []
    i, j = m, n
    
    while i > 0 or j > 0:
        if i > 0 and j > 0 and phonemes1[i-1] == phonemes2[j-1]:
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
            operations.append({
                'type': 'substitution',
                'index': i - 1,
                'expected': phonemes2[j-1],
                'detected': phonemes1[i-1]
            })
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
            operations.append({
                'type': 'insertion',
                'index': i - 1,
                'detected': phonemes1[i-1]
            })
            i -= 1
        elif j > 0 and dp[i][j] == dp[i][j-1] + 1:
            operations.append({
                'type': 'deletion',
                'index': j - 1,
                'expected': phonemes2[j-1]
            })
            j -= 1
        else:
            break
    
    operations.reverse()
    return dp[m][n], operations


def find_substitutions(
    transcribed_text: str, 
    expected_text: str
) -> List[Dict]:
    """
    Find phoneme substitutions between transcribed and expected text.
    
    Returns list of substitution errors with:
    - phoneme_index: position in phoneme sequence
    - expected: expected phoneme
    - detected: detected phoneme
    - confidence: estimated confidence
    """
    transcribed_phonemes = arabic_to_phonemes(transcribed_text)
    expected_phonemes = arabic_to_phonemes(expected_text)
    
    distance, operations = phoneme_levenshtein(transcribed_phonemes, expected_phonemes)
    
    substitutions = []
    for op in operations:
        if op['type'] == 'substitution':
            # Map phoneme back to potential letter
            substitutions.append({
                'phoneme_index': op['index'],
                'expected_phoneme': op['expected'],
                'detected_phoneme': op['detected'],
                'confidence': 0.75 if are_similar_phonemes(op['expected'], op['detected']) else 0.85
            })
    
    return substitutions


def are_similar_phonemes(p1: str, p2: str) -> bool:
    """
    Check if two phonemes are commonly confused.
    """
    similar_pairs = [
        ('q', 'k'),     # ق vs ك
        ('t_', 't'),    # ط vs ت
        ('d_', 'd'),    # ض vs د
        ('s_', 's'),    # ص vs س
        ('dh_', 'dh'),  # ظ vs ذ
        ('H', 'h'),     # ح vs ه
        ('?', "'"),     # ع vs ء
        ('th', 's'),    # ث vs س
    ]
    
    for pair in similar_pairs:
        if (p1, p2) == pair or (p2, p1) == pair:
            return True
    return False


def phoneme_similarity(text1: str, text2: str) -> float:
    """
    Calculate phoneme-level similarity between two Arabic texts.
    Returns value between 0.0 and 1.0.
    """
    p1 = arabic_to_phonemes(text1)
    p2 = arabic_to_phonemes(text2)
    
    if not p1 or not p2:
        return 0.0
    
    distance, _ = phoneme_levenshtein(p1, p2)
    max_len = max(len(p1), len(p2))
    
    return 1.0 - (distance / max_len)
