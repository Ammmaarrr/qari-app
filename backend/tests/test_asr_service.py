"""
Test ASR service
"""
import pytest
from unittest.mock import Mock, patch
from app.services.asr_service import transcribe


class TestASRService:
    """Test ASR transcription service"""
    
    @patch('app.services.asr_service.whisper')
    def test_transcribe_success(self, mock_whisper, sample_audio_path):
        """Test successful transcription"""
        # Mock Whisper response
        mock_result = {
            'text': 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ',
            'segments': [
                {
                    'text': 'بِسْمِ اللَّهِ',
                    'start': 0.0,
                    'end': 0.5,
                    'words': []
                },
                {
                    'text': 'الرَّحْمَٰنِ الرَّحِيمِ',
                    'start': 0.5,
                    'end': 1.2,
                    'words': []
                }
            ]
        }
        
        mock_whisper.load_model.return_value.transcribe.return_value = mock_result
        
        # Call transcribe
        text, segments = transcribe(sample_audio_path)
        
        # Verify results
        assert text == 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ'
        assert len(segments) == 2
        assert segments[0]['start'] == 0.0
        assert segments[0]['end'] == 0.5
    
    @patch('app.services.asr_service.whisper')
    def test_transcribe_empty_audio(self, mock_whisper, sample_audio_path):
        """Test transcription of silent/empty audio"""
        # Mock empty transcription
        mock_result = {
            'text': '',
            'segments': []
        }
        
        mock_whisper.load_model.return_value.transcribe.return_value = mock_result
        
        text, segments = transcribe(sample_audio_path)
        
        assert text == ''
        assert len(segments) == 0
    
    def test_transcribe_invalid_path(self):
        """Test transcription with invalid file path"""
        with pytest.raises(Exception):
            transcribe("/nonexistent/file.wav")
    
    @patch('app.services.asr_service.whisper')
    def test_transcribe_returns_timestamps(self, mock_whisper, sample_audio_path):
        """Test that transcription includes word-level timestamps"""
        mock_result = {
            'text': 'بِسْمِ اللَّهِ',
            'segments': [
                {
                    'text': 'بِسْمِ اللَّهِ',
                    'start': 0.0,
                    'end': 0.8,
                    'words': [
                        {'word': 'بِسْمِ', 'start': 0.0, 'end': 0.4},
                        {'word': 'اللَّهِ', 'start': 0.4, 'end': 0.8}
                    ]
                }
            ]
        }
        
        mock_whisper.load_model.return_value.transcribe.return_value = mock_result
        
        text, segments = transcribe(sample_audio_path)
        
        # Verify word-level timestamps exist
        assert 'words' in segments[0]
        assert len(segments[0]['words']) == 2
        assert segments[0]['words'][0]['word'] == 'بِسْمِ'
