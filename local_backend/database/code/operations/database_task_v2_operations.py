from local_backend.database.code.command.database_command import (
    create_task,
    get_task,
    list_tasks_by_user,
    update_task,
    delete_task,
    create_data,
    create_category,
    list_categories_by_user,
    upsert_sync_state,
    get_sync_state,
)
from datetime import datetime


class TaskV2Operations:
    def __init__(self):
        pass

    def _ensure_task_category(self, user_id: str) -> int:
        categories = list_categories_by_user(user_id)
        for cat in categories:
            if cat["category_kind"] == "task":
                return cat["category_id"]
        now = datetime.utcnow().isoformat()
        return create_category(
            user_id=user_id, category_kind="task", category_title="任务",
            category_content=None, category_link=None, category_created_at=now,
        )

    def _update_sync_version(self, user_id: str) -> None:
        sync_state = get_sync_state(user_id)
        if sync_state:
            now = datetime.utcnow().isoformat()
            upsert_sync_state(
                user_id=user_id, user_data_updated_at=now,
                user_last_synced_at=sync_state["user_last_synced_at"],
                user_version=sync_state["user_version"] + 1,
                sync_updated_at=now,
            )

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

        cat_id = self._ensure_task_category(user_id)
        create_data(
            user_id=user_id, data_category_id=cat_id,
            data_content_type="task", data_classification_code=3,
            data_title=title, data_content_text=description,
            data_link_url="task:{}".format(task_id),
            data_release_time=None, data_ddl_time=due_date,
            data_is_previewable=0, data_created_at=now,
            data_linked_schedule_id=linked_schedule_id,
        )
        self._update_sync_version(user_id)
        return task_id

    def get_all(self, user_id: str) -> list[dict]:
        return list_tasks_by_user(user_id)

    def update(self, user_id: str, task_id: int, title: str = None,
               description: str = None, due_date: str = None,
               priority: str = None, status: str = None,
               linked_schedule_id: int | None | object = None) -> None:
        task = get_task(task_id)
        if not task or task["user_id"] != user_id:
            raise ValueError("Task not found: {}".format(task_id))
        now = datetime.utcnow().isoformat()
        update_task(task_id, title=title, description=description,
                    due_date=due_date, priority=priority, status=status,
                    linked_schedule_id=linked_schedule_id,
                    updated_at=now)
        self._update_sync_version(user_id)

    def delete(self, user_id: str, task_id: int) -> bool:
        task = get_task(task_id)
        if not task or task["user_id"] != user_id:
            return False
        delete_task(task_id)
        self._update_sync_version(user_id)
        return True
