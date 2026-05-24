"""Task tools for LocalAgent."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from .base import BaseTool
from local_backend.database.code.handle.database_task_v2_handle import TaskV2Handle


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
    if len(time_part) == 5 and time_part.count(":") == 1:
        text = f"{date_part}T{time_part}:00"

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


def _format_datetime_for_display(dt_str: str | None) -> str:
    if not dt_str:
        return "无"
    date_part = dt_str[:10] if len(dt_str) >= 10 else dt_str
    if len(dt_str) > 16:
        time_part = dt_str[11:16]
        return f"{date_part} {time_part}"
    return date_part


_PRIORITY_LABELS = {0: "P0 · 紧急", 1: "P1 · 高", 2: "P2 · 中", 3: "P3 · 低"}


def _priority_label(task: dict[str, Any]) -> str:
    priority = task.get("priority")
    if isinstance(priority, str):
        norm = _normalize_priority(priority)
        if norm:
            num = int(norm.lstrip("p"))
            return _PRIORITY_LABELS.get(num, "P2 · 中")
    if isinstance(priority, int):
        return _PRIORITY_LABELS.get(priority, "P2 · 中")
    return "P2 · 中"


def _format_task_display(task: dict[str, Any], index: int | None = None) -> str:
    task_id = task.get("task_id") or task.get("data_id") or task.get("id") or "?"
    title = task.get("title") or task.get("data_title") or "未命名"
    status = task.get("status") or "pending"
    due_date = task.get("due_date") or task.get("data_ddl_time")
    desc = task.get("description") or task.get("data_content_text") or ""

    status_label = "✅ 已完成" if status == "completed" else "⬜ 待办"
    due_display = _format_datetime_for_display(due_date)

    prefix = f"{index}. " if index is not None else ""
    lines = [
        f"{prefix}[{status_label}] #{task_id} {title}",
        f"   优先级: {_priority_label(task)} | 截止: {due_display}",
    ]
    if desc:
        desc_preview = desc[:80] + ("..." if len(desc) > 80 else "")
        lines.append(f"   描述: {desc_preview}")
    return "\n".join(lines)


class _TaskToolBase(BaseTool):
    def __init__(self, user_id_getter: Callable[[], str | None]):
        self._user_id_getter = user_id_getter
        self._handle = TaskV2Handle()

    def _require_user(self) -> tuple[str | None, str | None]:
        user_id = self._user_id_getter()
        if not user_id:
            return None, "Error: Missing user context. Please login first."
        return user_id, None

    def _resolve_task_id(
        self,
        user_id: str,
        task_id: Any,
        title_keyword: str | None,
    ) -> tuple[list[int] | None, str | None]:
        """Resolve task_id or title_keyword.

        Unlike schedule resolution, returns ALL matching task IDs on multi-match
        so the Agent can present choices to the user.
        """
        if task_id is not None:
            try:
                tid = int(task_id)
            except (TypeError, ValueError):
                return None, "Error: task_id must be a positive integer"
            if tid <= 0:
                return None, "Error: task_id must be a positive integer"
            return [tid], None

        keyword = (title_keyword or "").strip().lower()
        if not keyword:
            return None, "Error: Provide task_id or title_keyword"

        result = self._handle.get_tasks(user_id)
        if not result.get("ok"):
            return None, f"Error: {result.get('message', 'Failed to list tasks')}"

        tasks = result.get("data", [])
        matches: list[int] = []
        for task in tasks:
            title = str(task.get("title") or task.get("data_title") or "").lower()
            if keyword in title:
                tid = task.get("task_id") or task.get("data_id") or task.get("id")
                try:
                    tid_int = int(tid)
                    if tid_int > 0:
                        matches.append(tid_int)
                except (TypeError, ValueError):
                    continue

        if not matches:
            return None, f"Error: No task found by title keyword '{title_keyword}'"

        return matches, None


class ListTasksTool(_TaskToolBase):
    name = "list_tasks"
    description = (
        "List current user tasks — this is the ONLY source of truth for what tasks exist. "
        "ALWAYS call this before claiming a task exists or doesn't exist. "
        "DO NOT rely on conversation memory for task state — memory may be stale. "
        "Optionally filter by status: 'pending' for active tasks, 'completed' for done tasks."
    )
    parameters = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "Optional filter: 'pending' or 'completed'. Omit to list all.",
                "enum": ["pending", "completed"],
            },
        },
    }

    async def execute(self, **kwargs) -> str:
        user_id, error = self._require_user()
        if error:
            return error
        assert user_id is not None

        status_filter = kwargs.get("status")

        result = self._handle.get_tasks(user_id)
        if not result.get("ok"):
            return f"Error: {result.get('message', 'Failed to list tasks')}"

        tasks = result.get("data", [])

        if status_filter:
            tasks = [t for t in tasks if (t.get("status") or "").lower() == status_filter.lower()]

        if not tasks:
            status_label = (
                {"pending": "待办", "completed": "已完成"}.get(status_filter, "")
                if status_filter
                else ""
            )
            return f"当前{' ' + status_label if status_label else ''}任务列表为空。"

        lines = []
        for i, task in enumerate(tasks, 1):
            lines.append(_format_task_display(task, index=i))
            lines.append("")

        header = "任务列表:\n" + "=" * 40
        return "\n".join([header, *lines])


class CreateTaskTool(_TaskToolBase):
    name = "create_task"
    description = (
        "Create a new task/TODO for the current user. "
        "BEFORE calling this, always call list_tasks first to check if an equivalent task already exists. "
        "If the user mentions a task you created earlier, DO NOT assume it still exists — verify with list_tasks. "
        "Always provide a clear title. Optionally set due_date, priority (p0/p1/p2/p3), and description."
    )
    parameters = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Task title (required)"},
            "description": {"type": "string", "description": "Task description or notes"},
            "due_date": {
                "type": "string",
                "description": "Due date in ISO-8601 format, e.g. '2026-05-24T18:00:00'. For date-only, append T00:00:00.",
            },
            "priority": {"type": "string", "description": "Priority: p0 (urgent), p1 (high), p2 (medium), p3 (low)"},
        },
        "required": ["title"],
    }

    async def execute(self, **kwargs) -> str:
        user_id, error = self._require_user()
        if error:
            return error
        assert user_id is not None

        title = str(kwargs.get("title") or "").strip()
        if not title:
            return "Error: title is required"

        description = kwargs.get("description")
        due_date = _normalize_iso_datetime(kwargs.get("due_date"))

        priority = None
        if kwargs.get("priority") is not None:
            priority = _normalize_priority(kwargs.get("priority"))
            if priority is None:
                return "Error: priority must be p0/p1/p2/p3"

        result = self._handle.create_task(
            user_id=user_id,
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
        )
        if not result.get("ok"):
            return f"Error: {result.get('message', 'create task failed')}"

        task_id = result.get("data", {}).get("task_id")
        extra = []
        if priority:
            extra.append(f"优先级={_priority_label({'priority': priority})}")
        if due_date:
            extra.append(f"截止={_format_datetime_for_display(due_date)}")
        extras = "，".join(extra)
        return f"创建任务成功: task_id={task_id}, title={title}" + (f"，{extras}" if extras else "")


class UpdateTaskTool(_TaskToolBase):
    name = "update_task"
    description = (
        "Update an existing task. Find the task by task_id or title_keyword. "
        "When multiple tasks match a keyword, return all candidates for user to pick — "
        "NEVER silently choose one. Call list_tasks first if unsure."
    )
    parameters = {
        "type": "object",
        "properties": {
            "task_id": {"type": "integer", "description": "Task ID to update"},
            "title_keyword": {
                "type": "string",
                "description": "Fallback matcher when task_id is unknown. Matches tasks whose title contains this keyword.",
            },
            "title": {"type": "string", "description": "New title"},
            "due_date": {"type": "string", "description": "New due date (ISO-8601)"},
            "priority": {"type": "string", "description": "New priority: p0/p1/p2/p3"},
            "description": {"type": "string", "description": "New description"},
            "status": {
                "type": "string",
                "description": "New status: 'pending' or 'completed'",
                "enum": ["pending", "completed"],
            },
        },
        "required": [],
    }

    async def execute(self, **kwargs) -> str:
        user_id, error = self._require_user()
        if error:
            return error
        assert user_id is not None

        task_ids, error = self._resolve_task_id(
            user_id=user_id,
            task_id=kwargs.get("task_id"),
            title_keyword=kwargs.get("title_keyword"),
        )
        if error:
            return error
        assert task_ids is not None

        if len(task_ids) > 1:
            result = self._handle.get_tasks(user_id)
            tasks = result.get("data", [])
            matched_tasks = [
                t for t in tasks
                if (t.get("task_id") or t.get("data_id") or t.get("id")) in task_ids
            ]

            lines = [f"找到 {len(task_ids)} 个匹配任务，请让用户明确指定 task_id:"]
            for i, t in enumerate(matched_tasks, 1):
                lines.append(_format_task_display(t, index=i))
            lines.append("")
            lines.append("请使用 task_id 参数重新调用 update_task。")
            return "\n".join(lines)

        task_id = task_ids[0]

        title: str | None = kwargs.get("title")
        description: str | None = kwargs.get("description")
        due_date: str | None = None
        if kwargs.get("due_date") is not None:
            due_date = _normalize_iso_datetime(kwargs.get("due_date"))
            if not due_date:
                return "Error: due_date must be valid ISO-8601 datetime"

        priority: str | None = None
        if kwargs.get("priority") is not None:
            priority = _normalize_priority(kwargs.get("priority"))
            if priority is None:
                return "Error: priority must be p0/p1/p2/p3"

        status: str | None = kwargs.get("status")
        if status is not None and status not in ("pending", "completed"):
            return "Error: status must be 'pending' or 'completed'"

        if not any([title, description, due_date, priority, status]):
            return "Error: No fields to update. Provide at least one of: title, due_date, priority, description, status"

        result = self._handle.update_task(
            user_id=user_id,
            task_id=task_id,
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            status=status,
        )
        if not result.get("ok"):
            return f"Error: {result.get('message', 'update task failed')}"

        changes = []
        if title:
            changes.append(f"title='{title}'")
        if description:
            changes.append("description updated")
        if due_date:
            changes.append(f"due_date={_format_datetime_for_display(due_date)}")
        if priority:
            changes.append(f"priority={priority}")
        if status:
            status_label = "已完成" if status == "completed" else "待办"
            changes.append(f"status={status_label}")

        return f"更新任务成功: task_id={task_id}，变更: {', '.join(changes)}"


class DeleteTaskTool(_TaskToolBase):
    name = "delete_task"
    description = (
        "Delete a task by task_id or title_keyword. "
        "When multiple tasks match a keyword, return all candidates for user to pick — "
        "NEVER silently delete. Always confirm deletion with the user before calling."
    )
    parameters = {
        "type": "object",
        "properties": {
            "task_id": {"type": "integer", "description": "Task ID to delete"},
            "title_keyword": {
                "type": "string",
                "description": "Fallback matcher when task_id is unknown. Matches tasks whose title contains this keyword.",
            },
        },
        "required": [],
    }

    async def execute(self, **kwargs) -> str:
        user_id, error = self._require_user()
        if error:
            return error
        assert user_id is not None

        task_ids, error = self._resolve_task_id(
            user_id=user_id,
            task_id=kwargs.get("task_id"),
            title_keyword=kwargs.get("title_keyword"),
        )
        if error:
            return error
        assert task_ids is not None

        if len(task_ids) > 1:
            result = self._handle.get_tasks(user_id)
            tasks = result.get("data", [])
            matched_tasks = [
                t for t in tasks
                if (t.get("task_id") or t.get("data_id") or t.get("id")) in task_ids
            ]

            lines = [f"找到 {len(task_ids)} 个匹配任务，请让用户明确指定要删除的 task_id:"]
            for i, t in enumerate(matched_tasks, 1):
                lines.append(_format_task_display(t, index=i))
            lines.append("")
            lines.append("请使用 task_id 参数重新调用 delete_task。")
            return "\n".join(lines)

        task_id = task_ids[0]

        result = self._handle.get_tasks(user_id)
        task_title = str(task_id)
        for t in result.get("data", []):
            tid = t.get("task_id") or t.get("data_id") or t.get("id")
            try:
                if int(tid) == task_id:
                    task_title = t.get("title") or t.get("data_title") or str(task_id)
                    break
            except (TypeError, ValueError):
                pass

        result = self._handle.delete_task(user_id=user_id, task_id=task_id)
        if not result.get("ok"):
            return f"Error: {result.get('message', 'delete task failed')}"

        return f"删除任务成功: task_id={task_id}, title={task_title}"
