import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Settings:
    APP_NAME = os.getenv("APP_NAME", "SUSTech Student Productivity Agent")
    APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))
    
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sustech_agent.db")
    
    CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
