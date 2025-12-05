"""
Qari App - Quran Recitation Analysis API
FastAPI main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.routes import (
    analyze,
    corrections,
    feedback,
    health,
    auth,
    progress,
    practice,
    files,
    stats,
)
from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting Qari App API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    # Initialize ML models on startup (lazy loading)
    yield
    logger.info("Shutting down Qari App API...")


app = FastAPI(
    title="Qari App API",
    description="Quran Recitation Analysis - ASR + Tajweed Checking",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, tags=["Authentication"])
app.include_router(analyze.router, prefix="/api/v1/recordings", tags=["Recordings"])
app.include_router(
    corrections.router, prefix="/api/v1/correction", tags=["Corrections"]
)
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["Feedback"])
app.include_router(progress.router, tags=["Progress"])
app.include_router(practice.router, tags=["Practice"])
app.include_router(files.router, tags=["Files"])
app.include_router(stats.router, tags=["Stats"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Qari App API - Quran Recitation Analysis",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG
    )
