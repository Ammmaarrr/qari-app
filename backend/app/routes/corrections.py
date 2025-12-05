"""
Correction audio endpoints
GET /api/v1/correction/audio/{id}
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from pathlib import Path
import logging

from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Mapping of correction IDs to audio files
# In production, this would be stored in database/S3
CORRECTION_AUDIO_MAPPING = {
    "qa_01": "corrections/qaf_correct.mp3",
    "madd_natural": "corrections/madd_natural.mp3",
    "ghunnah_noon": "corrections/ghunnah_noon.mp3",
    "qalqalah_ba": "corrections/qalqalah_ba.mp3",
    "qalqalah_jeem": "corrections/qalqalah_jeem.mp3",
    "qalqalah_dal": "corrections/qalqalah_dal.mp3",
    "qalqalah_ta": "corrections/qalqalah_ta.mp3",
    "qalqalah_qaf": "corrections/qalqalah_qaf.mp3",
}


@router.get("/audio/{correction_id}")
async def get_correction_audio(correction_id: str):
    """
    Get correction audio sample by ID.
    
    Returns audio file demonstrating correct pronunciation.
    In production, this would serve from S3/CDN.
    """
    logger.info(f"Fetching correction audio: {correction_id}")
    
    # Check if correction exists
    if correction_id not in CORRECTION_AUDIO_MAPPING:
        raise HTTPException(status_code=404, detail="Correction audio not found")
    
    # In production, return S3 presigned URL or CDN URL
    # For development, serve local file
    audio_path = Path(f"/app/audio/{CORRECTION_AUDIO_MAPPING[correction_id]}")
    
    if audio_path.exists():
        return FileResponse(
            audio_path,
            media_type="audio/mpeg",
            filename=f"{correction_id}.mp3"
        )
    else:
        # Return placeholder URL for development
        return {
            "correction_id": correction_id,
            "audio_url": f"https://storage.example.com/corrections/{correction_id}.mp3",
            "message": "Audio file not found locally. URL is placeholder."
        }


@router.get("/audio/{correction_id}/url")
async def get_correction_audio_url(correction_id: str):
    """
    Get presigned URL for correction audio.
    Useful for mobile app to cache audio.
    """
    if correction_id not in CORRECTION_AUDIO_MAPPING:
        raise HTTPException(status_code=404, detail="Correction audio not found")
    
    # In production, generate S3 presigned URL
    # For now, return placeholder
    return {
        "correction_id": correction_id,
        "url": f"https://{settings.S3_BUCKET_NAME}.s3.amazonaws.com/corrections/{correction_id}.mp3",
        "expires_in": 3600
    }


@router.get("/list")
async def list_corrections():
    """
    List all available correction audio samples.
    """
    return {
        "corrections": [
            {"id": k, "path": v} 
            for k, v in CORRECTION_AUDIO_MAPPING.items()
        ]
    }
