"""Calendar event tools for LocalAgent."""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any, Callable

from .base import BaseTool

try:
    from database.code.handle.database_schedule_handle import ScheduleHandle
except Exception:  # pragma: no cover
    try:
        from local_backend.database.code.handle.database_schedule_handle import ScheduleHandle
    except Exception:  # pragma: no cover
        ScheduleHandle = None

try:
    from database.code.handle.database_task_handle import TaskHandle
except Exception:  # pragma: no cover
    try:
        from local_backend.database.code.handle.database_task_handle import TaskHandle
    except Exception:  # pragma: no cover
        TaskHandle = None


_SCHEDULE_TASK_LINK_RE = re.compile(r"\[SCHEDULE_LINK:(\d+)\]")


def _format_time_for_display(start_time: str, end_time: str) -> str:
    s = start_time[:10] if start_time else ""
    e = end_time[:10] if end_time else ""
    st = start_time[11:16] if start_time and len(start_time) > 16 else ""
    et = end_time[11:16] if end_time and len(end_time) > 16 else ""
    if s == e and st == "00:00" and et in ("23:59", "23:59:00"):
        return f"{s}（全天）"
    if s == e and st and et:
        return f"{s} {st}-{et}"
    if s != e and st == "00:00" and et in ("23:59", "23:59:00", "00:00"):
        return f"{s} 至 {e}（全天）"
    if st and et:
        return f"{s} {st} - {e} {et}"
    return f"{s} - {e}"


def _normalize_iso_datetime(value: Any, fallback_time: str = "00:00:00") -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if not isinstance(value, str):
        return None

    text = value.strip()
    if not text:
        return None

    text = text.replace("Z", "+00:00")
    if "T" not in text and " " in text:
        text = text.replace(" ", "T", 1)
    if "T" not in text:
        text = f"{text}T{fallback_time}"

    date_part, time_part = text.split("T", 1)
    if "+" in time_part or "-" in time_part[1:]:
        time_core = time_part
    else:
        time_core = time_part

    if len(time_core) == 5 and time_core.count(":") == 1:
        text = f"{date_part}T{time_core}:00"

    try:
        return datetime.fromisoformat(text).isoformat()
    except ValueError:
        return None


def _normalize_priority(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, int):
        if value in (0, 1, 2, 3):
            return f"p{value}"
        return None

    text = str(value).strip().lower()
    if not text:
        return None
    if text in {"p0", "p1", "p2", "p3"}:
        return text
    if text in {"0", "1", "2", "3"}:
        return f"p{text}"
    return None


def _coerce_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


