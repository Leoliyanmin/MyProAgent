from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from .database_schedule_operations import ScheduleOperations
except ImportError:
    from database.code.database_schedule_operations import ScheduleOperations


def _load_request(request: dict[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(request, dict):
        return request
    if isinstance(request, Path):
        return json.loads(request.read_text(encoding="utf-8"))
    if isinstance(request, str):
        try:
            return json.loads(request)
        except json.JSONDecodeError:
            return json.loads(Path(request).read_text(encoding="utf-8"))
    raise TypeError("request must be dict, json string, or file path")


def _error(status: int, error_code: str, message: str, details: Any = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": False,
        "status": status,
        "error_code": error_code,
        "message": message,
    }
    if details is not None:
        payload["details"] = details
    return payload


def _coerce_schedule_id(schedule_id: Any) -> int | None:
    try:
        value = int(schedule_id)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _to_iso_datetime_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str) and value:
        normalized = value.replace("Z", "+00:00")
        try:
            datetime.fromisoformat(normalized)
        except ValueError:
            return None
        return value
    return None


def _normalize_schedule_priority(value: Any) -> int | None:
    if isinstance(value, int):
        priority = value
    elif isinstance(value, str):
        text = value.strip().lower()
        if not text:
            return None
        if text.startswith("p"):
            text = text[1:]
        try:
            priority = int(text)
        except ValueError:
            return None
    else:
        return None

    if priority in (0, 1, 2, 3):
        return priority
    return None


def _is_time_order_valid(start_time: str, end_time: str) -> bool:
    start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
    return end > start


class ScheduleHandle:
    """Local schedule function entry for API and agent calls."""

    def __init__(self) -> None:
        self.operations = ScheduleOperations()

    def create_schedule(self, user_id: str, title: str, start_time: Any, end_time: Any, **kwargs: Any) -> dict:
        if not user_id or not title:
            return _error(400, "SCHEDULE_INVALID_ARGUMENT", "user_id and title are required")

        normalized_start = _to_iso_datetime_str(start_time)
        normalized_end = _to_iso_datetime_str(end_time)
        if normalized_start is None or normalized_end is None:
            return _error(422, "SCHEDULE_TIME_INVALID", "start_time and end_time must be ISO-8601 datetime")

        if not _is_time_order_valid(normalized_start, normalized_end):
            return _error(422, "SCHEDULE_TIME_RANGE_INVALID", "end_time must be later than start_time")

        raw_priority = kwargs.get("priority")
        normalized_priority = 2 if raw_priority is None else _normalize_schedule_priority(raw_priority)
        if normalized_priority is None:
            return _error(422, "SCHEDULE_PRIORITY_INVALID", "priority must be one of p0, p1, p2, p3")

        try:
            schedule_id = self.operations.create_schedule(
                user_id=user_id,
                title=title,
                start_time=normalized_start,
                end_time=normalized_end,
                event_type=kwargs.get("event_type") or "personal",
                priority_level=normalized_priority,
                location=kwargs.get("location"),
                description=kwargs.get("description"),
                related_link=kwargs.get("related_link"),
                recurrence_rule=kwargs.get("recurrence_rule"),
                color_tag=kwargs.get("color_tag"),
            )
            schedule = self.operations.get_schedule_by_id(user_id=user_id, schedule_id=schedule_id)
            return {
                "ok": True,
                "status": 201,
                "data": {
                    "schedule_id": schedule_id,
                    "schedule": schedule,
                },
            }
        except ValueError as exc:
            return _error(404, "SCHEDULE_USER_NOT_FOUND", str(exc))
        except Exception as exc:  # pragma: no cover - defensive path
            return _error(500, "SCHEDULE_INTERNAL_ERROR", f"create schedule failed: {exc}")

    def get_schedules(self, user_id: str) -> dict:
        if not user_id:
            return _error(400, "SCHEDULE_INVALID_ARGUMENT", "user_id is required")

        try:
            schedules = self.operations.get_schedules_by_user(user_id)
            return {
                "ok": True,
                "status": 200,
                "data": schedules,
            }
        except Exception as exc:  # pragma: no cover - defensive path
            return _error(500, "SCHEDULE_INTERNAL_ERROR", f"get schedules failed: {exc}")

    def get_schedule(self, user_id: str, schedule_id: Any) -> dict:
        if not user_id:
            return _error(400, "SCHEDULE_INVALID_ARGUMENT", "user_id is required")

        normalized_schedule_id = _coerce_schedule_id(schedule_id)
        if normalized_schedule_id is None:
            return _error(400, "SCHEDULE_INVALID_ARGUMENT", "schedule_id must be a positive integer")

        try:
            schedule = self.operations.get_schedule_by_id(user_id=user_id, schedule_id=normalized_schedule_id)
            if schedule is None:
                return _error(404, "SCHEDULE_NOT_FOUND", f"Schedule not found: {normalized_schedule_id}")
            return {
                "ok": True,
                "status": 200,
                "data": schedule,
            }
        except Exception as exc:  # pragma: no cover - defensive path
            return _error(500, "SCHEDULE_INTERNAL_ERROR", f"get schedule failed: {exc}")

    def update_schedule(self, user_id: str, schedule_id: Any, **kwargs: Any) -> dict:
        if not user_id:
            return _error(400, "SCHEDULE_INVALID_ARGUMENT", "user_id is required")

        normalized_schedule_id = _coerce_schedule_id(schedule_id)
        if normalized_schedule_id is None:
            return _error(400, "SCHEDULE_INVALID_ARGUMENT", "schedule_id must be a positive integer")

        if kwargs.get("event_type") is not None:
            return _error(422, "SCHEDULE_UNSUPPORTED_FIELD", "event_type update is not supported by command layer")

        has_start_time = kwargs.get("start_time") is not None
        has_end_time = kwargs.get("end_time") is not None
        normalized_start = _to_iso_datetime_str(kwargs.get("start_time")) if has_start_time else None
        normalized_end = _to_iso_datetime_str(kwargs.get("end_time")) if has_end_time else None

        if has_start_time and normalized_start is None:
            return _error(422, "SCHEDULE_TIME_INVALID", "start_time must be ISO-8601 datetime")
        if has_end_time and normalized_end is None:
            return _error(422, "SCHEDULE_TIME_INVALID", "end_time must be ISO-8601 datetime")

        raw_priority = kwargs.get("priority")
        normalized_priority = None
        if raw_priority is not None:
            normalized_priority = _normalize_schedule_priority(raw_priority)
            if normalized_priority is None:
                return _error(422, "SCHEDULE_PRIORITY_INVALID", "priority must be one of p0, p1, p2, p3")

        try:
            existing = self.operations.get_schedule_by_id(user_id=user_id, schedule_id=normalized_schedule_id)
            if existing is None:
                return _error(404, "SCHEDULE_NOT_FOUND", f"Schedule not found: {normalized_schedule_id}")

            check_start = normalized_start or existing.get("schedule_start_time")
            check_end = normalized_end or existing.get("schedule_end_time")
            if isinstance(check_start, str) and isinstance(check_end, str):
                if not _is_time_order_valid(check_start, check_end):
                    return _error(422, "SCHEDULE_TIME_RANGE_INVALID", "end_time must be later than start_time")

            updated = self.operations.update_schedule(
                user_id=user_id,
                schedule_id=normalized_schedule_id,
                title=kwargs.get("title"),
                start_time=normalized_start,
                end_time=normalized_end,
                priority_level=normalized_priority,
                location=kwargs.get("location"),
                description=kwargs.get("description"),
                related_link=kwargs.get("related_link"),
                recurrence_rule=kwargs.get("recurrence_rule"),
                color_tag=kwargs.get("color_tag"),
            )
            return {
                "ok": True,
                "status": 200,
                "message": "schedule updated",
                "data": updated,
            }
        except ValueError as exc:
            return _error(404, "SCHEDULE_NOT_FOUND", str(exc))
        except Exception as exc:  # pragma: no cover - defensive path
            return _error(500, "SCHEDULE_INTERNAL_ERROR", f"update schedule failed: {exc}")

    def delete_schedule(self, user_id: str, schedule_id: Any) -> dict:
        if not user_id:
            return _error(400, "SCHEDULE_INVALID_ARGUMENT", "user_id is required")

        normalized_schedule_id = _coerce_schedule_id(schedule_id)
        if normalized_schedule_id is None:
            return _error(400, "SCHEDULE_INVALID_ARGUMENT", "schedule_id must be a positive integer")

        try:
            self.operations.delete_schedule(user_id, normalized_schedule_id)
            return {
                "ok": True,
                "status": 200,
                "message": "schedule deleted",
            }
        except ValueError as exc:
            return _error(404, "SCHEDULE_NOT_FOUND", str(exc))
        except Exception as exc:  # pragma: no cover - defensive path
            return _error(500, "SCHEDULE_INTERNAL_ERROR", f"delete schedule failed: {exc}")

    def handle(self, action: str, payload: Any = None) -> dict:
        action_name = (action or "").strip().lower()

        if action_name in {"create", "create_schedule"}:
            if not isinstance(payload, dict):
                return _error(400, "SCHEDULE_INVALID_ARGUMENT", "payload must be object")
            return self.create_schedule(
                user_id=str(payload.get("user_id") or ""),
                title=str(payload.get("title") or ""),
                start_time=payload.get("start_time"),
                end_time=payload.get("end_time"),
                event_type=payload.get("event_type"),
                priority=payload.get("priority"),
                location=payload.get("location"),
                description=payload.get("description"),
                related_link=payload.get("related_link"),
                recurrence_rule=payload.get("recurrence_rule"),
                color_tag=payload.get("color_tag"),
            )

        if action_name in {"list", "list_schedules", "get_schedules"}:
            if isinstance(payload, dict):
                user_id = payload.get("user_id")
            else:
                user_id = payload
            return self.get_schedules(str(user_id or ""))

        if action_name in {"get", "get_schedule"}:
            if not isinstance(payload, dict):
                return _error(400, "SCHEDULE_INVALID_ARGUMENT", "payload must be object")
            return self.get_schedule(
                user_id=str(payload.get("user_id") or ""),
                schedule_id=payload.get("schedule_id"),
            )

        if action_name in {"update", "update_schedule"}:
            if not isinstance(payload, dict):
                return _error(400, "SCHEDULE_INVALID_ARGUMENT", "payload must be object")
            return self.update_schedule(
                user_id=str(payload.get("user_id") or ""),
                schedule_id=payload.get("schedule_id"),
                title=payload.get("title"),
                start_time=payload.get("start_time"),
                end_time=payload.get("end_time"),
                location=payload.get("location"),
                description=payload.get("description"),
                related_link=payload.get("related_link"),
                recurrence_rule=payload.get("recurrence_rule"),
                color_tag=payload.get("color_tag"),
                priority=payload.get("priority"),
                event_type=payload.get("event_type"),
            )

        if action_name in {"delete", "delete_schedule"}:
            if not isinstance(payload, dict):
                return _error(400, "SCHEDULE_INVALID_ARGUMENT", "payload must be object")
            return self.delete_schedule(
                user_id=str(payload.get("user_id") or ""),
                schedule_id=payload.get("schedule_id"),
            )

        return _error(400, "SCHEDULE_ACTION_INVALID", f"unsupported action: {action}")


def handle_schedule_request(request: dict[str, Any] | str | Path) -> dict[str, Any]:
    content = _load_request(request)
    action = content.get("action")
    if not action:
        return _error(400, "SCHEDULE_ACTION_REQUIRED", "action is required")

    handler = ScheduleHandle()
    return handler.handle(action=str(action), payload=content.get("payload"))