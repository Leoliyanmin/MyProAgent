"""Course listing tools — unified event table."""

from __future__ import annotations

from .base import BaseTool
from local_backend.database.code.command.database_command import list_events_by_user


class _Base(BaseTool):
    def __init__(self, getter: Callable[[], str | None]):
        self._getter = getter

    def _auth(self):
        uid = self._getter()
        return (uid, None) if uid else (None, "Error: Missing user context.")


class ListCoursesTool(_Base):
    name = "list_courses"
    description = "List TIS courses for the user."
    parameters = {"type": "object", "properties": {}, "required": []}

    async def execute(self, **kwargs) -> str:
        uid, err = self._auth()
        if err: return err

        events = list_events_by_user(uid, event_source="tis", event_type="course")
        if not events:
            return "No courses found in TIS. Please bind and sync TIS first."

        import json
        seen = set()
        lines = []
        for e in events:
            title = e["event_title"]
            if title in seen: continue
            seen.add(title)
            try:
                meta = json.loads(e.get("event_meta_json", "{}") or "{}")
            except Exception:
                meta = {}
            teacher = meta.get("teacher", "")
            loc = e.get("event_location", "")
            line = f"  {title}"
            if teacher: line += f" — {teacher}"
            if loc: line += f" @ {loc}"
            lines.append(line)

        return f"You have {len(seen)} course(s):\n" + "\n".join(lines)
