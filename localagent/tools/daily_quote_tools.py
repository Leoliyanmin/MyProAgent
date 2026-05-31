"""Daily quote tools for LocalAgent - read, set, and refresh the user's daily quote."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable

from .base import BaseTool

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


class GetDailyQuoteTool(BaseTool):
    """Read the current daily quote displayed on the user's topbar."""

    name = "get_daily_quote"
    description = (
        "Read the user's current daily quote (每日一句) that is displayed "
        "on the topbar. Returns the quote text. Use this when the user asks "
        "about their current quote, what's showing, or wants to know what "
        "quote they have set."
    )
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    def __init__(self, user_id_getter: Callable[[], str | None]):
        self._user_id_getter = user_id_getter

    async def execute(self, **kwargs) -> str:
        user_id = self._user_id_getter()
        if not user_id:
            return "无法获取用户信息。"
        try:
            from local_backend.database.code.command.database_command import (
                get_user_setting,
            )
            settings = get_user_setting(user_id)
            quote = (settings or {}).get("daily_quote", "")
            if quote:
                return f"当前的每日一句：「{quote}」"
            return "当前没有设置每日一句。可以去用户设置页面添加，或者让我帮你设置一句。"
        except Exception as e:
            return f"读取每日一句失败: {e}"


class SetDailyQuoteTool(BaseTool):
    """Set a new daily quote for the user."""

    name = "set_daily_quote"
    description = (
        "Set the user's daily quote (每日一句) to a new custom text. "
        "The quote will appear on the topbar. Use this when the user asks "
        "you to change, update, or set their daily quote to something specific. "
        "The quote should be a short, meaningful sentence."
    )
    parameters = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The new daily quote text to display on the topbar. "
                               "Keep it concise (under 50 characters recommended).",
            },
        },
        "required": ["text"],
    }

    def __init__(self, user_id_getter: Callable[[], str | None]):
        self._user_id_getter = user_id_getter

    async def execute(self, text: str = "", **kwargs) -> str:
        user_id = self._user_id_getter()
        if not user_id:
            return "无法获取用户信息。"
        if not text or not text.strip():
            return "请提供要设置的每日一句内容。"
        try:
            from local_backend.database.code.command.database_command import (
                upsert_user_setting,
            )
            from local_backend.database.code.operations.database_quote_history_operations import (
                insert_quote_history,
            )
            upsert_user_setting(user_id, daily_quote=text.strip())
            insert_quote_history(user_id, text.strip(), source="agent")
            return f"每日一句已更新为：「{text.strip()}」"
        except Exception as e:
            return f"设置每日一句失败: {e}"


class RefreshDailyQuoteTool(BaseTool):
    """Fetch a new random quote from the Hitokoto API and set it as the daily quote."""

    name = "refresh_daily_quote"
    description = (
        "Fetch a random inspirational quote from the Hitokoto (一言) API "
        "and set it as the daily quote. The Hitokoto API provides quotes from "
        "anime, literature, poetry, philosophy, and more. Use this when the "
        "user wants a fresh quote, asks to '换一句', '来一句新的', "
        "or wants an auto-generated inspirational quote."
    )
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    def __init__(self, user_id_getter: Callable[[], str | None]):
        self._user_id_getter = user_id_getter

    async def execute(self, **kwargs) -> str:
        user_id = self._user_id_getter()
        if not user_id:
            return "无法获取用户信息。"
        try:
            import urllib.request
            req = urllib.request.Request(
                "https://v1.hitokoto.cn/",
                headers={"User-Agent": "ProAgent/1.0"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            quote = data.get("hitokoto", "")
            author = data.get("from_who", "")
            source = data.get("from", "")

            if not quote:
                return "未能从一言 API 获取到内容，请稍后再试。"

            from local_backend.database.code.command.database_command import (
                upsert_user_setting,
            )
            from local_backend.database.code.operations.database_quote_history_operations import (
                insert_quote_history,
            )
            upsert_user_setting(user_id, daily_quote=quote)
            insert_quote_history(
                user_id, quote, source="hitokoto",
                quote_author=author, quote_from=source,
            )

            attribution = ""
            if author or source:
                parts = [p for p in [author, f"《{source}》" if source else ""] if p]
                attribution = f" —— {' '.join(parts)}"

            return f"每日一句已刷新：「{quote}」{attribution}"
        except Exception as e:
            return f"刷新每日一句失败: {e}"


class GetDailyQuoteHistoryTool(BaseTool):
    """Get today's daily quote history — all quotes shown today."""

    name = "get_daily_quote_history"
    description = (
        "Get daily quote history for a specific date (or today by default). "
        "Returns all quotes shown on that date with their source and attribution. "
        "Use this when the user asks '今天换过哪些名言？', '昨天的记录', "
        "'2026-05-30 显示了什么？', or wants to review past quotes."
    )
    parameters = {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "Date in YYYY-MM-DD format (e.g. '2026-05-30'). "
                               "Omit or leave empty for today's records.",
            },
        },
        "required": [],
    }

    def __init__(self, user_id_getter: Callable[[], str | None]):
        self._user_id_getter = user_id_getter

    async def execute(self, date: str = "", **kwargs) -> str:
        user_id = self._user_id_getter()
        if not user_id:
            return "无法获取用户信息。"
        try:
            from local_backend.database.code.operations.database_quote_history_operations import (
                get_history_by_date,
            )
            rows = get_history_by_date(user_id, date if date else None)
            rows = get_today_history(user_id)
            if not rows:
                label = date if date else "今天"
                return f"{label}还没有记录过每日一句。"

            label = date if date else "今日"
            lines = [f"## {label}名言记录（共 {len(rows)} 条）\n"]
            for i, r in enumerate(rows, 1):
                parts = [f"{i}. 「{r['quote_text']}」"]
                if r.get("quote_author") or r.get("quote_from"):
                    author = r.get("quote_author", "")
                    source = f"《{r['quote_from']}》" if r.get("quote_from") else ""
                    attr_parts = [p for p in [author, source] if p]
                    if attr_parts:
                        parts.append(f"  —— {' '.join(attr_parts)}")
                source_tag = {"hitokoto": "一言", "agent": "Agent", "custom": "自定义"}.get(
                    r.get("source", ""), r.get("source", "")
                )
                parts.append(f"  [{source_tag}]")
                lines.append("".join(parts))

            return "\n".join(lines)
        except Exception as e:
            return f"读取历史失败: {e}"
