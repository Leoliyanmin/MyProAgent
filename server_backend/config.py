from pydantic import BaseSettings
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "SUSTech Student Productivity Agent (Server)"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    TEST_MODE: bool = False
    SKIP_VERIFICATION: bool = False  # 是否跳过验证码验证
    SKIP_RATE_LIMIT: bool = False  # 新增：是否跳过频率限制
    
    # 数据库配置（Server使用SQLite，实际部署可替换为PostgreSQL）
    DATABASE_URL: str = "sqlite:///./server_app.db"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    
    # 邮件服务配置
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "SUSTech Student Productivity Agent"
    
    # 验证码配置
    VERIFICATION_CODE_LENGTH: int = 6
    VERIFICATION_CODE_EXPIRE_MINUTES: int = 5
    VERIFICATION_CODE_MAX_ATTEMPTS: int = 3
    
    # 频率限制配置
    RATE_LIMIT_MAX_REQUESTS: int = 5
    RATE_LIMIT_WINDOW_MINUTES: int = 15
    
    class Config:
        env_file = os.path.join(os.path.dirname(__file__), ".env")


settings = Settings()
print(f"TEST_MODE: {settings.TEST_MODE}")
print(f"SKIP_VERIFICATION: {settings.SKIP_VERIFICATION}")
print(f"SKIP_RATE_LIMIT: {settings.SKIP_RATE_LIMIT}")