class _ScheduleToolBase(BaseTool):
    def __init__(self, user_id_getter: Callable[[], str | None]):
        self._user_id_getter = user_id_getter
        self._handle = ScheduleHandle() if ScheduleHandle is not None else None
        self._task_handle = TaskHandle() if TaskHandle is not None else None

    def _require_user(self) -> tuple[str | None, str | None]:
        if self._handle is None:
            return None, "Error: Schedule backend is unavailable"

        user_id = self._user_id_getter()
        if not user_id:
            return None, "Error: Missing user context. Please login first."
        return user_id, None

    def _resolve_schedule_id(
        self,
        user_id: str,
        schedule_id: Any,
        title_keyword: str | None,
    ) -> tuple[int | None, str | None]:
        if schedule_id is not None:
            try:
                sid = int(schedule_id)
            except (TypeError, ValueError):
                return None, "Error: schedule_id must be a positive integer"
            if sid <= 0:
                return None, "Error: schedule_id must be a positive integer"
            return sid, None

        keyword = (title_keyword or "").strip().lower()
        if not keyword:
            return None, "Error: Provide schedule_id or title_keyword"

        result = self._handle.get_schedules(user_id)
        if not result.get("ok"):
            return None, f"Error: {result.get('message', 'Failed to list schedules')}"

        schedules = result.get("data", [])
        for item in schedules:
            title = str(item.get("schedule_title") or item.get("title") or "").lower()
            if keyword in title:
                sid = item.get("schedule_id") or item.get("id")
                try:
                    return int(sid), None
                except (TypeError, ValueError):
                    continue

        return None, f"Error: No schedule found by title keyword '{title_keyword}'"

    @staticmethod
    def _task_id_from_record(task: dict[str, Any]) -> int | None:
        raw = task.get("data_id") or task.get("task_id") or task.get("id")
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return None
        return value if value > 0 else None

    def _find_linked_task(self, user_id: str, schedule_id: int) -> tuple[dict[str, Any] | None, str | None]:
        """Find the task linked to a schedule by data_linked_schedule_id column.

        Falls back to [SCHEDULE_LINK:id] string matching in description for
        backward compatibility with tasks created before the migration.
        """
        if self._task_handle is None:
            return None, "Task backend is unavailable"

        result = self._task_handle.get_tasks(user_id)
        if not result.get("ok"):
            return None, result.get("message", "Failed to list tasks")

        for task in result.get("data", []):
            linked_id = task.get("data_linked_schedule_id")
            if linked_id is not None:
                try:
                    if int(linked_id) == schedule_id:
                        return task, None
                except (TypeError, ValueError):
                    pass

            description = str(task.get("data_content_text") or task.get("description") or "")
            match = _SCHEDULE_TASK_LINK_RE.search(description)
            if match:
                try:
                    if int(match.group(1)) == schedule_id:
                        return task, None
                except (TypeError, ValueError):
                    continue

        return None, None

    def _upsert_linked_task(
        self,
        user_id: str,
        schedule_id: int,
        title: str,
        end_time: str,
        description: Any = None,
    ) -> tuple[int | None, str | None, bool]:
        if self._task_handle is None:
            return None, "Task backend is unavailable", False

        existing_task, find_error = self._find_linked_task(user_id, schedule_id)
        if find_error:
            return None, find_error, False

        if existing_task is not None:
            task_id = self._task_id_from_record(existing_task)
            if task_id is None:
                return None, "Linked task id is invalid", False

            update_result = self._task_handle.update_task(
                user_id=user_id,
                task_id=task_id,
                title=title,
                linked_schedule_id=schedule_id,
                due_date=end_time,
            )
            if not update_result.get("ok"):
                return None, update_result.get("message", "Failed to update linked task"), False
            return task_id, None, False

        create_result = self._task_handle.create_task(
            user_id=user_id,
            title=title,
            linked_schedule_id=schedule_id,
            due_date=end_time,
        )
        if not create_result.get("ok"):
            return None, create_result.get("message", "Failed to create linked task"), False
        return create_result.get("data", {}).get("task_id"), None, True

    def _delete_linked_task(self, user_id: str, schedule_id: int) -> tuple[bool, str | None]:
        if self._task_handle is None:
            return False, "Task backend is unavailable"

        existing_task, find_error = self._find_linked_task(user_id, schedule_id)
        if find_error:
            return False, find_error
        if existing_task is None:
            return False, None

        task_id = self._task_id_from_record(existing_task)
        if task_id is None:
            return False, "Linked task id is invalid"

        delete_result = self._task_handle.delete_task(user_id=user_id, task_id=task_id)
        if not delete_result.get("ok"):
            return False, delete_result.get("message", "Failed to delete linked task")
        return True, None

    def _get_schedule_data(self, user_id: str, schedule_id: int) -> tuple[dict[str, Any] | None, str | None]:
        get_result = self._handle.get_schedule(user_id=user_id, schedule_id=schedule_id)
        if not get_result.get("ok"):
            return None, get_result.get("message", "Failed to fetch schedule")
        return get_result.get("data") or {}, None


