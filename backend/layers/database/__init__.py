from layers.database.connection import engine, Base
from layers.database.models import User, Schedule, Task, AgentChat


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")


if __name__ == "__main__":
    init_db()
