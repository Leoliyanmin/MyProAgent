from layers.database.connection import engine, Base
from layers.database.models import User, Schedule, Task, AgentChat


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")
