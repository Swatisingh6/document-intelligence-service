import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Configuration Settings loaded from Environment Variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "Document Intelligence & Question Extraction Service"
    APP_ENV: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    API_V1_STR: str = "/api/v1"

    # Security / Auth
    SECRET_KEY: str = Field(default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database
    DATABASE_URL: str = Field(default="sqlite:///./doc_intel.db")
    
    # Redis & Celery
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0")

    # File Storage
    STORAGE_PATH: str = Field(default="./storage")
    MAX_UPLOAD_SIZE_MB: int = Field(default=20)
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/jpg"
    ]
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".jpg", ".jpeg", ".png"]

    # OCR Settings
    TESSERACT_CMD: str = Field(default="tesseract")

    # Optional AI/LLM Settings
    LLM_PROVIDER: str = Field(default="none")  # 'none', 'gemini', 'openai'
    LLM_API_KEY: str = Field(default="")
    LLM_MODEL: str = Field(default="gemini-1.5-flash")

    # Extraction & Confidence Thresholds
    HIGH_CONFIDENCE_THRESHOLD: float = 0.85
    MEDIUM_CONFIDENCE_THRESHOLD: float = 0.60


settings = Settings()

# Ensure storage directory exists
os.makedirs(settings.STORAGE_PATH, exist_ok=True)
