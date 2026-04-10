from database.connection import engine, Base
from database.models import User, Schedule, Task, AgentChat

# 创建所有表
Base.metadata.create_all(bind=engine)
print("Local database initialized successfully!")
