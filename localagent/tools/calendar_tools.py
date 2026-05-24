"""Calendar event tools for LocalAgent — unified event table."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from .base import BaseTool

from local_backend.database.code.command.database_command import (
    create_event, update_event, delete_event,
    list_events_by_user,
)


def _normalize_iso(value: Any, fallback: str = "00:00:00") -> str | None:
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
        text = f"{text}T{fallback}"
    date_part, time_part = text.split("T", 1)
    if len(time_part) == 5 and time_part.count(":") == 1:
        text = f"{date_part}T{time_part}:00"
    try:
        return datetime.fromisoformat(text).isoformat()
    except ValueError:
        return None


def _fmt_time(st: str, et: str) -> str:
    s, e = st[:10] if st else "", et[:10] if et else ""
    s_t = st[11:16] if st and len(st) > 16 else ""
    e_t = et[11:16] if et and len(et) > 16 else ""
    if s == e and s_t == "00:00" and e_t in ("23:59", "23:59:00"):
        return f"{s}（全天）"
    if s == e and s_t and e_t:
        return f"{s} {s_t}-{e_t}"
    if s_t and e_t:
        return f"{s} {s_t} - {e} {e_t}"
    return f"{s} - {e}"


class _Base(BaseTool):
    def __init__(self, user_id_getter: Callable[[], str | None]):
        self._uid = user_id_getter

    def _auth(self) -> tuple[str | None, str | None]:
        uid = self._uid()
        return (uid, None) if uid else (None, "Error: Missing user context.")

    def _resolve(self, uid: str, eid: Any, kw: str | None) -> tuple[int | None, str | None]:
        if eid is not None:
            try:
                return int(eid), None
            except (TypeError, ValueError):
                return None, "Error: event_id must be a number"
        kw = (kw or "").strip().lower()
        if not kw:
            return None, "Error: Provide event_id or title_keyword"
        for r in list_events_by_user(uid):
            if kw in str(r.get("event_title", "")).lower():
                return r["event_id"], None
        return None, f"Error: No event matching '{kw}'"


class CreateScheduleEventTool(_Base):
    name = "create_schedule_event"
    description = "Create a calendar event or todo for the user. Provide ISO-8601 datetimes like '2026-05-25T15:00:00'."
    parameters = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Event title"},
            "start_time": {"type": "string", "description": "Start datetime ISO-8601"},
            "end_time": {"type": "string", "description": "End datetime ISO-8601"},
            "description": {"type": "string"},
            "location": {"type": "string"},
            "priority": {"type": "integer", "description": "0-3, default 2"},
            "color_tag": {"type": "string", "description": "Hex color"},
            "show_in_todo": {"type": "boolean", "description": "Show in TodoWidget? Default true"},
        },
        "required": ["title", "start_time", "end_time"],
    }

    async def execute(self, **kwargs) -> str:
        uid, err = self._auth()
        if err:
            return err
        title = str(kwargs.get("title") or "").strip()
        if not title:
            return "Error: title is required"
        st = _normalize_iso(kwargs.get("start_time"), "00:00:00")
        et = _normalize_iso(kwargs.get("end_time"), "23:59:00")
        if not st or not et:
            return "Error: invalid datetime format"
        todo = 1 if kwargs.get("show_in_todo", True) else 0
        eid = create_event(
            user_id=uid, event_title=title,
            event_type="agent", event_source="manual",
            event_start_time=st, event_end_time=et,
            event_location=kwargs.get("location"),
            event_description=kwargs.get("description"),
            event_show_in_todo=todo,
            event_priority=int(kwargs.get("priority", 2)),
            event_color_tag=kwargs.get("color_tag", "#007aff"),
        )
        return f"Event created: event_id={eid}, title={title}, time: {_fmt_time(st, et)}"


class UpdateScheduleEventTool(_Base):
    name = "update_schedule_event"
    description = "Update an event by event_id or title keyword."
    parameters = {
        "type": "object",
        "properties": {
            "event_id": {"type": "integer"},
            "title_keyword": {"type": "string"},
            "title": {"type": "string"},
            "start_time": {"type": "string"},
            "end_time": {"type": "string"},
            "description": {"type": "string"},
            "location": {"type": "string"},
            "priority": {"type": "integer"},
            "color_tag": {"type": "string"},
            "show_in_todo": {"type": "boolean"},
            "completed": {"type": "boolean"},
        },
        "required": [],
    }

    async def execute(self, **kwargs) -> str:
        uid, err = self._auth()
        if err:
            return err
        eid, err = self._resolve(uid, kwargs.get("event_id"), kwargs.get("title_keyword"))
        if err:
            return err
        up = {}
        for k, col in [("title", "event_title"), ("description", "event_description"),
                        ("location", "event_location"), ("priority", "event_priority"),
                        ("color_tag", "event_color_tag")]:
            if kwargs.get(k) is not None:
                up[col] = kwargs[k]
        if kwargs.get("start_time") is not None:
            v = _normalize_iso(kwargs["start_time"], "00:00:00")
            if not v: return "Error: invalid start_time"
            up["event_start_time"] = v
        if kwargs.get("end_time") is not None:
            v = _normalize_iso(kwargs["end_time"], "23:59:00")
            if not v: return "Error: invalid end_time"
            up["event_end_time"] = v
        if kwargs.get("show_in_todo") is not None:
            up["event_show_in_todo"] = 1 if kwargs["show_in_todo"] else 0
        if kwargs.get("completed") is not None:
            up["event_is_completed"] = 1 if kwargs["completed"] else 0
        if not up:
            return "Error: nothing to update"
        update_event(event_id=eid, **up)
        return f"Event updated: event_id={eid}"


class UpdateScheduleEventTimeTool(_Base):
    name = "update_schedule_event_time"
    description = "Update only start/end time."
    parameters = {
        "type": "object",
        "properties": {
            "event_id": {"type": "integer"},
            "title_keyword": {"type": "string"},
            "start_time": {"type": "string"},
            "end_time": {"type": "string"},
        },
        "required": ["start_time", "end_time"],
    }

    async def execute(self, **kwargs) -> str:
        uid, err = self._auth()
        if err:
            return err
        eid, err = self._resolve(uid, kwargs.get("event_id"), kwargs.get("title_keyword"))
        if err:
            return err
        st = _normalize_iso(kwargs["start_time"], "00:00:00")
        et = _normalize_iso(kwargs["end_time"], "23:59:00")
        if not st or not et:
            return "Error: invalid datetime"
        update_event(event_id=eid, event_start_time=st, event_end_time=et)
        return f"Event time updated: event_id={eid}"


class DeleteScheduleEventTool(_Base):
    name = "delete_schedule_event"
    description = "Delete an event by event_id or title keyword."
    parameters = {
        "type": "object",
        "properties": {
            "event_id": {"type": "integer"},
            "title_keyword": {"type": "string"},
        },
        "required": [],
    }

    async def execute(self, **kwargs) -> str:
        uid, err = self._auth()
        if err:
            return err
        eid, err = self._resolve(uid, kwargs.get("event_id"), kwargs.get("title_keyword"))
        if err:
            return err
        delete_event(eid)
        return f"Event deleted: event_id={eid}"
