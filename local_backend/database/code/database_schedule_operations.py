from __future__ import annotations

import threading
from datetime import datetime, timezone

try:
    from . import database_command as db
except ImportError:
    import database_command as db

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
    """Local schedule database operations for agent and API flows."""

    def create_schedule(
        self,
        user_id: str,
        title: str,
        start_time: str,
        end_time: str,
        event_type: str = "personal",
        location: str | None = None,
        description: str | None = None,
        related_link: str | None = None,
        recurrence_rule: str | None = None,
        color_tag: str | None = None,
    ) -> int:
        with _get_user_lock(user_id):
            self._require_user(user_id)
            schedule_id = db.create_schedule(
                user_id=user_id,
                schedule_event_type=event_type,
                schedule_title=title,
                schedule_start_time=start_time,
                schedule_end_time=end_time,
                schedule_location=location,
                schedule_description=description,
                schedule_related_link=related_link,
                schedule_recurrence_rule=recurrence_rule,
                schedule_color_tag=color_tag,
            )
            self._bump_sync_state(user_id)
            return schedule_id

    def get_schedules_by_user(self, user_id: str) -> list[dict]:
        with _get_user_lock(user_id):
            return db.list_schedule_by_user(user_id)

    def get_schedule_by_id(self, user_id: str, schedule_id: int) -> dict | None:
        with _get_user_lock(user_id):
            schedule = db.get_schedule(schedule_id)
            if schedule is None or schedule.get("user_id") != user_id:
                return None
            return schedule

    def update_schedule(
        self,
        user_id: str,
        schedule_id: int,
        title: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        location: str | None = None,
        description: str | None = None,
        related_link: str | None = None,
        recurrence_rule: str | None = None,
        color_tag: str | None = None,
    ) -> dict:
        with _get_user_lock(user_id):
            schedule = db.get_schedule(schedule_id)
            if schedule is None or schedule.get("user_id") != user_id:
                raise ValueError(f"Schedule not found: {schedule_id}")

            changed_fields = (
                title,
                start_time,
                end_time,
                location,
                description,
                related_link,
                recurrence_rule,
                color_tag,
            )
            if all(value is None for value in changed_fields):
                return schedule

            db.update_schedule(
                schedule_id=schedule_id,
                schedule_title=title,
                schedule_start_time=start_time,
                schedule_end_time=end_time,
                schedule_location=location,
                schedule_description=description,
                schedule_related_link=related_link,
                schedule_recurrence_rule=recurrence_rule,
                schedule_color_tag=color_tag,
            )
            self._bump_sync_state(user_id)
            updated = db.get_schedule(schedule_id)
            if updated is None:
                raise ValueError(f"Schedule not found: {schedule_id}")
            return updated

    def delete_schedule(self, user_id: str, schedule_id: int) -> None:
        with _get_user_lock(user_id):
            schedule = db.get_schedule(schedule_id)
            if schedule is None or schedule.get("user_id") != user_id:
                raise ValueError(f"Schedule not found: {schedule_id}")

            db.delete_schedule(schedule_id)
            self._bump_sync_state(user_id)

    def _require_user(self, user_id: str) -> None:
        if db.get_user(user_id) is None:
            raise ValueError(f"User not found: {user_id}")

    def _bump_sync_state(self, user_id: str) -> None:
        now = _now_iso()
        sync_state = db.get_sync_state(user_id)

        if sync_state is None:
            db.upsert_sync_state(
                user_id=user_id,
                user_data_updated_at=now,
                user_last_synced_at=None,
                user_version=1,
                sync_updated_at=now,
            )
            return

        current_version = int(sync_state.get("user_version") or 1)
        db.upsert_sync_state(
            user_id=user_id,
            user_data_updated_at=now,
            user_last_synced_at=sync_state.get("user_last_synced_at"),
            user_version=current_version + 1,
            sync_updated_at=now,
        )