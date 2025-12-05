"""
Practice session routes for repetition loop
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from ..auth import get_current_user, TokenData
from ..services.spaced_repetition import (
    PracticeItem, ReviewResult,
    get_due_items, process_review, get_user_stats,
    add_errors_to_practice, get_recommended_practice,
)

router = APIRouter(prefix="/api/v1/practice", tags=["practice"])


class ReviewRequest(BaseModel):
    item_id: str
    quality: int  # 0-5 scale
    response_time: Optional[float] = None


class PracticeSession(BaseModel):
    session_id: str
    items: List[dict]
    total_items: int


@router.get("/due", response_model=List[dict])
async def get_due_practice_items(
    limit: int = 10,
    current_user: TokenData = Depends(get_current_user),
):
    """Get practice items that are due for review."""
    items = get_due_items(current_user.user_id, limit=limit)
    return [item.dict() for item in items]


@router.post("/review")
async def submit_review(
    review: ReviewRequest,
    current_user: TokenData = Depends(get_current_user),
):
    """Submit a review result for a practice item."""
    try:
        result = ReviewResult(
            item_id=review.item_id,
            quality=review.quality,
            response_time=review.response_time,
        )
        updated_item = process_review(result)
        
        return {
            "success": True,
            "item": updated_item.dict(),
            "next_review": updated_item.next_review.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/stats")
async def get_practice_stats(current_user: TokenData = Depends(get_current_user)):
    """Get spaced repetition statistics."""
    return get_user_stats(current_user.user_id)


@router.get("/recommended")
async def get_recommended(current_user: TokenData = Depends(get_current_user)):
    """Get recommended practice session."""
    return get_recommended_practice(current_user.user_id)


@router.post("/add-errors")
async def add_errors_from_analysis(
    surah: int,
    ayah: int,
    errors: List[dict],
    current_user: TokenData = Depends(get_current_user),
):
    """Add errors from an analysis to the practice queue."""
    added = add_errors_to_practice(
        current_user.user_id,
        surah,
        ayah,
        errors,
    )
    return {
        "added_count": len(added),
        "items": [item.dict() for item in added],
    }


@router.delete("/item/{item_id}")
async def remove_practice_item(
    item_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """Remove a practice item (mark as mastered)."""
    from ..services.spaced_repetition import practice_items_db, user_queues_db
    
    if item_id not in practice_items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Verify ownership
    item = practice_items_db[item_id]
    if item["user_id"] != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Remove from database
    del practice_items_db[item_id]
    
    # Remove from user queue
    if current_user.user_id in user_queues_db:
        user_queues_db[current_user.user_id] = [
            i for i in user_queues_db[current_user.user_id] if i != item_id
        ]
    
    return {"success": True, "removed": item_id}
