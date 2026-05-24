"""Email tools for LocalAgent.

These tools call EmailService directly (same process, no HTTP round-trip)
to avoid the 502 deadlock from httpx calling back into the same uvicorn worker.
"""

from __future__ import annotations

from typing import Any, Callable

from .base import BaseTool

from local_backend.service.email_service import EmailService


class _EmailToolBase(BaseTool):
    def __init__(self, user_id_getter: Callable[[], str | None]):
        self._user_id_getter = user_id_getter

    def _require_auth(self) -> tuple[str | None, str | None]:
        user_id = self._user_id_getter()
        if not user_id:
            return None, "Error: Missing user context. Please login first."
        if EmailService is None:
            return None, "Error: Email service not available."
        return user_id, None


def _get_service() -> EmailService | None:
    if EmailService is None:
        return None
    return EmailService()


class CheckEmailStatusTool(_EmailToolBase):
    name = "check_email_status"
    description = "Check the current email bind status for the user."
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
        if service is None:
            return "Error: Email service not available."
        data = service.get_email_status(user_id)

        if not data.get("success"):
            return f"Error: {data.get('message', 'Failed to get status')}"

        if not data.get("is_bound", False):
            return "Email is not bound. Please go to User Settings to bind your email account first."

        email = data.get("email_address", "")
        bind_time = data.get("bind_time", "")
        last_sync = data.get("last_sync_time", "")
        lines = [
            "Email Status:",
            "  Status: Bound",
            f"  Address: {email}",
        ]
        if bind_time:
            lines.append(f"  Bind Time: {bind_time}")
        if last_sync:
            lines.append(f"  Last Sync: {last_sync}")
        return "\n".join(lines)


class GetEmailsTool(_EmailToolBase):
    name = "get_emails"
    description = "Retrieve synced emails for the user. Optionally filter by title keyword and limit results."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Optional keyword to filter email titles. Case-insensitive partial match.",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of emails to return (default 50, max 100).",
                "default": 50,
            },
        },
        "required": [],
    }

    async def execute(self, **kwargs) -> str:
        user_id, error = self._require_auth()
        if error:
            return error

        service = _get_service()
        if service is None:
            return "Error: Email service not available."
        data = service.get_email_messages(user_id)

        if not data.get("success"):
            return f"Error: {data.get('message', 'Failed to get messages')}"

        messages = data.get("messages", [])
        if not messages:
            return "No synced emails found. Try syncing first in the Email page."

        query = (kwargs.get("query") or "").strip().lower()
        if query:
            messages = [
                m for m in messages
                if query in (str(m.get("title") or "")).lower()
            ]
            if not messages:
                return f"No emails found matching '{query}'."

        max_results = int(kwargs.get("max_results") or 50)
        if max_results < 1:
            max_results = 50
        if max_results > 100:
            max_results = 100
        all_messages = messages
        messages = all_messages[:max_results]
        total = len(all_messages)

        header = f"Showing {len(messages)} of {total} total email(s):"
        lines = [header, ""]
        for i, msg in enumerate(messages, 1):
            title = msg.get("title") or "(No subject)"
            sender = msg.get("sender") or ""
            time = (msg.get("release_time") or "")[:16].replace("T", " ")
            msg_id = msg.get("message_id") or msg.get("id") or ""
            lines.append(f"{i}. [#{msg_id}] \"{title}\"")
            lines.append(f"   From: {sender}  |  {time}")
            lines.append("")

        return "\n".join(lines).strip()


class SendEmailTool(_EmailToolBase):
    name = "send_email"
    description = "Send an email through the user's bound email account."
    parameters = {
        "type": "object",
        "properties": {
            "to": {
                "type": "string",
                "description": "Recipient email address.",
            },
            "subject": {
                "type": "string",
                "description": "Email subject line.",
            },
            "body": {
                "type": "string",
                "description": "Email body content.",
            },
        },
        "required": ["to", "subject", "body"],
    }

    async def execute(self, **kwargs) -> str:
        user_id, error = self._require_auth()
        if error:
            return error

        to = (kwargs.get("to") or "").strip()
        subject = (kwargs.get("subject") or "").strip()
        body = (kwargs.get("body") or "").strip()

        if not to:
            return "Error: 'to' (recipient) is required."
        if not subject:
            return "Error: 'subject' is required."
        if not body:
            return "Error: 'body' is required."

        service = _get_service()
        if service is None:
            return "Error: Email service not available."
        data = service.send_email(user_id, subject, body, to)

        if data.get("success"):
            return f"Email sent successfully to {to} with subject \"{subject}\"."
        return f"Error: {data.get('message', 'Failed to send email')}"


