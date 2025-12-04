from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class FeedbackReview(BaseModel):
    recording_id: str
    reviewer_id: str
    error_type: Optional[str] = None
    is_correct: bool
    notes: Optional[str] = None


@router.post("/review")
async def submit_review(feedback: FeedbackReview):
    """Submit human reviewer feedback."""
    return {
        "status": "received",
        "recording_id": feedback.recording_id,
        "message": "Feedback recorded for training data"
    }