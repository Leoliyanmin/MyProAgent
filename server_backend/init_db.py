from database.connection import engine, Base
from database.models import User, Schedule, Task, AgentChat, SyncRecord

# 创建所有表
Base.metadata.create_all(bind=engine)
print("Server database initialized successfully!")
