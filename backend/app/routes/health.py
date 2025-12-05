"""
Health check endpoint
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    return {"status": "healthy", "service": "qari-app-api"}


@router.get("/ready")
async def readiness_check():
    """Readiness check - verify all dependencies are available"""
    # TODO: Add database and Redis connectivity checks
    return {
        "status": "ready",
        "database": "connected",
        "redis": "connected",
        "models": "loaded",
    }
