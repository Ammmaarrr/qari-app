"""
Verse Alignment & Matching Service
Match transcription to Quran verses
"""
import logging
from typing import Dict, Any, Optional, List
import difflib
import re

logger = logging.getLogger(__name__)

# Quran text database - in production, load from proper database
# This is a sample with first few ayahs of Al-Fatiha
QURAN_DATABASE = {
    1: {  # Surah Al-Fatiha
        1: "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
        2: "الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ",
        3: "الرَّحْمَٰنِ الرَّحِيمِ",
        4: "مَالِكِ يَوْمِ الدِّينِ",
        5: "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ",
        6: "اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ",
        7: "صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ"
    },
    2: {  # Surah Al-Baqarah (first few ayahs)
        1: "الم",
        2: "ذَٰلِكَ الْكِتَابُ لَا رَيْبَ فِيهِ هُدًى لِلْمُتَّقِينَ",
        3: "الَّذِينَ يُؤْمِنُونَ بِالْغَيْبِ وَيُقِيمُونَ الصَّلَاةَ وَمِمَّا رَزَقْنَاهُمْ يُنْفِقُونَ",
    },
    112: {  # Surah Al-Ikhlas
        1: "قُلْ هُوَ اللَّهُ أَحَدٌ",
        2: "اللَّهُ الصَّمَدُ",
        3: "لَمْ يَلِدْ وَلَمْ يُولَدْ",
        4: "وَلَمْ يَكُنْ لَهُ كُفُوًا أَحَدٌ"
    },
    114: {  # Surah An-Nas
        1: "قُلْ أَعُوذُ بِرَبِّ النَّاسِ",
        2: "مَلِكِ النَّاسِ",
        3: "إِلَٰهِ النَّاسِ",
        4: "مِنْ شَرِّ الْوَسْوَاسِ الْخَنَّاسِ",
        5: "الَّذِي يُوَسْوِسُ فِي صُدُورِ النَّاسِ",
        6: "مِنَ الْجِنَّةِ وَالنَّاسِ"
    }
}


def normalize_arabic_text(text: str) -> str:
    """
    Normalize Arabic text for comparison.
    Removes diacritics and normalizes characters.
    """
    # Remove common diacritics
    diacritics = [
        '\u064B',  # Fathatan
        '\u064C',  # Dammatan
        '\u064D',  # Kasratan
        '\u064E',  # Fatha
        '\u064F',  # Damma
        '\u0650',  # Kasra
        '\u0651',  # Shadda
        '\u0652',  # Sukun
        '\u0653',  # Maddah
        '\u0654',  # Hamza above
        '\u0655',  # Hamza below
        '\u0670',  # Superscript Alef
    ]
    
    normalized = text
    for d in diacritics:
        normalized = normalized.replace(d, '')
    
    # Normalize Alef variants
    normalized = re.sub('[أإآا]', 'ا', normalized)
    
    # Normalize Yeh variants
    normalized = re.sub('[ىي]', 'ي', normalized)
    
    # Normalize Teh Marbuta
    normalized = normalized.replace('ة', 'ه')
    
    # Remove extra whitespace
    normalized = ' '.join(normalized.split())
    
    return normalized