class CreateScheduleEventTool(_ScheduleToolBase):
    name = "create_schedule_event"
    description = "Create a calendar event for current user. For all-day events, use start_time as the date at 00:00 and end_time as the same date at 23:59. Always provide explicit ISO-8601 datetimes, e.g. '2026-04-20T15:00:00', never relative terms."
    parameters = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Event title"},
            "start_time": {"type": "string", "description": "Start datetime in ISO-8601"},
            "end_time": {"type": "string", "description": "End datetime in ISO-8601"},
            "description": {"type": "string", "description": "Optional description"},
            "location": {"type": "string", "description": "Optional location"},
            "priority": {"type": "string", "description": "Optional priority: p0/p1/p2/p3"},
            "color_tag": {"type": "string", "description": "Optional color hex"},
            "sync_to_todo": {
                "type": "boolean",
                "description": "Default true. When true, create a linked TODO item too. Set false only when user explicitly asks calendar-only.",
            },
        },
        "required": ["title", "start_time", "end_time"],
    }

    async def execute(self, **kwargs) -> str:
        user_id, error = self._require_user()
        if error:
            return error

        title = str(kwargs.get("title") or "").strip()
        if not title:
            return "Error: title is required"

        start_time = _normalize_iso_datetime(kwargs.get("start_time"), fallback_time="00:00:00")
        end_time = _normalize_iso_datetime(kwargs.get("end_time"), fallback_time="23:59:00")
        if not start_time or not end_time:
            return "Error: start_time/end_time must be valid ISO-8601 datetime"

        priority = _normalize_priority(kwargs.get("priority"))
        if kwargs.get("priority") is not None and priority is None:
            return "Error: priority must be p0/p1/p2/p3"

        sync_to_todo = _coerce_bool(kwargs.get("sync_to_todo"), True)

        result = self._handle.create_schedule(
            user_id=user_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            event_type="personal",
            priority=priority,
            location=kwargs.get("location"),
            description=kwargs.get("description"),
            color_tag=kwargs.get("color_tag"),
        )
        if not result.get("ok"):
            return f"Error: {result.get('message', 'create schedule failed')}"

        schedule_id_raw = result.get("data", {}).get("schedule_id")
        try:
            schedule_id = int(schedule_id_raw)
        except (TypeError, ValueError):
            return "Error: schedule created but schedule_id is missing or invalid"
        if not sync_to_todo:
            return (
                f"创建日程成功: schedule_id={schedule_id}, title={title}, "
                f"时间: {_format_time_for_display(start_time, end_time)}. "
                "按要求仅写入日程。"
            )

        task_id, task_error, created = self._upsert_linked_task(
            user_id=user_id,
            schedule_id=int(schedule_id),
            title=title,
            end_time=end_time,
            description=kwargs.get("description"),
        )
        if task_error:
            return (
                f"创建日程成功: schedule_id={schedule_id}, title={title}, "
                f"时间: {_format_time_for_display(start_time, end_time)}. "
                f"但同步 TODO 失败: {task_error}"
            )

        task_sync_text = "已同步创建" if created else "已同步更新"
        return (
            f"创建日程成功: schedule_id={schedule_id}, title={title}, "
            f"时间: {_format_time_for_display(start_time, end_time)}. "
            f"{task_sync_text} TODO: task_id={task_id}"
        )


