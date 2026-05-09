from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    APP_NAME: str = "SUSTech Student Productivity Agent (Server)"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    TEST_MODE: bool = True
    SKIP_VERIFICATION: bool = True
    SKIP_RATE_LIMIT: bool = True
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "sqlite:///./database/db/server.db"

    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "SUSTech Student Productivity Agent"

    VERIFICATION_CODE_LENGTH: int = 6
    VERIFICATION_CODE_EXPIRE_MINUTES: int = 5
    VERIFICATION_CODE_MAX_ATTEMPTS: int = 3

    RATE_LIMIT_MAX_REQUESTS: int = 5
    RATE_LIMIT_WINDOW_MINUTES: int = 60

    model_config = {"env_file": os.path.join(os.path.dirname(__file__), ".env"), "extra": "allow"}


settings = Settings()