class AnalyzeEmailsTool(_EmailToolBase):
    """Use LLM + user profile to semantically analyze synced emails."""

    name = "analyze_emails"
    description = (
        "Use AI to analyze synced emails, combined with the user's personal profile "
        "(interests, habits, etc.) to find important emails or filter by semantic criteria. "
        "Call this when the user asks 'what important emails do I have', "
        "'help me check my emails', or 'filter emails'."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The user's filtering requirement, e.g. 'important emails', 'course-related emails', 'from advisor'. Default: 'important emails'.",
                "default": "重要的邮件",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of recent emails to analyze (default 50, max 100).",
                "default": 50,
            },
        },
        "required": [],
    }

    def __init__(
        self,
        user_id_getter: Callable[[], str | None],
        llm_provider,
        profile_getter: Callable[[], dict] | None = None,
    ):
        super().__init__(user_id_getter)
        self._llm = llm_provider
        self._profile_getter = profile_getter

    async def execute(self, **kwargs) -> str:
        user_id, error = self._require_auth()
        if error:
            return error

        service = _get_service()
        if service is None:
            return "Error: Email service not available."
        data = service.get_email_messages(user_id)

        if not data.get("success"):
            return f"Error: {data.get('message', 'Failed to get messages')}"

        messages = data.get("messages", [])
        if not messages:
            return "No synced emails to analyze. Please sync emails first in the Email page."

        max_results = int(kwargs.get("max_results") or 50)
        if max_results < 1:
            max_results = 50
        if max_results > 100:
            max_results = 100
        messages = messages[:max_results]

        query = kwargs.get("query") or "重要的邮件"
        profile = {}
        if self._profile_getter:
            profile = self._profile_getter()

        prompt = _build_analysis_prompt(messages, query, profile)
        try:
            response = await self._llm.chat(
                messages=[{"role": "user", "content": prompt}],
                tools=[],
            )
            return response.content or "No analysis result produced."
        except Exception as e:
            return f"Error analyzing emails: {e}"


class GetStarredEmailsTool(_EmailToolBase):
    name = "get_starred_emails"
    description = "Retrieve all starred (星标) emails for the current user. Use when the user asks about starred emails, important emails, or saved emails."
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
        if service is None:
            return "Error: Email service not available."
        data = service.get_starred_emails(user_id)

        if not data.get("success"):
            return f"Error: {data.get('message', 'Failed to get starred emails')}"

        messages = data.get("messages", [])
        if not messages:
            return "No starred emails. Star emails in the Email page or ask me to star specific emails."

        lines = [f"You have {len(messages)} starred email(s):", ""]
        for i, msg in enumerate(messages, 1):
            title = msg.get("title") or "(No subject)"
            sender = msg.get("sender") or ""
            time = (msg.get("release_time") or "")[:16].replace("T", " ")
            reason = msg.get("star_reason", "")
            msg_id = msg.get("message_id") or msg.get("id") or ""
            lines.append(f"{i}. ★ [#{msg_id}] \"{title}\"")
            lines.append(f"   From: {sender}  |  {time}")
            if reason:
                lines.append(f"   Reason: {reason}")
            lines.append("")
        return "\n".join(lines).strip()