class UpdateScheduleEventTool(_ScheduleToolBase):
    name = "update_schedule_event"
    description = "Update a schedule event by schedule_id or title_keyword."
    parameters = {
        "type": "object",
        "properties": {
            "schedule_id": {"type": "integer", "description": "Schedule ID to update"},
            "title_keyword": {"type": "string", "description": "Fallback matcher when schedule_id not provided"},
            "title": {"type": "string", "description": "New title"},
            "start_time": {"type": "string", "description": "New start time (ISO-8601)"},
            "end_time": {"type": "string", "description": "New end time (ISO-8601)"},
            "description": {"type": "string", "description": "New description"},
            "location": {"type": "string", "description": "New location"},
            "priority": {"type": "string", "description": "New priority: p0/p1/p2/p3"},
            "color_tag": {"type": "string", "description": "New color"},
            "sync_to_todo": {
                "type": "boolean",
                "description": "Default true. Keep linked TODO in sync. Set false only when user explicitly asks calendar-only updates.",
            },
        },
        "required": [],
    }

    async def execute(self, **kwargs) -> str:
        user_id, error = self._require_user()
        if error:
            return error

        schedule_id, error = self._resolve_schedule_id(
            user_id=user_id,
            schedule_id=kwargs.get("schedule_id"),
            title_keyword=kwargs.get("title_keyword"),
        )
        if error:
            return error

        start_time = None
        end_time = None
        if kwargs.get("start_time") is not None:
            start_time = _normalize_iso_datetime(kwargs.get("start_time"), fallback_time="00:00:00")
            if not start_time:
                return "Error: start_time must be valid ISO-8601 datetime"
        if kwargs.get("end_time") is not None:
            end_time = _normalize_iso_datetime(kwargs.get("end_time"), fallback_time="23:59:00")
            if not end_time:
                return "Error: end_time must be valid ISO-8601 datetime"

        priority = None
        if kwargs.get("priority") is not None:
            priority = _normalize_priority(kwargs.get("priority"))
            if priority is None:
                return "Error: priority must be p0/p1/p2/p3"

        sync_to_todo = _coerce_bool(kwargs.get("sync_to_todo"), True)

        result = self._handle.update_schedule(
            user_id=user_id,
            schedule_id=schedule_id,
            title=kwargs.get("title"),
            start_time=start_time,
            end_time=end_time,
            location=kwargs.get("location"),
            description=kwargs.get("description"),
            color_tag=kwargs.get("color_tag"),
            priority=priority,
        )
        if not result.get("ok"):
            return f"Error: {result.get('message', 'update schedule failed')}"

        if not sync_to_todo:
            return f"更新日程成功: schedule_id={schedule_id}（按要求仅更新日程）"

        schedule_data, schedule_error = self._get_schedule_data(user_id, schedule_id)
        if schedule_error:
            return f"更新日程成功: schedule_id={schedule_id}，但读取更新后的日程失败: {schedule_error}"

        task_id, task_error, created = self._upsert_linked_task(
            user_id=user_id,
            schedule_id=schedule_id,
            title=str(schedule_data.get("schedule_title") or schedule_data.get("title") or kwargs.get("title") or "未命名日程"),
            end_time=str(schedule_data.get("schedule_end_time") or schedule_data.get("end_time") or end_time or ""),
            description=schedule_data.get("schedule_description") or schedule_data.get("description") or kwargs.get("description"),
        )
        if task_error:
            return f"更新日程成功: schedule_id={schedule_id}，但同步 TODO 失败: {task_error}"

        task_sync_text = "已同步创建" if created else "已同步更新"
        return f"更新日程成功: schedule_id={schedule_id}，{task_sync_text} TODO: task_id={task_id}"


