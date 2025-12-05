"""
Progress tracking routes for Qari App
User statistics, session history, learning progress
"""

from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from ..auth import get_current_user, TokenData
import uuid

router = APIRouter(prefix="/api/v1/progress", tags=["progress"])


# Pydantic models
class SessionSummary(BaseModel):
    session_id: str
    surah: int
    ayah: int
    score: float
    error_count: int
    timestamp: datetime


class UserStats(BaseModel):
    total_sessions: int
    total_practice_time: int  # in seconds
    average_score: float
    best_score: float
    total_errors_fixed: int
    streak_days: int
    last_practice: Optional[datetime]


class ProgressByError(BaseModel):
    error_type: str
    total_occurrences: int
    fixed_count: int
    improvement_rate: float


class DailyProgress(BaseModel):
    date: str
    sessions: int
    average_score: float
    practice_time: int


class SurahProgress(BaseModel):
    surah: int
    ayahs_practiced: int
    average_score: float
    last_practiced: Optional[datetime]


# In-memory storage (replace with database)
sessions_db: dict = {}
user_stats_db: dict = {}


def get_or_create_user_stats(user_id: str) -> dict:
    """Get or create user statistics."""
    if user_id not in user_stats_db:
        user_stats_db[user_id] = {
            "total_sessions": 0,
            "total_practice_time": 0,
            "scores": [],
            "errors_fixed": 0,
            "streak_days": 0,
            "last_practice": None,
            "practice_dates": set(),
        }
    return user_stats_db[user_id]


@router.get("/stats", response_model=UserStats)
async def get_user_stats(current_user: TokenData = Depends(get_current_user)):
    """Get overall user statistics."""
    stats = get_or_create_user_stats(current_user.user_id)

    scores = stats["scores"]
    avg_score = sum(scores) / len(scores) if scores else 0.0
    best_score = max(scores) if scores else 0.0

    return UserStats(
        total_sessions=stats["total_sessions"],
        total_practice_time=stats["total_practice_time"],
        average_score=round(avg_score, 2),
        best_score=round(best_score, 2),
        total_errors_fixed=stats["errors_fixed"],
        streak_days=stats["streak_days"],
        last_practice=stats["last_practice"],
    )


@router.get("/sessions", response_model=List[SessionSummary])
async def get_session_history(
    current_user: TokenData = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get user's session history."""
    user_sessions = [
        s for s in sessions_db.values() if s.get("user_id") == current_user.user_id
    ]

    # Sort by timestamp descending
    user_sessions.sort(key=lambda x: x["timestamp"], reverse=True)

    # Paginate
    paginated = user_sessions[offset : offset + limit]

    return [
        SessionSummary(
            session_id=s["session_id"],
            surah=s["surah"],
            ayah=s["ayah"],
            score=s["score"],
            error_count=s["error_count"],
            timestamp=s["timestamp"],
        )
        for s in paginated
    ]


@router.get("/errors", response_model=List[ProgressByError])
async def get_error_progress(current_user: TokenData = Depends(get_current_user)):
    """Get progress breakdown by error type."""
    # Mock data - in production, aggregate from sessions
    error_types = [
        ("substituted_letter", 45, 32),
        ("madd_short", 28, 20),
        ("madd_long", 15, 12),
        ("ghunnah_missing", 22, 18),
        ("qalqalah_missing", 12, 8),
        ("idgham_missing", 8, 5),
    ]

    return [
        ProgressByError(
            error_type=error_type,
            total_occurrences=total,
            fixed_count=fixed,
            improvement_rate=round(fixed / total * 100, 1) if total > 0 else 0,
        )
        for error_type, total, fixed in error_types
    ]


@router.get("/daily", response_model=List[DailyProgress])
async def get_daily_progress(
    current_user: TokenData = Depends(get_current_user),
    days: int = Query(7, ge=1, le=30),
):
    """Get daily progress for the last N days."""
    progress = []
    today = datetime.utcnow().date()

    for i in range(days):
        date = today - timedelta(days=i)
        date_str = date.isoformat()

        # Count sessions for this day
        day_sessions = [
            s
            for s in sessions_db.values()
            if s.get("user_id") == current_user.user_id
            and s["timestamp"].date() == date
        ]

        if day_sessions:
            avg_score = sum(s["score"] for s in day_sessions) / len(day_sessions)
            total_time = sum(s.get("duration", 30) for s in day_sessions)
        else:
            avg_score = 0
            total_time = 0

        progress.append(
            DailyProgress(
                date=date_str,
                sessions=len(day_sessions),
                average_score=round(avg_score, 2),
                practice_time=total_time,
            )
        )

    return progress


@router.get("/surah", response_model=List[SurahProgress])
async def get_surah_progress(current_user: TokenData = Depends(get_current_user)):
    """Get progress by surah."""
    # Aggregate sessions by surah
    surah_data: dict = {}

    for session in sessions_db.values():
        if session.get("user_id") != current_user.user_id:
            continue

        surah = session["surah"]
        if surah not in surah_data:
            surah_data[surah] = {
                "ayahs": set(),
                "scores": [],
                "last_practiced": None,
            }

        surah_data[surah]["ayahs"].add(session["ayah"])
        surah_data[surah]["scores"].append(session["score"])

        if (
            surah_data[surah]["last_practiced"] is None
            or session["timestamp"] > surah_data[surah]["last_practiced"]
        ):
            surah_data[surah]["last_practiced"] = session["timestamp"]

    return [
        SurahProgress(
            surah=surah,
            ayahs_practiced=len(data["ayahs"]),
            average_score=round(sum(data["scores"]) / len(data["scores"]), 2),
            last_practiced=data["last_practiced"],
        )
        for surah, data in sorted(surah_data.items())
    ]


@router.post("/record-session")
async def record_session(
    surah: int,
    ayah: int,
    score: float,
    error_count: int,
    duration: int = 30,
    current_user: TokenData = Depends(get_current_user),
):
    """Record a practice session (called internally after analysis)."""
    session_id = str(uuid.uuid4())
    timestamp = datetime.utcnow()

    session = {
        "session_id": session_id,
        "user_id": current_user.user_id,
        "surah": surah,
        "ayah": ayah,
        "score": score,
        "error_count": error_count,
        "duration": duration,
        "timestamp": timestamp,
    }
    sessions_db[session_id] = session

    # Update user stats
    stats = get_or_create_user_stats(current_user.user_id)
    stats["total_sessions"] += 1
    stats["total_practice_time"] += duration
    stats["scores"].append(score)
    stats["last_practice"] = timestamp

    # Update streak
    today = timestamp.date()
    stats["practice_dates"].add(today)

    # Calculate streak
    streak = 0
    check_date = today
    while check_date in stats["practice_dates"]:
        streak += 1
        check_date -= timedelta(days=1)
    stats["streak_days"] = streak

    return {"session_id": session_id, "recorded": True}
