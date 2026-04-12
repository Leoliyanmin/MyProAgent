from pydantic import BaseSettings
from typing import List


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "SUSTech Student Productivity Agent (Local)"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"  # 日志级别: DEBUG, INFO, WARNING, ERROR
    
    # 数据库配置（Local使用SQLite）
    DATABASE_URL: str = "sqlite:///./local_app.db"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # 服务器后端配置
    SERVER_BACKEND_URL: str = "http://localhost:8001"
    
    class Config:
        env_file = ".env"


settings = Settings()
