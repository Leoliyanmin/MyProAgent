"""Blackboard tools for LocalAgent.

Provides tools to check Blackboard bind status, trigger sync, and query
assignments directly from the local database.
"""

from __future__ import annotations

from typing import Any, Callable
from datetime import datetime, timedelta

from .base import BaseTool

from local_backend.service.blackboard_service import BlackboardService
from local_backend.database.code.command.database_command import list_events_by_user


class _BlackboardToolBase(BaseTool):
    def __init__(self, user_id_getter: Callable[[], str | None]):
        self._user_id_getter = user_id_getter

    def _require_auth(self) -> tuple[str | None, str | None]:
        user_id = self._user_id_getter()
        if not user_id:
            return None, "Error: Missing user context. Please login first."
        return user_id, None


def _get_service() -> BlackboardService:
    return BlackboardService()


class GetBlackboardStatusTool(_BlackboardToolBase):
    name = "get_blackboard_status"
    description = "Check the current Blackboard bind status for the user."
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    async def execute(self, **kwargs) -> str:
        user_id, error = self._require_auth()
        if error:
            return error

        service = _get_service()
        data = service.get_blackboard_status(user_id)

        if not data.get("success"):
            return f"Error: {data.get('message', 'Failed to get Blackboard status')}"

        if not data.get("is_bound", False):
            return "Blackboard is not bound. Please go to Settings to bind your Blackboard account first."

        username = data.get("username", "")
        bind_time = data.get("bind_time", "")
        last_sync = data.get("last_sync_time", "")
        courses_count = data.get("courses_count", 0)

        lines = [
            "Blackboard Status:",
            "  Status: Bound",
            f"  Username: {username}",
            f"  Courses: {courses_count}",
        ]
        if bind_time:
            lines.append(f"  Bind Time: {bind_time}")
        if last_sync:
            lines.append(f"  Last Sync: {last_sync}")
        return "\n".join(lines)


class SyncBlackboardTool(_BlackboardToolBase):
    name = "sync_blackboard"
    description = "Trigger Blackboard data sync. Fetches the latest courses and assignments from Blackboard."
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    async def execute(self, **kwargs) -> str:
        user_id, error = self._require_auth()
        if error:
            return error

        service = _get_service()
        result = service.sync_blackboard_data(user_id)

        if result.get("success"):
            return result.get("message", "Blackboard sync completed.")
        return f"Error: {result.get('message', 'Sync failed')}"


class GetBlackboardAssignmentsTool(_BlackboardToolBase):
    name = "get_blackboard_assignments"
    description = (
        "Get upcoming assignments from Blackboard courses. "
        "Returns assignments with course name, title, and due date. "
        "Call this when the user asks 'what assignments are due', "
        "'check my homework deadlines', or 'what do I need to submit this week'."
    )
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    async def execute(self, **kwargs) -> str:
        user_id, error = self._require_auth()
        if error:
            return error

        import json
        assignments = list_events_by_user(user_id, event_type="assignment")

        if not assignments:
            return "No assignments found in your Blackboard courses. Please bind and sync Blackboard first."

        def _sort_key(e: dict) -> tuple[int, str]:
            due = e.get("event_end_time")
            if due:
                return (0, str(due))
            return (1, "")

        assignments.sort(key=_sort_key)

        lines = [f"You have {len(assignments)} assignment(s):", ""]
        for i, a in enumerate(assignments, 1):
            title = a.get("event_title") or "(No title)"
            due = a.get("event_end_time", "")
            if due:
                try:
                    due_display = due[:16].replace("T", " ")
                except Exception:
                    due_display = due
            else:
                due_display = "No deadline"

            course_name = "Unknown Course"
            meta_str = a.get("event_meta_json")
            if meta_str:
                try:
                    meta = json.loads(meta_str)
                    course_name = meta.get("course_name", course_name)
                except (json.JSONDecodeError, TypeError):
                    pass

            lines.append(f"{i}. [{course_name}] {title}")
            lines.append(f"   Due: {due_display}")
            link = a.get("event_link_url")
            if link:
                lines.append(f"   Link: {link}")
            lines.append("")

        return "\n".join(lines).strip()
