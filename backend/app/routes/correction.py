from fastapi import APIRouter

router = APIRouter()


@router.get("/audio/{correction_id}")
async def get_correction_audio(correction_id: str):
    """Get correction audio sample by ID."""
    return {
        "id": correction_id,
        "audio_url": f"https://example.com/corrections/{correction_id}.mp3",
        "letter": "ق",
        "description": "Correct pronunciation of Qaf"
    }