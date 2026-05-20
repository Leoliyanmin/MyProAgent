from local_backend.database.code.command.database_command import (
    create_task,
    get_task,
    list_tasks_by_user,
    update_task,
    delete_task,
)
from local_backend.database.code.operations.database_task_operations import TaskOperations
from datetime import datetime


class TaskV2Operations:
    def __init__(self):
        self._legacy = TaskOperations()

    def create(self, user_id: str, title: str, description: str = None,
               due_date: str = None, linked_schedule_id: int = None) -> int:
        now = datetime.utcnow().isoformat()
        task_id = create_task(
            user_id=user_id, title=title, description=description,
            priority=2, status="pending", due_date=due_date,
            linked_schedule_id=linked_schedule_id, source="manual",
            created_at=now,
        )
        update_task(task_id, updated_at=now)
        self._legacy.create_task(user_id, title, description, due_date, linked_schedule_id)
        return task_id

    def get_all(self, user_id: str) -> list[dict]:
        return list_tasks_by_user(user_id)

    def update(self, user_id: str, task_id: int, title: str = None,
               description: str = None, due_date: str = None,
               linked_schedule_id: int | None | object = None) -> None:
        task = get_task(task_id)
        if not task or task["user_id"] != user_id:
            raise ValueError("Task not found: {}".format(task_id))
        now = datetime.utcnow().isoformat()
        update_task(task_id, title=title, description=description,
                    due_date=due_date, linked_schedule_id=linked_schedule_id,
                    updated_at=now)
        self._legacy.update_task(user_id, task_id, title, description, due_date, linked_schedule_id)

    def delete(self, user_id: str, task_id: int) -> bool:
        task = get_task(task_id)
        if not task or task["user_id"] != user_id:
            return False
        delete_task(task_id)
        self._legacy.delete_task(user_id, task_id)
        return True
