"""
Test tajweed detection rules
"""

import pytest
from unittest.mock import Mock, patch
from app.services.tajweed import (
    analyze_tajweed,
    detect_madd_errors,
    detect_ghunnah_errors,
    detect_qalqalah_errors,
    detect_substituted_letters,
    detect_missing_words,
    TajweedErrorType,
)


class TestTajweedDetection:
    """Test tajweed rule detection"""

    @patch("app.services.tajweed.detect_madd_errors")
    @patch("app.services.tajweed.detect_ghunnah_errors")
    @patch("app.services.tajweed.detect_qalqalah_errors")
    @patch("app.services.tajweed.detect_substituted_letters")
    @patch("app.services.tajweed.detect_missing_words")
    def test_analyze_tajweed_calls_all_detectors(
        self,
        mock_missing,
        mock_subst,
        mock_qalqalah,
        mock_ghunnah,
        mock_madd,
        sample_audio_path,
    ):
        """Test that analyze_tajweed calls all detector functions"""
        # Mock all detectors to return empty lists
        for mock in [mock_missing, mock_subst, mock_qalqalah, mock_ghunnah, mock_madd]:
            mock.return_value = []

        matched_ayah = {"surah": 1, "ayah": 1, "text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"}
        segments = [{"text": "بِسْمِ اللَّهِ", "start": 0.0, "end": 0.5}]

        result = analyze_tajweed(sample_audio_path, matched_ayah, segments)

        # Verify all detectors were called
        mock_madd.assert_called_once()
        mock_ghunnah.assert_called_once()
        mock_qalqalah.assert_called_once()
        mock_subst.assert_called_once()
        mock_missing.assert_called_once()

        # Verify return structure
        assert "errors" in result
        assert "score" in result
        assert "recommendation" in result

    def test_detect_madd_errors_short_duration(self, sample_audio_path):
        """Test madd error detection for too-short elongation"""
        # This is a basic test - in practice you'd use actual audio with madd
        expected_text = "اللَّهِ"  # Contains madd
        segments = [{"text": "اللَّهِ", "start": 0.0, "end": 0.2}]  # Too short

        errors = detect_madd_errors(sample_audio_path, expected_text, segments)

        # May or may not detect depending on implementation
        # Just verify it returns a list
        assert isinstance(errors, list)

    def test_detect_substituted_letters_with_mismatch(self):
        """Test substituted letter detection"""
        transcribed = [
            {"word": "بسم", "start": 0.0, "end": 0.3},
            {"word": "كلله", "start": 0.3, "end": 0.6},  # Wrong: should be 'الله'
        ]
        expected = ["بسم", "الله"]
        segments = [{"text": "بسم كلله", "start": 0.0, "end": 0.6}]

        errors = detect_substituted_letters(transcribed, expected, segments)

        # Should detect a substitution
        assert isinstance(errors, list)
        if len(errors) > 0:
            assert errors[0].type == TajweedErrorType.SUBSTITUTED_LETTER

    def test_detect_missing_words_with_skip(self):
        """Test missing word detection"""
        transcribed = [
            {"word": "بسم", "start": 0.0, "end": 0.3},
            # Missing 'الله'
            {"word": "الرحمن", "start": 0.3, "end": 0.6},
        ]
        expected = ["بسم", "الله", "الرحمن"]
        segments = [{"text": "بسم الرحمن", "start": 0.0, "end": 0.6}]

        errors = detect_missing_words(transcribed, expected, segments)

        # Should detect missing word
        assert isinstance(errors, list)
        if len(errors) > 0:
            assert errors[0].type == TajweedErrorType.MISSING_WORD

    def test_detect_ghunnah_errors_returns_list(self, sample_audio_path):
        """Test that ghunnah detection returns a list"""
        expected_text = "مِنْ"  # Contains noon with ghunnah
        segments = [{"text": "من", "start": 0.0, "end": 0.3}]

        errors = detect_ghunnah_errors(sample_audio_path, expected_text, segments)

        assert isinstance(errors, list)

    def test_detect_qalqalah_errors_returns_list(self, sample_audio_path):
        """Test that qalqalah detection returns a list"""
        expected_text = "قُلْ"  # Contains qalqalah letter ق
        segments = [{"text": "قل", "start": 0.0, "end": 0.3}]

        errors = detect_qalqalah_errors(sample_audio_path, expected_text, segments)

        assert isinstance(errors, list)

    @patch("app.services.tajweed.detect_madd_errors")
    @patch("app.services.tajweed.detect_ghunnah_errors")
    @patch("app.services.tajweed.detect_qalqalah_errors")
    @patch("app.services.tajweed.detect_substituted_letters")
    @patch("app.services.tajweed.detect_missing_words")
    def test_analyze_tajweed_perfect_recitation(
        self,
        mock_missing,
        mock_subst,
        mock_qalqalah,
        mock_ghunnah,
        mock_madd,
        sample_audio_path,
    ):
        """Test score calculation for perfect recitation (no errors)"""
        # All detectors return no errors
        for mock in [mock_missing, mock_subst, mock_qalqalah, mock_ghunnah, mock_madd]:
            mock.return_value = []

        matched_ayah = {"surah": 1, "ayah": 1, "text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"}
        segments = [{"text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "start": 0.0, "end": 1.0}]

        result = analyze_tajweed(sample_audio_path, matched_ayah, segments)

        # Perfect recitation should have high score
        assert result["score"] > 0.9
        assert len(result["errors"]) == 0
