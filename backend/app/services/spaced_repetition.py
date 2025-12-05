"""
Spaced Repetition and Practice Session Management
Implements SM-2 algorithm for optimal learning
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from pydantic import BaseModel
import uuid
import math

# In-memory storage (replace with database)
practice_items_db: Dict[str, dict] = {}
user_queues_db: Dict[str, list] = {}


class PracticeItem(BaseModel):
    item_id: str
    user_id: str
    surah: int
    ayah: int
    error_type: str
    
    # SM-2 parameters
    easiness_factor: float = 2.5
    interval: int = 1  # days
    repetitions: int = 0
    next_review: datetime
    last_review: Optional[datetime] = None
    
    # Performance tracking
    total_attempts: int = 0
    successful_attempts: int = 0


class ReviewResult(BaseModel):
    item_id: str
    quality: int  # 0-5 scale (0=complete failure, 5=perfect)
    response_time: Optional[float] = None  # seconds


def calculate_sm2(
    easiness_factor: float,
    interval: int,
    repetitions: int,
    quality: int,
) -> tuple:
    """
    SM-2 Algorithm for spaced repetition.
    Returns (new_easiness, new_interval, new_repetitions)
    """
    # Quality must be 0-5
    quality = max(0, min(5, quality))
    
    # Update easiness factor
    new_ef = easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = max(1.3, new_ef)  # Minimum EF is 1.3
    
    if quality < 3:
        # Failed review - reset
        new_interval = 1
        new_repetitions = 0
    else:
        # Successful review
        new_repetitions = repetitions + 1
        
        if new_repetitions == 1:
            new_interval = 1
        elif new_repetitions == 2:
            new_interval = 6
        else:
            new_interval = math.ceil(interval * new_ef)
    
    return new_ef, new_interval, new_repetitions


def create_practice_item(
    user_id: str,
    surah: int,
    ayah: int,
    error_type: str,
) -> PracticeItem:
    """Create a new practice item from an error."""
    item_id = str(uuid.uuid4())
    
    item = PracticeItem(
        item_id=item_id,
        user_id=user_id,
        surah=surah,
        ayah=ayah,
        error_type=error_type,
        next_review=datetime.utcnow(),  # Review immediately first time
    )
    
    practice_items_db[item_id] = item.dict()
    
    # Add to user's queue
    if user_id not in user_queues_db:
        user_queues_db[user_id] = []
    user_queues_db[user_id].append(item_id)
    
    return item


def get_due_items(user_id: str, limit: int = 10) -> List[PracticeItem]:
    """Get practice items due for review."""
    now = datetime.utcnow()
    
    due_items = []
    for item_id in user_queues_db.get(user_id, []):
        if item_id not in practice_items_db:
            continue
        
        item_data = practice_items_db[item_id]
        next_review = item_data.get("next_review")
        
        if isinstance(next_review, str):
            next_review = datetime.fromisoformat(next_review)
        
        if next_review and next_review <= now:
            due_items.append(PracticeItem(**item_data))
    
    # Sort by next_review (oldest first)
    due_items.sort(key=lambda x: x.next_review)
    
    return due_items[:limit]


def process_review(result: ReviewResult) -> PracticeItem:
    """Process a review result and update the practice item."""
    if result.item_id not in practice_items_db:
        raise ValueError(f"Practice item not found: {result.item_id}")
    
    item_data = practice_items_db[result.item_id]
    
    # Calculate new SM-2 values
    new_ef, new_interval, new_reps = calculate_sm2(
        item_data["easiness_factor"],
        item_data["interval"],
        item_data["repetitions"],
        result.quality,
    )
    
    # Update item
    item_data["easiness_factor"] = new_ef
    item_data["interval"] = new_interval
    item_data["repetitions"] = new_reps
    item_data["next_review"] = datetime.utcnow() + timedelta(days=new_interval)
    item_data["last_review"] = datetime.utcnow()
    item_data["total_attempts"] = item_data.get("total_attempts", 0) + 1
    
    if result.quality >= 3:
        item_data["successful_attempts"] = item_data.get("successful_attempts", 0) + 1
    
    practice_items_db[result.item_id] = item_data
    
    return PracticeItem(**item_data)


def get_user_stats(user_id: str) -> dict:
    """Get spaced repetition statistics for a user."""
    user_items = [
        practice_items_db[item_id]
        for item_id in user_queues_db.get(user_id, [])
        if item_id in practice_items_db
    ]
    
    now = datetime.utcnow()
    
    due_count = 0
    learning_count = 0
    mastered_count = 0
    
    for item in user_items:
        next_review = item.get("next_review")
        if isinstance(next_review, str):
            next_review = datetime.fromisoformat(next_review)
        
        if next_review and next_review <= now:
            due_count += 1
        
        interval = item.get("interval", 1)
        if interval <= 7:
            learning_count += 1
        elif interval > 21:
            mastered_count += 1
    
    return {
        "total_items": len(user_items),
        "due_now": due_count,
        "learning": learning_count,
        "mastered": mastered_count,
        "review_accuracy": _calculate_accuracy(user_items),
    }


def _calculate_accuracy(items: list) -> float:
    """Calculate overall review accuracy."""
    total_attempts = sum(i.get("total_attempts", 0) for i in items)
    successful_attempts = sum(i.get("successful_attempts", 0) for i in items)
    
    if total_attempts == 0:
        return 0.0
    
    return round(successful_attempts / total_attempts * 100, 1)


def add_errors_to_practice(
    user_id: str,
    surah: int,
    ayah: int,
    errors: list,
) -> List[PracticeItem]:
    """Add errors from an analysis to the practice queue."""
    added_items = []
    
    for error in errors:
        error_type = error.get("type", "unknown")
        
        # Check if similar item already exists
        existing = _find_similar_item(user_id, surah, ayah, error_type)
        
        if not existing:
            item = create_practice_item(user_id, surah, ayah, error_type)
            added_items.append(item)
    
    return added_items


def _find_similar_item(
    user_id: str,
    surah: int,
    ayah: int,
    error_type: str,
) -> Optional[str]:
    """Find if a similar practice item already exists."""
    for item_id in user_queues_db.get(user_id, []):
        if item_id not in practice_items_db:
            continue
        
        item = practice_items_db[item_id]
        if (item["surah"] == surah and 
            item["ayah"] == ayah and 
            item["error_type"] == error_type):
            return item_id
    
    return None


def get_recommended_practice(user_id: str) -> dict:
    """Get recommended practice session based on due items."""
    due_items = get_due_items(user_id, limit=20)
    stats = get_user_stats(user_id)
    
    # Group by error type
    error_groups = {}
    for item in due_items:
        if item.error_type not in error_groups:
            error_groups[item.error_type] = []
        error_groups[item.error_type].append(item)
    
    # Prioritize weakest areas
    priority_order = sorted(
        error_groups.keys(),
        key=lambda x: len(error_groups[x]),
        reverse=True,
    )
    
    return {
        "due_count": len(due_items),
        "stats": stats,
        "priority_areas": priority_order[:3],
        "recommended_items": [item.dict() for item in due_items[:5]],
    }
