"""
Human review/feedback endpoints
POST /api/v1/feedback/review
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class ErrorReview(BaseModel):
    """Single error review by human"""

    error_index: int
    is_correct: bool  # Was the AI detection correct?
    actual_error_type: Optional[str] = None  # If misclassified, what's the real type?
    notes: Optional[str] = None


class ReviewSubmission(BaseModel):
    """Human review submission for a recording"""

    recording_id: str
    reviewer_id: str
    error_reviews: List[ErrorReview]
    overall_assessment: str  # "correct", "mostly_correct", "needs_improvement"
    additional_errors: Optional[List[dict]] = None  # Errors AI missed
    notes: Optional[str] = None


class ReviewQueue(BaseModel):
    """Item in review queue"""

    recording_id: str
    user_id: str
    surah: int
    ayah: int
    low_confidence_errors: List[dict]
    created_at: datetime
    priority: int  # Higher = more urgent


@router.post("/review")
async def submit_review(review: ReviewSubmission):
    """
    Submit human review for a flagged recording.

    Used by qualified Qari reviewers to confirm or correct
    uncertain AI detections. This data is used for training.
    """
    logger.info(
        f"Review submitted for recording {review.recording_id} by {review.reviewer_id}"
    )

    # TODO: Store in database
    # TODO: Update training dataset
    # TODO: If 2+ reviewers agree, mark as confirmed

    return {
        "status": "accepted",
        "recording_id": review.recording_id,
        "reviewer_id": review.reviewer_id,
        "message": "Review submitted successfully. Thank you for your contribution.",
    }


@router.get("/queue")
async def get_review_queue(reviewer_id: str, limit: int = 10):
    """
    Get recordings pending human review.

    Returns recordings with low-confidence detections
    that need human verification.
    """
    # TODO: Query database for pending reviews
    # For now, return mock data

    return {
        "queue": [
            {
                "recording_id": "mock-recording-001",
                "user_id": "user-123",
                "surah": 1,
                "ayah": 1,
                "low_confidence_errors": [
                    {
                        "type": "substituted_letter",
                        "confidence": 0.55,
                        "letter": "ق",
                        "detected": "ك",
                    }
                ],
                "created_at": "2024-01-15T10:30:00Z",
                "priority": 3,
            }
        ],
        "total_pending": 1,
    }


@router.get("/stats")
async def get_review_stats(reviewer_id: Optional[str] = None):
    """
    Get review statistics for monitoring.
    """
    return {
        "total_recordings_analyzed": 1000,
        "pending_review": 45,
        "reviewed_today": 23,
        "agreement_rate": 0.89,  # Inter-reviewer agreement
        "model_accuracy_estimate": 0.82,
    }


@router.post("/flag")
async def flag_for_review(
    recording_id: str, reason: str, flagged_by: str  # "system" or user_id
):
    """
    Flag a recording for human review.

    Can be triggered by:
    - System (low confidence detection)
    - User (disagrees with feedback)
    """
    logger.info(f"Recording {recording_id} flagged for review: {reason}")

    # TODO: Add to review queue in database

    return {
        "status": "flagged",
        "recording_id": recording_id,
        "message": "Recording has been queued for expert review.",
    }
