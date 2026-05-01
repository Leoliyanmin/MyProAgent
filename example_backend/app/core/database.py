from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from . import config

DATABASE_URL = config.DATABASE_URL
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(engine, future=True)
Base = declarative_base()

def init_db():
    """
    初始化数据库，创建所有模型表。
    """
    print("Initializing database...")
    Base.metadata.create_all(engine, )

def get_db():
    """
    获取一个数据库会话（Session），用于FastAPI依赖注入。
    请求结束后自动关闭会话。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_sync():
    """
    获取一个同步数据库会话（Session），适用于非异步场景。
    需要手动关闭会话。
    """
    return SessionLocal()