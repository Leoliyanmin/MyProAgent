from __future__ import annotations

import json
import threading
from datetime import datetime, timezone

from local_backend.database.code.command import database_command as db

_USER_LOCKS: dict[str, threading.RLock] = {}
_USER_LOCKS_GUARD = threading.Lock()


def _get_user_lock(user_id: str) -> threading.RLock:
    with _USER_LOCKS_GUARD:
        lock = _USER_LOCKS.get(user_id)
        if lock is None:
            lock = threading.RLock()
            _USER_LOCKS[user_id] = lock
        return lock


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ScheduleOperations:
    def create_schedule(
        self, user_id: str, title: str, start_time: str, end_time: str,
        event_type: str = "personal", priority_level: int = 2,
        is_completed: int = 0, location: str | None = None,
        description: str | None = None, related_link: str | None = None,
        recurrence_rule: str | None = None, color_tag: str | None = None,
    ) -> int:
        with _get_user_lock(user_id):
            self._require_user(user_id)
            meta = {}
            if recurrence_rule:
                meta["recurrence_rule"] = recurrence_rule
            meta_json = json.dumps(meta) if meta else None

            event_id = db.create_event(
                user_id=user_id,
                event_title=title,
                event_type=event_type,
                event_source="manual",
                event_start_time=start_time,
                event_end_time=end_time,
                event_location=location,
                event_description=description,
                event_link_url=related_link,
                event_is_completed=is_completed,
                event_show_in_todo=0,
                event_priority=priority_level,
                event_color_tag=color_tag,
                event_meta_json=meta_json,
            )
            self._bump_sync_state(user_id)
            return event_id

    def get_schedules_by_user(self, user_id: str) -> list[dict]:
        with _get_user_lock(user_id):
            return db.list_events_by_user(user_id, event_source="manual")

    def get_schedule_by_id(self, user_id: str, schedule_id: int) -> dict | None:
        with _get_user_lock(user_id):
            event = db.get_event(schedule_id)
            if event is None or event.get("user_id") != user_id:
                return None
            return event

    def update_schedule(
        self, user_id: str, schedule_id: int, title: str | None = None,
        start_time: str | None = None, end_time: str | None = None,
        priority_level: int | None = None, is_completed: int | None = None,
        location: str | None = None, description: str | None = None,
        related_link: str | None = None, recurrence_rule: str | None = None,
        color_tag: str | None = None,
    ) -> dict:
        with _get_user_lock(user_id):
            event = db.get_event(schedule_id)
            if event is None or event.get("user_id") != user_id:
                raise ValueError(f"Schedule not found: {schedule_id}")

            changed_fields = (
                title, start_time, end_time, priority_level,
                is_completed, location, description, related_link,
                recurrence_rule, color_tag,
            )
            if all(value is None for value in changed_fields):
                return event

            meta = {}
            if event.get("event_meta_json"):
                try:
                    meta = json.loads(event["event_meta_json"])
                except (json.JSONDecodeError, TypeError):
                    pass
            if recurrence_rule is not None:
                meta["recurrence_rule"] = recurrence_rule

            db.update_event(
                schedule_id,
                event_title=title,
                event_type=None,
                event_start_time=start_time,
                event_end_time=end_time,
                event_location=location,
                event_description=description,
                event_link_url=related_link,
                event_is_completed=is_completed,
                event_priority=priority_level,
                event_color_tag=color_tag,
                event_meta_json=json.dumps(meta) if meta else None,
            )
            self._bump_sync_state(user_id)
            updated = db.get_event(schedule_id)
            if updated is None:
                raise ValueError(f"Schedule not found: {schedule_id}")
            return updated

    def delete_schedule(self, user_id: str, schedule_id: int) -> None:
        with _get_user_lock(user_id):
            event = db.get_event(schedule_id)
            if event is None or event.get("user_id") != user_id:
                raise ValueError(f"Schedule not found: {schedule_id}")
            db.delete_event(schedule_id)
            self._bump_sync_state(user_id)

    def _require_user(self, user_id: str) -> None:
        if db.get_user(user_id) is None:
            import datetime as _dt
            db.upsert_user(
                user_id=user_id,
                username=user_id,
                user_email=user_id,
                user_is_active=1,
                user_created_at=_dt.datetime.utcnow().isoformat(),
                user_last_login=None,
                user_source_device_id=None,
            )

    def _bump_sync_state(self, user_id: str) -> None:
        now = _now_iso()
        sync_state = db.get_sync_state(user_id)
        if sync_state is None:
            db.upsert_sync_state(
                user_id=user_id, user_data_updated_at=now,
                user_last_synced_at=None, user_version=1, sync_updated_at=now,
            )
            return
        current_version = int(sync_state.get("user_version") or 1)
        db.upsert_sync_state(
            user_id=user_id, user_data_updated_at=now,
            user_last_synced_at=sync_state.get("user_last_synced_at"),
            user_version=current_version + 1, sync_updated_at=now,
        )
