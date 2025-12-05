"""
Test alignment and verse matching service
"""
import pytest
from app.services.alignment import (
    normalize_arabic_text,
    match_ayah,
    calculate_similarity,
    get_ayah_text,
    get_word_alignment
)


class TestAlignment:
    """Test verse alignment and matching"""
    
    def test_normalize_arabic_text_removes_diacritics(self):
        """Test that diacritics are removed from Arabic text"""
        text_with_diacritics = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
        normalized = normalize_arabic_text(text_with_diacritics)
        
        # Should not contain diacritics
        diacritics = ['\u064B', '\u064C', '\u064D', '\u064E', '\u064F', 
                      '\u0650', '\u0651', '\u0652', '\u0653', '\u0654']
        for diacritic in diacritics:
            assert diacritic not in normalized
    
    def test_normalize_arabic_text_preserves_letters(self):
        """Test that Arabic letters are preserved"""
        text = "بسم الله"
        normalized = normalize_arabic_text(text)
        
        # Should still contain Arabic letters
        assert len(normalized) > 0
        assert 'ب' in normalized or 'الله' in normalized
    
    def test_match_ayah_with_exact_match(self):
        """Test matching with exact ayah specification"""
        transcription = "بسم الله الرحمن الرحيم"
        
        result = match_ayah(transcription, surah=1, ayah=1)
        
        assert result['surah'] == 1
        assert result['ayah'] == 1
        assert result['confidence'] > 0.7  # Should have high confidence
    
    def test_match_ayah_without_specification(self):
        """Test matching without specifying surah/ayah"""
        transcription = "قل هو الله احد"
        
        result = match_ayah(transcription)
        
        # Should match Surah Al-Ikhlas (112:1)
        assert result['surah'] == 112
        assert result['ayah'] == 1
        assert result['confidence'] > 0.5
    
    def test_calculate_similarity_identical_texts(self):
        """Test similarity calculation for identical texts"""
        text1 = "بسم الله الرحمن الرحيم"
        text2 = "بسم الله الرحمن الرحيم"
        
        similarity = calculate_similarity(text1, text2)
        
        assert similarity == 1.0
    
    def test_calculate_similarity_different_texts(self):
        """Test similarity calculation for different texts"""
        text1 = "بسم الله"
        text2 = "قل هو الله"
        
        similarity = calculate_similarity(text1, text2)
        
        assert 0.0 <= similarity < 1.0
    
    def test_get_ayah_text_valid(self):
        """Test getting ayah text from database"""
        text = get_ayah_text(1, 1)
        
        assert text is not None
        assert len(text) > 0
        assert 'بسم' in text or 'بِسْمِ' in text
    
    def test_get_ayah_text_invalid_surah(self):
        """Test getting ayah with invalid surah number"""
        with pytest.raises(Exception):
            get_ayah_text(200, 1)
    
    def test_get_word_alignment_exact_match(self):
        """Test word alignment with exact match"""
        transcribed = ['بسم', 'الله', 'الرحمن']
        expected = ['بسم', 'الله', 'الرحمن']
        
        alignment = get_word_alignment(transcribed, expected)
        
        assert len(alignment) > 0
        # All should be matches
        matches = [a for a in alignment if a['type'] == 'match']
        assert len(matches) == 3
    
    def test_get_word_alignment_with_substitution(self):
        """Test word alignment with word substitution"""
        transcribed = ['بسم', 'لله', 'الرحمن']  # 'لله' instead of 'الله'
        expected = ['بسم', 'الله', 'الرحمن']
        
        alignment = get_word_alignment(transcribed, expected)
        
        # Should detect substitution
        substitutions = [a for a in alignment if a['type'] == 'substitute']
        assert len(substitutions) > 0
    
    def test_get_word_alignment_with_missing_word(self):
        """Test word alignment with missing word"""
        transcribed = ['بسم', 'الرحمن']  # Missing 'الله'
        expected = ['بسم', 'الله', 'الرحمن']
        
        alignment = get_word_alignment(transcribed, expected)
        
        # Should detect deletion
        deletions = [a for a in alignment if a['type'] == 'delete']
        assert len(deletions) > 0
