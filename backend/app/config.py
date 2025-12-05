"""
Application configuration settings
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/qari_db"
    REDIS_URL: str = "redis://redis:6379/0"

    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "qari-app-audio"

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None

    # JWT
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Audio Processing
    MAX_AUDIO_DURATION_SECONDS: int = 120
    AUDIO_SAMPLE_RATE: int = 16000

    # Model
    WHISPER_MODEL_SIZE: str = "large-v2"
    MODEL_CACHE_DIR: str = "/app/models/cache"

    # TTS
    TTS_PROVIDER: str = "local"
    GOOGLE_TTS_API_KEY: Optional[str] = None
    AMAZON_POLLY_REGION: str = "us-east-1"

    # Tajweed Thresholds
    MADD_SHORT_THRESHOLD: float = 0.05
    MADD_NORMAL_MIN: float = 0.18
    MADD_NORMAL_MAX: float = 0.25
    GHUNNAH_MIN_DURATION: float = 0.12
    CONFIDENCE_THRESHOLD: float = 0.6

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
