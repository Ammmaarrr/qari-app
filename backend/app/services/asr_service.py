"""
ASR (Automatic Speech Recognition) Service
Uses Whisper for Arabic transcription
"""
import logging
from typing import Tuple, List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Lazy loading of heavy ML models
_whisper_model = None
_whisperx_model = None


def get_whisper_model():
    """Lazy load Whisper model"""
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper
            from app.config import settings
            logger.info(f"Loading Whisper model: {settings.WHISPER_MODEL_SIZE}")
            _whisper_model = whisper.load_model(settings.WHISPER_MODEL_SIZE)
            logger.info("Whisper model loaded successfully")
        except ImportError:
            logger.warning("Whisper not installed. Using mock transcription.")
            _whisper_model = "mock"
    return _whisper_model


def transcribe(audio_path: str, language: str = "ar") -> Tuple[str, List[Dict[str, Any]]]:
    """
    Transcribe audio file to text using Whisper.
    
    Args:
        audio_path: Path to normalized 16kHz mono WAV file
        language: Language code (default: Arabic)
        
    Returns:
        Tuple of (transcription_text, segments_with_timestamps)
        
    Segments format:
    [
        {
            "id": 0,
            "start": 0.0,
            "end": 2.5,
            "text": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
            "words": [
                {"word": "بِسْمِ", "start": 0.0, "end": 0.5},
                ...
            ]
        },
        ...
    ]
    """
    logger.info(f"Transcribing audio: {audio_path}")
    
    model = get_whisper_model()
    
    if model == "mock":
        # Return mock data for development without ML dependencies
        return _mock_transcription()
    
    try:
        # Run Whisper transcription
        result = model.transcribe(
            audio_path,
            language=language,
            task="transcribe",
            word_timestamps=True,  # Get word-level timestamps
            verbose=False
        )
        
        transcription = result["text"].strip()
        segments = result.get("segments", [])
        
        # Process segments to extract word timestamps
        processed_segments = []
        for seg in segments:
            processed_seg = {
                "id": seg.get("id", 0),
                "start": seg.get("start", 0.0),
                "end": seg.get("end", 0.0),
                "text": seg.get("text", "").strip(),
                "words": []
            }
            
            # Extract word-level timestamps if available
            if "words" in seg:
                for word_info in seg["words"]:
                    processed_seg["words"].append({
                        "word": word_info.get("word", "").strip(),
                        "start": word_info.get("start", 0.0),
                        "end": word_info.get("end", 0.0),
                        "probability": word_info.get("probability", 1.0)
                    })
            
            processed_segments.append(processed_seg)
        
        logger.info(f"Transcription complete: {len(transcription)} chars, {len(segments)} segments")
        return transcription, processed_segments
        
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}", exc_info=True)
        raise RuntimeError(f"ASR transcription failed: {str(e)}")


def transcribe_with_whisperx(audio_path: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Transcribe using WhisperX for better alignment.
    
    WhisperX provides more accurate word-level timestamps
    through forced alignment.
    """
    global _whisperx_model
    
    try:
        import whisperx
        import torch
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        
        # Load model if not cached
        if _whisperx_model is None:
            from app.config import settings
            _whisperx_model = whisperx.load_model(
                settings.WHISPER_MODEL_SIZE,
                device,
                compute_type=compute_type
            )
        
        # Transcribe
        audio = whisperx.load_audio(audio_path)
        result = _whisperx_model.transcribe(audio, batch_size=16)
        
        # Load alignment model for Arabic
        model_a, metadata = whisperx.load_align_model(
            language_code="ar",
            device=device
        )
        
        # Align
        result = whisperx.align(
            result["segments"],
            model_a,
            metadata,
            audio,
            device,
            return_char_alignments=False
        )
        
        transcription = " ".join(seg["text"] for seg in result["segments"])
        
        return transcription, result["segments"]
        
    except ImportError:
        logger.warning("WhisperX not available, falling back to standard Whisper")
        return transcribe(audio_path)


def _mock_transcription() -> Tuple[str, List[Dict[str, Any]]]:
    """
    Return mock transcription for development/testing.
    This allows running the API without ML dependencies.
    """
    logger.warning("Using MOCK transcription - install whisper for real ASR")
    
    mock_text = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"
    mock_segments = [
        {
            "id": 0,
            "start": 0.0,
            "end": 3.5,
            "text": mock_text,
            "words": [
                {"word": "بِسْمِ", "start": 0.0, "end": 0.6, "probability": 0.95},
                {"word": "اللَّهِ", "start": 0.6, "end": 1.2, "probability": 0.98},
                {"word": "الرَّحْمَٰنِ", "start": 1.2, "end": 2.2, "probability": 0.92},
                {"word": "الرَّحِيمِ", "start": 2.2, "end": 3.5, "probability": 0.96},
            ]
        }
    ]
    
    return mock_text, mock_segments


def get_phonetic_transcription(arabic_text: str) -> str:
    """
    Convert Arabic text to phonetic representation.
    
    Useful for comparing expected vs detected phonemes.
    This is a simplified version - a full implementation would
    use proper Arabic phonological rules.
    """
    # Simplified phonetic mapping
    # In production, use a proper Arabic phonetic converter
    phonetic_map = {
        'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j', 'ح': 'H',
        'خ': 'kh', 'د': 'd', 'ذ': 'dh', 'ر': 'r', 'ز': 'z',
        'س': 's', 'ش': 'sh', 'ص': 'S', 'ض': 'D', 'ط': 'T',
        'ظ': 'Z', 'ع': '3', 'غ': 'gh', 'ف': 'f', 'ق': 'q',
        'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n', 'ه': 'h',
        'و': 'w', 'ي': 'y', 'ء': "'", 'ا': 'a', 'أ': "'a",
        'إ': "'i", 'آ': "'aa", 'ة': 'h', 'ى': 'a',
    }
    
    result = []
    for char in arabic_text:
        if char in phonetic_map:
            result.append(phonetic_map[char])
        elif char.isspace():
            result.append(' ')
        # Skip diacritics for simplified version
    
    return ''.join(result)
