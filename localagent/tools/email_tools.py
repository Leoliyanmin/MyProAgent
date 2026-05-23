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


class AnalyzeEmailsTool(_EmailToolBase):
    """用 LLM + 用户画像对已同步邮件做个性化语义分析。"""

    name = "analyze_emails"
    description = (
        "使用 AI 分析已同步的邮件，结合你的个人画像（兴趣、习惯等）"
        "找出重要邮件或按语义条件筛选邮件。"
        "当用户问'有什么重要邮件'、'帮我看看邮件'、'筛选邮件'时调用此工具。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "用户的筛选需求，如'重要的邮件'、'关于课程的邮件'、'导师发的'等。默认为'重要的邮件'。",
                "default": "重要的邮件",
            },
            "max_results": {
                "type": "integer",
                "description": "从最近邮件中取多少封做分析（默认 20，最大 50）",
                "default": 20,
            },
        },
        "required": [],
    }

    def __init__(
        self,
        user_id_getter: Callable[[], str | None],
        token_getter: Callable[[], str | None],
        llm_provider,
        profile_getter: Callable[[], dict] | None = None,
    ):
        super().__init__(user_id_getter, token_getter)
        self._llm = llm_provider
        self._profile_getter = profile_getter

    def _build_profile_context(self) -> str:
        if not self._profile_getter:
            return ""
        try:
            profile = self._profile_getter()
        except Exception:
            return ""

        parts = []

        interests = profile.get("interests_identified", [])
        if interests:
            topics = [i.get("topic", "") for i in interests if i.get("topic")]
            if topics:
                parts.append(f"用户的兴趣领域：{', '.join(topics)}")

        patterns = profile.get("study_work_patterns", {})
        work_style = patterns.get("work_style", "")
        if work_style:
            style_map = {
                "structured": "喜欢有计划、按部就班的学习方式",
                "deadline_driven": "习惯在截止日期前集中处理任务",
                "flexible": "喜欢灵活自由的学习方式",
            }
            style_desc = style_map.get(work_style, "")
            if style_desc:
                parts.append(f"学习工作风格：{style_desc}")

        topics = patterns.get("topic_areas", [])
        if topics:
            parts.append(f"常涉及的话题领域：{', '.join(topics)}")

        mbti = profile.get("mbti_inference", {})
        mbti_type = mbti.get("mbti_type", "")
        if mbti_type:
            parts.append(f"MBTI 人格类型：{mbti_type}")

        if not parts:
            return ""
        return "用户画像参考信息（基于历史对话分析）：\n" + "\n".join(f"- {p}" for p in parts)

    async def _fetch_emails(self, headers: dict) -> list[dict] | None:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{BACKEND_BASE}/api/v1/email/messages", headers=headers
                )
                data = resp.json()
        except Exception:
            return None
        if not data.get("success"):
            return None
        return data.get("messages", [])

    async def execute(self, **kwargs) -> str:
        headers, error = self._require_auth()
        if error:
            return error

        messages = await self._fetch_emails(headers)
        if messages is None:
            return "错误：无法连接到后端获取邮件，请稍后重试。"
        if not messages:
            return "暂无已同步的邮件，请先在邮件页面触发同步。"

        query = (kwargs.get("query") or "重要的邮件").strip()
        max_results = int(kwargs.get("max_results") or 20)
        max_results = max(1, min(max_results, 50))
        sample = messages[:max_results]

        lines = []
        for i, m in enumerate(sample, 1):
            title = m.get("title") or "(无主题)"
            sender = m.get("sender") or "(未知发件人)"
            time = (m.get("release_time") or "")[:16].replace("T", " ")
            lines.append(f"{i}. 标题: {title}")
            lines.append(f"   发件人: {sender}  |  时间: {time}")
        email_text = "\n".join(lines)

        profile_context = self._build_profile_context()
        profile_section = (
            f"\n{profile_context}\n\n" if profile_context
            else "\n（暂无用户画像数据，请基于邮件本身判断重要性）\n\n"
        )

        prompt = (
            "你是一个专业的邮件助手。请根据以下用户画像和邮件列表，"
            "分析哪些邮件对这个**特定用户**来说是重要的。\n\n"
            f"用户需求：{query}\n"
            f"{profile_section}"
            f"邮件列表（共 {len(sample)} 封）：\n{email_text}\n\n"
            "请严格按照以下 JSON 格式返回，不要包含其他文字：\n"
            "{\n"
            '  "summary": "一句话总结分析结果",\n'
            '  "important": [\n'
            '    {"index": 序号, "reason": "结合画像说明为什么对这位用户重要"}'
            "  ]\n"
            "}\n\n"
            '如果都不重要，返回 {"summary": "最近没有特别重要的邮件。", "important": []}'
        )

        try:
            response = await self._llm.chat([{"role": "user", "content": prompt}])
        except Exception as e:
            return f"错误：AI 分析失败 - {e}"

        content = response.content or ""
        import re, json as _json
        match = re.search(r"\{.+\}", content, re.DOTALL)
        if not match:
            return f"AI 分析完成，但结果解析失败。原始回复：\n{content[:200]}"

        try:
            result = _json.loads(match.group())
        except _json.JSONDecodeError:
            return f"AI 分析完成，但结果解析失败。原始回复：\n{content[:200]}"

        summary = result.get("summary", "")
        important = result.get("important", [])

        output_parts = []
        if summary:
            output_parts.append(f"📬 {summary}")
        if important:
            output_parts.append("")
            for item in important:
                idx = item.get("index", 0)
                reason = item.get("reason", "")
                if 1 <= idx <= len(sample):
                    m = sample[idx - 1]
                    title = m.get("title") or "(无主题)"
                    output_parts.append(
                        f"  ⭐ {title}\n     原因: {reason}"
                    )
                else:
                    output_parts.append(f"  ⭐ (邮件 {idx}) {reason}")
        if not important:
            output_parts.append("\n暂时没有需要特别关注的邮件。")

        return "\n".join(output_parts)
