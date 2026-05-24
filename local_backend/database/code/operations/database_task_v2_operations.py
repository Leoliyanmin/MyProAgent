import json
from datetime import datetime

from local_backend.database.code.command.database_command import (
    create_event,
    get_event,
    list_events_by_user,
    update_event,
    delete_event,
    upsert_sync_state,
    get_sync_state,
)


class TaskV2Operations:
    def __init__(self):
        pass

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
               due_date: str = None, linked_schedule_id: int = None,
               priority: str = None) -> int:
        now = datetime.utcnow().isoformat()
        _priority = 2
        if priority is not None:
            if isinstance(priority, int):
                _priority = priority
            else:
                _priority = int(str(priority).lstrip("p") or "2")

        meta = {"status": "pending"}
        if linked_schedule_id is not None:
            meta["linked_schedule_id"] = linked_schedule_id

        event_id = create_event(
            user_id=user_id,
            event_title=title,
            event_type="task",
            event_source="manual",
            event_description=description,
            event_end_time=due_date,
            event_priority=_priority,
            event_is_completed=0,
            event_show_in_todo=1,
            event_meta_json=json.dumps(meta, ensure_ascii=False),
            event_created_at=now,
        )
        self._update_sync_version(user_id)
        return event_id

    def get_all(self, user_id: str) -> list[dict]:
        return list_events_by_user(user_id, event_type="task")

    def update(self, user_id: str, task_id: int, title: str = None,
               description: str = None, due_date: str = None,
               priority: str = None, status: str = None,
               linked_schedule_id: int | None | object = None) -> None:
        event = get_event(task_id)
        if not event or event["user_id"] != user_id:
            raise ValueError("Task not found: {}".format(task_id))

        _priority = None
        if priority is not None:
            if isinstance(priority, int):
                _priority = priority
            else:
                _priority = int(str(priority).lstrip("p") or "2")

        is_completed = None
        meta = {}
        if event.get("event_meta_json"):
            try:
                meta = json.loads(event["event_meta_json"])
            except (json.JSONDecodeError, TypeError):
                pass

        if status is not None:
            meta["status"] = status
            is_completed = 1 if status == "completed" else 0
        if linked_schedule_id is not None:
            meta["linked_schedule_id"] = linked_schedule_id

        update_event(
            task_id,
            event_title=title,
            event_description=description,
            event_end_time=due_date,
            event_priority=_priority,
            event_is_completed=is_completed,
            event_meta_json=json.dumps(meta, ensure_ascii=False) if meta else None,
        )
        self._update_sync_version(user_id)

    def delete(self, user_id: str, task_id: int) -> bool:
        event = get_event(task_id)
        if not event or event["user_id"] != user_id:
            return False
        delete_event(task_id)
        self._update_sync_version(user_id)
        return True
