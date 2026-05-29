"""Local backend configuration.

Single source of truth: .env file in the same directory.
config.py defines schema, types, and validation only.
All runtime values come from .env — no business defaults here.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- Application ----
    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool = False
    TEST_MODE: bool = False
    SKIP_VERIFICATION: bool = False
    LOG_LEVEL: str = "INFO"

    # ---- Database ----
    DATABASE_URL: str

    # ---- JWT ----
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    # ---- CORS ----
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost:1420",
    ]

    # ---- Server Backend ----
    SERVER_BACKEND_URL: str = "http://127.0.0.1:8001"

    # ---- Sync ----
    SYNC_INTERVAL_SECONDS: int = 3600
    EMAIL_SYNC_INTERVAL_SECONDS: int = 1800
    EMAIL_SYNC_MAX_MESSAGES: int = 20

    # ---- Encryption ----
    ENCRYPTION_KEY: str


settings = Settings()