class UpdateScheduleEventTimeTool(_ScheduleToolBase):
    name = "update_schedule_event_time"
    description = "Update only start_time and end_time for a schedule event."
    parameters = {
        "type": "object",
        "properties": {
            "schedule_id": {"type": "integer", "description": "Schedule ID to update"},
            "title_keyword": {"type": "string", "description": "Fallback matcher when schedule_id not provided"},
            "start_time": {"type": "string", "description": "New start time in ISO-8601"},
            "end_time": {"type": "string", "description": "New end time in ISO-8601"},
            "sync_to_todo": {
                "type": "boolean",
                "description": "Default true. Keep linked TODO due time in sync.",
            },
        },
        "required": ["start_time", "end_time"],
    }

    async def execute(self, **kwargs) -> str:
        user_id, error = self._require_user()
        if error:
            return error

        schedule_id, error = self._resolve_schedule_id(
            user_id=user_id,
            schedule_id=kwargs.get("schedule_id"),
            title_keyword=kwargs.get("title_keyword"),
        )
        if error:
            return error

        start_time = _normalize_iso_datetime(kwargs.get("start_time"), fallback_time="00:00:00")
        end_time = _normalize_iso_datetime(kwargs.get("end_time"), fallback_time="23:59:00")
        if not start_time or not end_time:
            return "Error: start_time/end_time must be valid ISO-8601 datetime"

        sync_to_todo = _coerce_bool(kwargs.get("sync_to_todo"), True)

        result = self._handle.update_schedule(
            user_id=user_id,
            schedule_id=schedule_id,
            start_time=start_time,
            end_time=end_time,
        )
        if not result.get("ok"):
            return f"Error: {result.get('message', 'update schedule time failed')}"

        if not sync_to_todo:
            return f"更新时间成功: schedule_id={schedule_id}, start_time={start_time}, end_time={end_time}（按要求仅更新日程）"

        schedule_data, schedule_error = self._get_schedule_data(user_id, schedule_id)
        if schedule_error:
            return (
                f"更新时间成功: schedule_id={schedule_id}, start_time={start_time}, end_time={end_time}，"
                f"但读取更新后的日程失败: {schedule_error}"
            )

        task_id, task_error, created = self._upsert_linked_task(
            user_id=user_id,
            schedule_id=schedule_id,
            title=str(schedule_data.get("schedule_title") or schedule_data.get("title") or "未命名日程"),
            end_time=str(schedule_data.get("schedule_end_time") or schedule_data.get("end_time") or end_time),
            description=schedule_data.get("schedule_description") or schedule_data.get("description"),
        )
        if task_error:
            return (
                f"更新时间成功: schedule_id={schedule_id}, start_time={start_time}, end_time={end_time}，"
                f"但同步 TODO 失败: {task_error}"
            )

        task_sync_text = "已同步创建" if created else "已同步更新"
        return (
            f"更新时间成功: schedule_id={schedule_id}, start_time={start_time}, end_time={end_time}，"
            f"{task_sync_text} TODO: task_id={task_id}"
        )


class DeleteScheduleEventTool(_ScheduleToolBase):
    name = "delete_schedule_event"
    description = "Delete a schedule event by schedule_id or title_keyword."
    parameters = {
        "type": "object",
        "properties": {
            "schedule_id": {"type": "integer", "description": "Schedule ID to delete"},
            "title_keyword": {"type": "string", "description": "Fallback matcher when schedule_id not provided"},
            "delete_todo_too": {
                "type": "boolean",
                "description": "Default true. Delete linked TODO item together.",
            },
        },
        "required": [],
    }

    async def execute(self, **kwargs) -> str:
        user_id, error = self._require_user()
        if error:
            return error

        schedule_id, error = self._resolve_schedule_id(
            user_id=user_id,
            schedule_id=kwargs.get("schedule_id"),
            title_keyword=kwargs.get("title_keyword"),
        )
        if error:
            return error

        delete_todo_too = _coerce_bool(kwargs.get("delete_todo_too"), True)

        result = self._handle.delete_schedule(user_id=user_id, schedule_id=schedule_id)
        if not result.get("ok"):
            return f"Error: {result.get('message', 'delete schedule failed')}"

        if not delete_todo_too:
            return f"删除日程成功: schedule_id={schedule_id}（按要求仅删除日程）"

        deleted_task, task_error = self._delete_linked_task(user_id, schedule_id)
        if task_error:
            return f"删除日程成功: schedule_id={schedule_id}，但删除关联 TODO 失败: {task_error}"
        if deleted_task:
            return f"删除日程成功: schedule_id={schedule_id}，已同步删除关联 TODO"
        return f"删除日程成功: schedule_id={schedule_id}（未找到关联 TODO）"
