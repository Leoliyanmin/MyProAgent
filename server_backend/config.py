from pydantic import BaseSettings
from typing import List


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "SUSTech Student Productivity Agent (Server)"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # 数据库配置（Server使用SQLite，实际部署可替换为PostgreSQL）
    DATABASE_URL: str = "sqlite:///./server_app.db"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    class Config:
        env_file = ".env"


settings = Settings()
