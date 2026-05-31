"""Server backend configuration.

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
    APP_NAME: str = "ProAgent-Server"
    APP_VERSION: str = "0.0.0"
    DEBUG: bool = False
    TEST_MODE: bool = False
    SKIP_VERIFICATION: bool = False
    SKIP_RATE_LIMIT: bool = False
    LOG_LEVEL: str = "INFO"

    # ---- Database ----
    DATABASE_URL: str = "sqlite:///./server_app.db"

    # ---- JWT ----
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    # ---- CORS ----
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    # ---- SMTP ----
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = ""

    # ---- Verification Code ----
    VERIFICATION_CODE_LENGTH: int = 6
    VERIFICATION_CODE_EXPIRE_MINUTES: int = 5
    VERIFICATION_CODE_MAX_ATTEMPTS: int = 3

    # ---- Rate Limiting ----
    RATE_LIMIT_MAX_REQUESTS: int = 5
    RATE_LIMIT_WINDOW_MINUTES: int = 15

    # ---- Redis (optional) ----
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""


settings = Settings()