class StarEmailTool(_EmailToolBase):
    name = "star_email"
    description = "Star (add to starred) an email by its ID or title keyword. Use when the user wants to mark an email as important."
    parameters = {
        "type": "object",
        "properties": {
            "email_id": {
                "type": "integer",
                "description": "Email ID number (from get_emails results).",
            },
            "reason": {
                "type": "string",
                "description": "Optional reason for starring.",
            },
        },
        "required": ["email_id"],
    }

    async def execute(self, **kwargs) -> str:
        user_id, error = self._require_auth()
        if error:
            return error
        email_id = kwargs.get("email_id")
        if email_id is None:
            return "Error: email_id is required."
        reason = kwargs.get("reason")

        service = _get_service()
        if service is None:
            return "Error: Email service not available."
        data = service.star_email(user_id, int(email_id), reason)

        if data.get("success"):
            msg = data.get("message") or f"Email #{email_id} starred."
            return msg
        return f"Error: {data.get('message', 'Failed to star email')}"


class UnstarEmailTool(_EmailToolBase):
    name = "unstar_email"
    description = "Remove star from an email by its ID. Use when the user wants to unmark a previously starred email."
    parameters = {
        "type": "object",
        "properties": {
            "email_id": {
                "type": "integer",
                "description": "Email ID number.",
            },
        },
        "required": ["email_id"],
    }

    async def execute(self, **kwargs) -> str:
        user_id, error = self._require_auth()
        if error:
            return error
        email_id = kwargs.get("email_id")
        if email_id is None:
            return "Error: email_id is required."

        service = _get_service()
        if service is None:
            return "Error: Email service not available."
        data = service.unstar_email(user_id, int(email_id))

        if data.get("success"):
            return f"Email #{email_id} unstarred."
        return f"Error: {data.get('message', 'Failed to unstar email')}"


class SyncEmailsTool(_EmailToolBase):
    name = "sync_emails"
    description = "触发邮件同步。调用此工具从绑定的邮箱拉取最新邮件。"
    parameters = {
        "type": "object",
        "properties": {
            "max_messages": {
                "type": "integer",
                "description": "最大同步邮件数（默认 50）",
                "default": 50,
            },
        },
        "required": [],
    }

    async def execute(self, **kwargs) -> str:
        user_id, error = self._require_auth()
        if error:
            return error
        max_messages = kwargs.get("max_messages") or 50
        service = _get_service()
        if service is None:
            return "Error: Email service not available."
        result = service.sync_email_data(user_id, max_messages=max_messages)
        if result.get("success"):
            data = result.get("data", {})
            db_total = data.get("db_total", 0)
            fetched = data.get("synced", 0)
            new_count = data.get("new_count", 0)
            if new_count > 0:
                return f"邮件同步完成。本地共 {db_total} 封，本次新增 {new_count} 封。"
            return f"邮件同步完成。本地共 {db_total} 封，无新邮件。"
        return f"Error: {result.get('message', '同步失败')}"


class DeleteEmailTool(_EmailToolBase):
    name = "delete_email"
    description = "将邮件移入垃圾箱（软删除）。用户说'删除邮件'时用这个。"
    parameters = {
        "type": "object",
        "properties": {
            "message_id": {"type": "integer", "description": "邮件 ID"},
        },
        "required": ["message_id"],
    }

    async def execute(self, **kwargs) -> str:
        user_id, error = self._require_auth()
        if error:
            return error
        message_id = kwargs.get("message_id")
        if message_id is None:
            return "Error: message_id is required."
        service = _get_service()
        if service is None:
            return "Error: Email service not available."
        result = service.delete_email_message(user_id, int(message_id))
        if result.get("success"):
            return result.get("message") or f"邮件 #{message_id} 已移入垃圾箱。"
        return f"Error: {result.get('message', '删除失败')}"


class GetTrashEmailsTool(_EmailToolBase):
    name = "get_trash_emails"
    description = "查看垃圾箱中的邮件列表。当用户问'垃圾箱里有什么'或'查看已删除的邮件'时使用。"
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
        if service is None:
            return "Error: Email service not available."
        result = service.get_trash_messages(user_id)

        if not result.get("success"):
            return f"Error: {result.get('message', 'Failed to get trash messages')}"

        messages = result.get("messages", [])
        if not messages:
            return "垃圾箱为空。"

        lines = [f"垃圾箱中共有 {len(messages)} 封邮件：", ""]
        for i, msg in enumerate(messages, 1):
            title = msg.get("title") or "(No subject)"
            sender = msg.get("sender") or ""
            time = (msg.get("release_time") or "")[:16].replace("T", " ")
            msg_id = msg.get("id") or msg.get("message_id") or ""
            lines.append(f"{i}. [#{msg_id}] \"{title}\"")
            lines.append(f"   From: {sender}  |  {time}")
            lines.append("")
        return "\n".join(lines).strip()


