from pydantic import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "SUSTech Student Productivity Agent (Local)"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "sqlite:///./local_app.db"

    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    SERVER_BACKEND_URL: str = "http://localhost:8001"

    class Config:
        env_file = ".env"


settings = Settings()
