"""
Application configuration.
"""

import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings from environment"""

    # Application
    APP_NAME: str = "AIVision OCR API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-secret-key-in-production"
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    ALLOWED_HEADERS: List[str] = ["*"]

    # Database
    DATABASE_URL: str = "postgresql://aivision:password@localhost:5432/aivision"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Storage
    STORAGE_TYPE: str = "local"  # local, s3, minio
    S3_BUCKET: str = "aivision-documents"
    S3_ENDPOINT: str = "https://s3.amazonaws.com"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    LOCAL_STORAGE_PATH: str = "./uploads"

    # Vision Model API Keys
    GOOGLE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Document Processing
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "jpg", "jpeg", "png", "tiff", "heic"]
    PDF_DPI: int = 300
    MAX_CONCURRENT_EXTRACTIONS: int = 20

    # Model Defaults
    DEFAULT_VISION_MODEL: str = "gemini-2.0-flash-exp"
    CONFIDENCE_THRESHOLD: float = 0.70
    ENABLE_MODEL_FALLBACK: bool = True

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # Monitoring
    SENTRY_DSN: str = ""
    LOG_LEVEL: str = "INFO"

    # Feature Flags
    ENABLE_BATCH_PROCESSING: bool = True
    ENABLE_CUSTOM_TEMPLATES: bool = True
    ENABLE_ANALYTICS: bool = True
    ENABLE_WEBHOOKS: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_api_keys() -> dict:
    """Get API keys for vision models"""
    return {
        "gemini": settings.GOOGLE_API_KEY,
        "openai": settings.OPENAI_API_KEY,
        "anthropic": settings.ANTHROPIC_API_KEY
    }