class RestoreEmailTool(_EmailToolBase):
    name = "restore_email"
    description = "从垃圾箱恢复一封邮件到收件箱。当用户说'恢复那封邮件'或'撤销删除'时使用。"
    parameters = {
        "type": "object",
        "properties": {
            "message_id": {"type": "integer", "description": "邮件 ID"},
        },
        "required": ["message_id"],
    }

    async def execute(self, **kwargs) -> str:
        user_id, error = self._require_auth()
        if error:
            return error
        message_id = kwargs.get("message_id")
        if message_id is None:
            return "Error: message_id is required."
        service = _get_service()
        if service is None:
            return "Error: Email service not available."
        result = service.restore_email_message(user_id, int(message_id))
        if result.get("success"):
            return result.get("message") or f"邮件 #{message_id} 已恢复。"
        return f"Error: {result.get('message', '恢复失败')}"


class PermanentDeleteEmailTool(_EmailToolBase):
    name = "permanent_delete_email"
    description = "永久删除一封邮件。此操作不可撤销。当用户明确说'永久删除'时使用。"
    parameters = {
        "type": "object",
        "properties": {
            "message_id": {"type": "integer", "description": "邮件 ID"},
        },
        "required": ["message_id"],
    }

    async def execute(self, **kwargs) -> str:
        user_id, error = self._require_auth()
        if error:
            return error
        message_id = kwargs.get("message_id")
        if message_id is None:
            return "Error: message_id is required."
        service = _get_service()
        if service is None:
            return "Error: Email service not available."
        result = service.permanent_delete_email(user_id, int(message_id))
        if result.get("success"):
            return result.get("message") or f"邮件 #{message_id} 已永久删除。"
        return f"Error: {result.get('message', '永久删除失败')}"


class EmptyTrashTool(_EmailToolBase):
    name = "empty_trash"
    description = "清空垃圾箱，永久删除垃圾箱中的所有邮件。此操作不可撤销。"
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
        if service is None:
            return "Error: Email service not available."
        result = service.empty_trash(user_id)
        if result.get("success"):
            return result.get("message") or "垃圾箱已清空。"
        return f"Error: {result.get('message', '清空垃圾箱失败')}"


def _build_analysis_prompt(
    messages: list[dict],
    query: str,
    profile: dict,
) -> str:
    interests = profile.get("interests_identified", []) or profile.get("interests", [])
    topic_areas = profile.get("study_work_patterns", {}).get("topic_areas", []) or profile.get("topic_areas", [])

    profile_desc = ""
    if interests:
        interest_names = [i.get("topic", i) if isinstance(i, dict) else str(i) for i in interests]
        profile_desc += f"用户的兴趣领域：{', '.join(interest_names[:8])}\n"
    if topic_areas:
        profile_desc += f"用户关注的话题：{', '.join(topic_areas[:8])}\n"

    email_list = []
    for i, msg in enumerate(messages, 1):
        title = msg.get("title") or "(无主题)"
        sender = msg.get("sender") or ""
        time = (msg.get("release_time") or "")[:16].replace("T", " ")
        email_list.append(f"{i}. [{time}] {sender} — {title}")
    emails_text = "\n".join(email_list)

    return (
        f"你是一个智能邮件分析师。请根据以下信息，帮助用户筛选邮件。\n\n"
        f"{profile_desc}"
        f"用户的筛选需求：{query}\n\n"
        f"最近 {len(messages)} 封邮件：\n{emails_text}\n\n"
        "请按重要性从高到低列出最相关的邮件（最多 5 封），"
        "用简洁的中文说明每一封为什么符合用户的需求。"
        "如果没有明显相关的邮件，如实说明。"
        "不要编造邮件信息，只使用上面列出的邮件。"
    )
