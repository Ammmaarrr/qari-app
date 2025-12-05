"""
Recording analysis endpoint
POST /api/v1/recordings/analyze
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import Optional
import uuid
import logging
import time

from app.services.audio_processing import normalize_audio_to_16k
from app.services.asr_service import transcribe
from app.services.alignment import match_ayah
from app.services.tajweed import analyze_tajweed
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/analyze")
async def analyze_recording(
    user_id: str = Form(..., description="User identifier (UUID)"),
    surah: Optional[int] = Form(None, description="Surah number (1-114)"),
    ayah: Optional[int] = Form(None, description="Ayah number"),
    mode: str = Form("short", description="Recording mode: 'short' or 'long'"),
    audio_file: UploadFile = File(..., description="Audio file (WAV/MP3)")
):
    """
    Analyze a Quran recitation recording.
    
    This endpoint:
    1. Receives audio file upload
    2. Normalizes audio to 16kHz mono WAV
    3. Runs ASR (Whisper) to transcribe
    4. Matches transcription to Quran verses
    5. Performs forced alignment
    6. Runs tajweed rule checks
    7. Returns detailed analysis with errors and suggestions
    
    Returns:
        JSON with matched_ayah, errors list, overall_score, and recommendation
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    logger.info(f"[{request_id}] Analyzing recording for user {user_id}, surah={surah}, ayah={ayah}, mode={mode}")
    
    # Validate audio file
    if not audio_file.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")
    
    allowed_extensions = {'.wav', '.mp3', '.m4a', '.ogg', '.webm'}
    file_ext = Path(audio_file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported audio format. Allowed: {allowed_extensions}"
        )
    
    # Validate surah/ayah if provided
    if surah is not None and (surah < 1 or surah > 114):
        raise HTTPException(status_code=400, detail="Surah must be between 1 and 114")
    
    try:
        # Save uploaded file to temp directory
        tmp_dir = Path("/tmp/recitations")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        
        original_filename = tmp_dir / f"{request_id}_original{file_ext}"
        normalized_filename = tmp_dir / f"{request_id}_normalized.wav"
        
        # Write uploaded file
        content = await audio_file.read()
        with open(original_filename, "wb") as f:
            f.write(content)
        
        logger.info(f"[{request_id}] Saved audio file: {original_filename} ({len(content)} bytes)")
        
        # Step 1: Normalize audio to 16kHz mono WAV
        normalize_audio_to_16k(str(original_filename), str(normalized_filename))
        logger.info(f"[{request_id}] Audio normalized")
        
        # Step 2: ASR - Transcribe audio
        transcription, segments = transcribe(str(normalized_filename))
        logger.info(f"[{request_id}] Transcription: {transcription[:100]}...")
        
        # Step 3: Match to Quran verse
        matched = match_ayah(transcription, surah, ayah)
        logger.info(f"[{request_id}] Matched ayah: Surah {matched['surah']}, Ayah {matched['ayah']}")
        
        # Step 4: Tajweed analysis with forced alignment
        analysis = analyze_tajweed(str(normalized_filename), matched, segments)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        logger.info(f"[{request_id}] Analysis complete in {processing_time:.2f}s")
        
        # Build response
        response = {
            "request_id": request_id,
            "matched_ayah": {
                "surah": matched["surah"],
                "ayah": matched["ayah"],
                "confidence": matched["confidence"],
                "text": matched.get("text", "")
            },
            "errors": analysis["errors"],
            "overall_score": analysis["score"],
            "recommendation": analysis["recommendation"],
            "processing_time_seconds": round(processing_time, 2)
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"[{request_id}] Error analyzing recording: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    finally:
        # Cleanup temp files (in production, you might want to keep for debugging)
        # original_filename.unlink(missing_ok=True)
        # normalized_filename.unlink(missing_ok=True)
        pass


@router.post("/analyze/quick")
async def quick_analyze(
    user_id: str = Form(...),
    surah: int = Form(..., description="Surah number"),
    ayah: int = Form(..., description="Ayah number"),
    target_word_index: int = Form(..., description="Index of word to focus on (0-based)"),
    error_type: str = Form(..., description="Type of error being corrected"),
    audio_file: UploadFile = File(...)
):
    """
    Quick analysis for repetition loop - focuses on a specific word.
    Used when user is retrying a specific error.
    
    This endpoint:
    1. Transcribes the short audio clip
    2. Focuses analysis on the target word only
    3. Returns pass/fail with specific feedback
    """
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] Quick analyze: word {target_word_index}, error_type={error_type}")
    
    try:
        # Save and normalize audio
        tmp_dir = Path("/tmp/recitations")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        
        file_ext = Path(audio_file.filename).suffix.lower()
        original_filename = tmp_dir / f"{request_id}_quick{file_ext}"
        normalized_filename = tmp_dir / f"{request_id}_quick_normalized.wav"
        
        content = await audio_file.read()
        with open(original_filename, "wb") as f:
            f.write(content)
        
        normalize_audio_to_16k(str(original_filename), str(normalized_filename))
        
        # Transcribe
        transcription, segments = transcribe(str(normalized_filename))
        
        # Get expected ayah text
        from app.services.alignment import get_ayah_text
        expected_text = get_ayah_text(surah, ayah)
        expected_words = expected_text.split()
        
        # Validate word index
        if target_word_index < 0 or target_word_index >= len(expected_words):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid word index. Ayah has {len(expected_words)} words"
            )
        
        target_word = expected_words[target_word_index]
        transcribed_words = transcription.split()
        
        # Simple matching - check if target word appears in transcription
        # For more accuracy, could use phonetic matching
        passed = False
        confidence = 0.0
        feedback = ""
        
        if len(transcribed_words) > 0:
            # Find closest match to target word
            from difflib import SequenceMatcher
            similarities = [
                SequenceMatcher(None, target_word, tw).ratio() 
                for tw in transcribed_words
            ]
            max_similarity = max(similarities) if similarities else 0.0
            
            # Threshold for passing
            PASS_THRESHOLD = 0.75
            
            if max_similarity >= PASS_THRESHOLD:
                passed = True
                confidence = max_similarity
                feedback = f"Excellent! '{target_word}' pronounced correctly."
            else:
                confidence = max_similarity
                feedback = f"The word '{target_word}' needs more practice. Listen to the correction audio and try again."
        else:
            feedback = "No speech detected. Please try again with a clearer recording."
        
        logger.info(f"[{request_id}] Quick result: passed={passed}, confidence={confidence:.2f}")
        
        return {
            "passed": passed,
            "confidence": round(confidence, 2),
            "feedback": feedback,
            "target_word": target_word,
            "detected": transcribed_words[0] if transcribed_words else None
        }
        
    except Exception as e:
        logger.error(f"[{request_id}] Quick analyze error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Quick analysis failed: {str(e)}")
