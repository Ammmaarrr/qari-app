from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import analyze, correction, feedback, websocket

app = FastAPI(
    title="Qari App API",
    description="Quran recitation analysis with tajweed feedback",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analyze.router, prefix="/api/v1/recordings", tags=["recordings"])
app.include_router(correction.router, prefix="/api/v1/correction", tags=["correction"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["feedback"])
app.include_router(websocket.router, tags=["websocket"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}