def match_ayah(
    transcription: str,
    surah: Optional[int] = None,
    ayah: Optional[int] = None
) -> Dict[str, Any]:
    """
    Match transcription to Quran verse.
    
    If surah/ayah provided, compare against that specific verse.
    Otherwise, search for best match across database.
    
    Returns:
        Dict with surah, ayah, confidence, text, and alignment info
    """
    logger.info(f"Matching transcription to ayah (surah={surah}, ayah={ayah})")
    
    normalized_transcription = normalize_arabic_text(transcription)
    
    # If specific ayah provided, match against it
    if surah is not None and ayah is not None:
        if surah in QURAN_DATABASE and ayah in QURAN_DATABASE[surah]:
            expected_text = QURAN_DATABASE[surah][ayah]
            normalized_expected = normalize_arabic_text(expected_text)
            
            # Calculate similarity
            similarity = calculate_similarity(
                normalized_transcription, 
                normalized_expected
            )
            
            return {
                "surah": surah,
                "ayah": ayah,
                "confidence": similarity,
                "text": expected_text,
                "normalized_expected": normalized_expected,
                "normalized_transcription": normalized_transcription,
                "match_type": "exact_reference"
            }
        else:
            logger.warning(f"Surah {surah}, Ayah {ayah} not found in database")
    
    # Search for best match
    best_match = find_best_match(normalized_transcription)
    return best_match


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts using sequence matching.
    Returns value between 0.0 and 1.0.
    """
    # Use difflib for sequence matching
    matcher = difflib.SequenceMatcher(None, text1, text2)
    return matcher.ratio()


def find_best_match(
    transcription: str,
    search_surahs: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Find best matching ayah for transcription.
    
    Args:
        transcription: Normalized transcription text
        search_surahs: List of surah numbers to search (None = all)
    """
    best_match = {
        "surah": 1,
        "ayah": 1,
        "confidence": 0.0,
        "text": "",
        "match_type": "search"
    }
    
    surahs_to_search = search_surahs or list(QURAN_DATABASE.keys())
    
    for surah_num in surahs_to_search:
        if surah_num not in QURAN_DATABASE:
            continue
            
        for ayah_num, ayah_text in QURAN_DATABASE[surah_num].items():
            normalized_ayah = normalize_arabic_text(ayah_text)
            similarity = calculate_similarity(transcription, normalized_ayah)
            
            if similarity > best_match["confidence"]:
                best_match = {
                    "surah": surah_num,
                    "ayah": ayah_num,
                    "confidence": similarity,
                    "text": ayah_text,
                    "normalized_expected": normalized_ayah,
                    "match_type": "search"
                }
    
    logger.info(
        f"Best match: Surah {best_match['surah']}, "
        f"Ayah {best_match['ayah']}, "
        f"Confidence: {best_match['confidence']:.2f}"
    )
    
    return best_match


def get_word_alignment(
    transcribed_words: List[str],
    expected_words: List[str]
) -> List[Dict[str, Any]]:
    """
    Align transcribed words with expected words.
    
    Returns list of alignments showing matches, substitutions,
    insertions, and deletions.
    """
    matcher = difflib.SequenceMatcher(None, transcribed_words, expected_words)
    
    alignments = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1):
                alignments.append({
                    "type": "match",
                    "transcribed_index": i1 + k,
                    "expected_index": j1 + k,
                    "transcribed_word": transcribed_words[i1 + k],
                    "expected_word": expected_words[j1 + k]
                })
        elif tag == 'replace':
            for k in range(max(i2 - i1, j2 - j1)):
                t_idx = i1 + k if i1 + k < i2 else None
                e_idx = j1 + k if j1 + k < j2 else None
                alignments.append({
                    "type": "substitution",
                    "transcribed_index": t_idx,
                    "expected_index": e_idx,
                    "transcribed_word": transcribed_words[t_idx] if t_idx else None,
                    "expected_word": expected_words[e_idx] if e_idx else None
                })
        elif tag == 'delete':
            for k in range(i2 - i1):
                alignments.append({
                    "type": "insertion",  # Extra word in transcription
                    "transcribed_index": i1 + k,
                    "expected_index": None,
                    "transcribed_word": transcribed_words[i1 + k],
                    "expected_word": None
                })
        elif tag == 'insert':
            for k in range(j2 - j1):
                alignments.append({
                    "type": "deletion",  # Missing word from transcription
                    "transcribed_index": None,
                    "expected_index": j1 + k,
                    "transcribed_word": None,
                    "expected_word": expected_words[j1 + k]
                })
    
    return alignments


def get_ayah_text(surah: int, ayah: int) -> Optional[str]:
    """Get ayah text from database"""
    if surah in QURAN_DATABASE and ayah in QURAN_DATABASE[surah]:
        return QURAN_DATABASE[surah][ayah]
    return None
