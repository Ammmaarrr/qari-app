"""
File serving routes for audio and uploads
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter(prefix="/api/v1", tags=["files"])

# Storage directories
AUDIO_CACHE_DIR = Path("audio_cache")
UPLOADS_DIR = Path("uploads")


@router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """Serve cached audio files (TTS generated)."""
    file_path = AUDIO_CACHE_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        file_path,
        media_type="audio/mpeg",
        filename=filename,
    )


@router.get("/files/{file_path:path}")
async def get_uploaded_file(file_path: str):
    """Serve uploaded files."""
    full_path = UPLOADS_DIR / file_path
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type
    suffix = full_path.suffix.lower()
    media_types = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".webm": "audio/webm",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
    }
    media_type = media_types.get(suffix, "application/octet-stream")
    
    return FileResponse(
        full_path,
        media_type=media_type,
        filename=full_path.name,
    )
