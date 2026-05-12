"""Email tools for LocalAgent.

These tools call the local backend email API via HTTP. They require
the local backend (port 8002) to be running and the user to have
bound their email account in UserSettings.
"""

from __future__ import annotations

from typing import Any, Callable

import httpx

from .base import BaseTool

BACKEND_BASE = "http://127.0.0.1:8002"


class _EmailToolBase(BaseTool):
    def __init__(self, user_id_getter: Callable[[], str | None], token_getter: Callable[[], str | None]):
        self._user_id_getter = user_id_getter
        self._token_getter = token_getter

    def _headers(self) -> dict[str, str] | None:
        token = self._token_getter()
        if not token:
            return None
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def _require_auth(self) -> tuple[dict[str, str] | None, str | None]:
        user_id = self._user_id_getter()
        if not user_id:
            return None, "Error: Missing user context. Please login first."
        headers = self._headers()
        if not headers:
            return None, "Error: Missing authentication token. Please login first."
        return headers, None


class CheckEmailStatusTool(_EmailToolBase):
    name = "check_email_status"
    description = "Check the current email bind status for the user."
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    async def execute(self, **kwargs) -> str:
        headers, error = self._require_auth()
        if error:
            return error

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{BACKEND_BASE}/api/v1/email/status", headers=headers)
                data = resp.json()
        except Exception as e:
            return f"Error: Failed to connect to backend - {e}"

        if not data.get("success"):
            return f"Error: {data.get('message', 'Failed to get status')}"

        is_bound = data.get("is_bound", False)
        if not is_bound:
            return "Email is not bound. Please go to User Settings to bind your email account first."

        email = data.get("email_address", "")
        bind_time = data.get("bind_time", "")
        last_sync = data.get("last_sync_time", "")
        lines = [
            "Email Status:",
            f"  Status: Bound",
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
                "description": "Maximum number of emails to return (default 20, max 50).",
                "default": 20,
            },
        },
        "required": [],
    }

    async def execute(self, **kwargs) -> str:
        headers, error = self._require_auth()
        if error:
            return error

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{BACKEND_BASE}/api/v1/email/messages", headers=headers)
                data = resp.json()
        except Exception as e:
            return f"Error: Failed to connect to backend - {e}"

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

        max_results = int(kwargs.get("max_results") or 20)
        if max_results < 1:
            max_results = 20
        if max_results > 50:
            max_results = 50

        messages = messages[:max_results]

        lines = [f"Found {len(messages)} email(s):", ""]
        for i, msg in enumerate(messages, 1):
            title = msg.get("title") or "(No subject)"
            sender = msg.get("sender") or ""
            time = (msg.get("release_time") or "")[:16].replace("T", " ")
            lines.append(f"{i}. \"{title}\"")
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
        headers, error = self._require_auth()
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

        payload = {
            "title": subject,
            "context": body,
            "receiver": to,
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{BACKEND_BASE}/api/v1/email/send",
                    headers=headers,
                    json=payload,
                )
                data = resp.json()
        except Exception as e:
            return f"Error: Failed to connect to backend - {e}"

        if data.get("success"):
            return f"Email sent successfully to {to} with subject \"{subject}\"."
        else:
            return f"Error: {data.get('message', 'Failed to send email')}"
