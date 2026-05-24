"""TIS tools for LocalAgent — unified event table."""

from __future__ import annotations

from typing import Any, Callable
from collections import defaultdict

from .base import BaseTool
from local_backend.database.code.command.database_command import list_events_by_user

_WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


class _Base(BaseTool):
    def __init__(self, getter: Callable[[], str | None]):
        self._getter = getter

    def _auth(self) -> tuple[str | None, str | None]:
        uid = self._getter()
        return (uid, None) if uid else (None, "Error: Missing user context.")


class GetTisStatusTool(_Base):
    name = "get_tis_status"
    description = "Check TIS bind status."
    parameters = {"type": "object", "properties": {}, "required": []}

    async def execute(self, **kwargs) -> str:
        uid, err = self._auth()
        if err: return err
        events = list_events_by_user(uid, event_source="tis", event_type="course")
        if not events:
            return "TIS is not bound. Please go to Settings to bind your TIS account first."
        unique = len({e["event_title"] for e in events})
        return f"TIS Status:\n  Status: Bound\n  Courses: {unique}\n  Events: {len(events)}"


class GetTisScheduleTool(_Base):
    name = "get_tis_schedule"
    description = "Get TIS course schedule. Call when user asks about classes or schedule."
    parameters = {
        "type": "object",
        "properties": {"current_week": {"type": "integer", "description": "Optional week"}},
        "required": [],
    }

    async def execute(self, **kwargs) -> str:
        uid, err = self._auth()
        if err: return err

        events = list_events_by_user(uid, event_source="tis", event_type="course")
        if not events:
            return "No TIS courses found. Please bind and sync TIS first."

        cw = kwargs.get("current_week")
        if cw is not None:
            try: cw = int(cw)
            except: cw = None

        by_day: dict[int, list[dict]] = defaultdict(list)
        import json
        for e in events:
            try:
                meta = json.loads(e.get("event_meta_json", "{}") or "{}")
            except Exception:
                meta = {}
            wn, dow = meta.get("week_num", 1), meta.get("day_of_week", 0)
            if cw is not None and wn != cw:
                continue
            by_day[dow].append(e)

        if not by_day:
            return "No schedule events found." + (f" (Week {cw})" if cw else "")

        lines = ["TIS Course Schedule:", ""]
        for day in sorted(by_day.keys()):
            dn = _WEEKDAY_NAMES[day - 1] if 1 <= day <= 7 else f"Day {day}"
            lines.append(f"--- {dn} ---")
            for e in by_day[day]:
                try:
                    meta = json.loads(e.get("event_meta_json", "{}") or "{}")
                except Exception:
                    meta = {}
                teacher = meta.get("teacher", "")
                ps, pe = meta.get("period_start", ""), meta.get("period_end", "")
                wn = meta.get("week_num", "")
                st = (e.get("event_start_time") or "")[11:16]
                et = (e.get("event_end_time") or "")[11:16]
                detail = f"  {e['event_title']}"
                if st: detail += f" | {st}-{et}"
                elif ps: detail += f" | Period {ps}-{pe}"
                if e.get("event_location"): detail += f" | {e['event_location']}"
                if wn: detail += f" | Week {wn}"
                if teacher: detail += f" | {teacher}"
                lines.append(detail)
            lines.append("")
        return "\n".join(lines).strip()
