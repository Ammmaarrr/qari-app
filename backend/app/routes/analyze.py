from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional

router = APIRouter()


@router.post("/analyze")
async def analyze_recording(
    user_id: str = Form(...),
    surah: Optional[int] = Form(None),
    ayah: Optional[int] = Form(None),
    mode: str = Form("short"),
    audio_file: UploadFile = File(...)
):
    """
    Analyze a Quran recitation recording for tajweed errors.
    Returns mock response for Sprint 0.
    """
    return {
        "matched_ayah": {"surah": surah or 1, "ayah": ayah or 1, "confidence": 0.92},
        "errors": [
            {
                "type": "substituted_letter",
                "letter": "ق",
                "expected": "ق",
                "detected": "ك",
                "start_time": 0.56,
                "end_time": 0.68,
                "confidence": 0.85,
                "suggestion": "Push back of tongue - listen and repeat",
                "correction_audio_url": "https://example.com/corrections/qa_01.mp3"
            }
        ],
        "overall_score": 0.78,
        "recommendation": "Repeat ayah two times focusing on 'ق'."
    }