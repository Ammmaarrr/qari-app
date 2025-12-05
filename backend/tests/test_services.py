"""
Backend Unit Tests
Run with: pytest tests/ -v
"""
import pytest
from pathlib import Path
import sys

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAudioProcessing:
    """Tests for audio processing utilities"""
    
    def test_normalize_audio_function_exists(self):
        """Test that normalize_audio_to_16k function is importable"""
        from app.services.audio_processing import normalize_audio_to_16k
        assert callable(normalize_audio_to_16k)
    
    def test_get_audio_duration_function_exists(self):
        """Test that get_audio_duration function is importable"""
        from app.services.audio_processing import get_audio_duration
        assert callable(get_audio_duration)
    
    def test_check_audio_quality_function_exists(self):
        """Test that check_audio_quality function is importable"""
        from app.services.audio_processing import check_audio_quality
        assert callable(check_audio_quality)


class TestASRService:
    """Tests for ASR transcription service"""
    
    def test_transcribe_function_exists(self):
        """Test that transcribe function is importable"""
        from app.services.asr_service import transcribe
        assert callable(transcribe)
    
    def test_mock_transcription_returns_tuple(self):
        """Test mock transcription returns expected format"""
        from app.services.asr_service import _mock_transcription
        text, segments = _mock_transcription()
        
        assert isinstance(text, str)
        assert len(text) > 0
        assert isinstance(segments, list)
        assert len(segments) > 0
        
        # Check segment structure
        seg = segments[0]
        assert "id" in seg
        assert "start" in seg
        assert "end" in seg
        assert "text" in seg
        assert "words" in seg
    
    def test_get_phonetic_transcription(self):
        """Test phonetic transcription conversion"""
        from app.services.asr_service import get_phonetic_transcription
        
        result = get_phonetic_transcription("بسم")
        assert isinstance(result, str)
        assert len(result) > 0


class TestAlignment:
    """Tests for verse alignment service"""
    
    def test_normalize_arabic_text(self):
        """Test Arabic text normalization"""
        from app.services.alignment import normalize_arabic_text
        
        # Test diacritic removal
        text_with_diacritics = "بِسْمِ"
        normalized = normalize_arabic_text(text_with_diacritics)
        assert isinstance(normalized, str)
    
    def test_calculate_similarity(self):
        """Test similarity calculation"""
        from app.services.alignment import calculate_similarity
        
        # Identical texts should have similarity 1.0
        sim = calculate_similarity("test", "test")
        assert sim == 1.0
        
        # Different texts should have lower similarity
        sim = calculate_similarity("test", "different")
        assert sim < 1.0
        assert sim >= 0.0
    
    def test_match_ayah_with_known_surah(self):
        """Test ayah matching with known surah"""
        from app.services.alignment import match_ayah
        
        # Test with Surah Al-Fatiha
        result = match_ayah("بسم الله الرحمن الرحيم", surah=1, ayah=1)
        
        assert "surah" in result
        assert "ayah" in result
        assert "confidence" in result
        assert result["surah"] == 1
        assert result["ayah"] == 1
    
    def test_get_ayah_text(self):
        """Test getting ayah text from database"""
        from app.services.alignment import get_ayah_text
        
        # Al-Fatiha, Ayah 1
        text = get_ayah_text(1, 1)
        assert text is not None
        assert len(text) > 0
        
        # Non-existent surah
        text = get_ayah_text(999, 1)
        assert text is None


class TestTajweed:
    """Tests for tajweed analysis service"""
    
    def test_tajweed_error_types_exist(self):
        """Test that error types are defined"""
        from app.services.tajweed import TajweedErrorType
        
        assert hasattr(TajweedErrorType, 'SUBSTITUTED_LETTER')
        assert hasattr(TajweedErrorType, 'MISSING_WORD')
        assert hasattr(TajweedErrorType, 'MADD_SHORT')
        assert hasattr(TajweedErrorType, 'GHUNNAH_MISSING')
        assert hasattr(TajweedErrorType, 'QALQALAH_MISSING')
    
    def test_analyze_tajweed_returns_expected_structure(self):
        """Test that analyze_tajweed returns expected structure"""
        from app.services.tajweed import analyze_tajweed
        
        # Mock inputs
        matched_ayah = {
            "surah": 1,
            "ayah": 1,
            "text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
            "confidence": 0.9
        }
        segments = [
            {
                "id": 0,
                "start": 0.0,
                "end": 3.0,
                "text": "بسم الله الرحمن الرحيم",
                "words": [
                    {"word": "بسم", "start": 0.0, "end": 0.5},
                    {"word": "الله", "start": 0.5, "end": 1.0},
                    {"word": "الرحمن", "start": 1.0, "end": 2.0},
                    {"word": "الرحيم", "start": 2.0, "end": 3.0},
                ]
            }
        ]
        
        result = analyze_tajweed("/fake/path.wav", matched_ayah, segments)
        
        assert "errors" in result
        assert "score" in result
        assert "recommendation" in result
        assert isinstance(result["errors"], list)
        assert isinstance(result["score"], float)
        assert 0.0 <= result["score"] <= 1.0
    
    def test_calculate_score(self):
        """Test score calculation"""
        from app.services.tajweed import calculate_score, TajweedError, TajweedErrorType
        
        # No errors should give perfect score
        score = calculate_score([], 10)
        assert score == 1.0
        
        # With errors, score should be lower
        errors = [
            TajweedError(
                type=TajweedErrorType.SUBSTITUTED_LETTER,
                letter="ق",
                expected="ق",
                detected="ك",
                start_time=0.0,
                end_time=0.5,
                confidence=0.8,
                suggestion="Test",
                correction_audio_url="",
                severity="high"
            )
        ]
        score = calculate_score(errors, 10)
        assert score < 1.0


class TestConfig:
    """Tests for configuration"""
    
    def test_settings_load(self):
        """Test that settings can be loaded"""
        from app.config import settings
        
        assert hasattr(settings, 'ENVIRONMENT')
        assert hasattr(settings, 'HOST')
        assert hasattr(settings, 'PORT')
        assert hasattr(settings, 'CONFIDENCE_THRESHOLD')
    
    def test_tajweed_thresholds(self):
        """Test that tajweed thresholds are set"""
        from app.config import settings
        
        assert settings.MADD_SHORT_THRESHOLD > 0
        assert settings.GHUNNAH_MIN_DURATION > 0
        assert 0 < settings.CONFIDENCE_THRESHOLD < 1


class TestAPIRoutes:
    """Tests for API routes structure"""
    
    def test_analyze_route_exists(self):
        """Test that analyze route module is importable"""
        from app.routes import analyze
        assert hasattr(analyze, 'router')
    
    def test_corrections_route_exists(self):
        """Test that corrections route module is importable"""
        from app.routes import corrections
        assert hasattr(corrections, 'router')
    
    def test_feedback_route_exists(self):
        """Test that feedback route module is importable"""
        from app.routes import feedback
        assert hasattr(feedback, 'router')
    
    def test_health_route_exists(self):
        """Test that health route module is importable"""
        from app.routes import health
        assert hasattr(health, 'router')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
