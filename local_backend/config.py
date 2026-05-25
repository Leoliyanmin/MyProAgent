from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "SUSTech Student Productivity Agent (Local)"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "sqlite:///./local_app.db"
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8080", "http://localhost:1420"]
    SERVER_BACKEND_URL: str = "http://localhost:8001"
    TEST_MODE: bool = True
    SKIP_VERIFICATION: bool = True

    # Blackboard/TIS 配置
    
    # Blackboard配置
    CAS_SERVER_URL: str = "https://cas.sustech.edu.cn/cas"
    CAS_VALIDATE_PATH: str = "/validate"
    CAS_LOGIN_PATH: str = "/login"
    BLACKBOARD_URL: str = "https://bb.sustech.edu.cn"
    BLACKBOARD_LOGIN_PATH: str = "/webapps/login/?action=login&new_loc=%2Fwebapps%2Fportal%2Fexecute%2FdefaultTab"
    BLACKBOARD_COURSE_PATH: str = "/webapps/blackboard/content/listContent.jsp"
    BLACKBOARD_ASSIGNMENT_PATH: str = "/webapps/assignments/content/listContent.jsp"
    BLACKBOARD_CALLBACK_URL: str = "http://localhost:8002/api/v1/blackboard/callback"
    ENCRYPTION_KEY: str = "your-encryption-key-here-123456789012345678901234"
    SYNC_INTERVAL_SECONDS: int = 10  # 本地到服务器定时同步间隔（秒）
    EMAIL_SYNC_INTERVAL_SECONDS: int = 300  # 邮件定时同步间隔（秒）
    EMAIL_SYNC_MAX_MESSAGES: int = 20  # 每次最多同步邮件数
    
    model_config = {"env_file": ".env", "extra": "allow"}


settings = Settings()
