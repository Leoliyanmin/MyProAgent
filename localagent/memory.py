"""Memory consolidation for local agent."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .provider import OpenAICompatProvider


@dataclass
class MemoryEntry:
    """A memory entry from conversation history."""

    timestamp: str
    content: str
    cursor: int = 0


@dataclass
class ConsolidationResult:
    """Result of memory consolidation."""

    success: bool
    entries_processed: int
    summary: str | None = None


def _sanitize_user_id(user_id: str | None) -> str:
    """Sanitize user_id for use as a directory name."""
    if user_id is None:
        return ""
    return user_id.replace("/", "_").replace("\\", "_").replace(":", "_").replace("@", "_at_")


class MemoryStore:
    """Stores memory and history for consolidation.

    When ``user_id`` is provided, all files are stored under
    ``.memory/{user_id}/`` for per-user isolation.
    When ``user_id`` is None, the root ``.memory/`` is used (backward compatible).
    """

    def __init__(self, workspace: Path):
        self.workspace = Path(workspace).resolve()

    def _user_dir(self, user_id: str | None) -> Path:
        """Return the per-user memory directory, creating it if needed."""
        base = self.workspace / ".memory"
        if user_id:
            d = base / _sanitize_user_id(user_id)
        else:
            d = base
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _history_file(self, user_id: str | None) -> Path:
        return self._user_dir(user_id) / "history.jsonl"

    def _cursor_file(self, user_id: str | None) -> Path:
        return self._user_dir(user_id) / "cursor.txt"

    def _memory_file(self, user_id: str | None) -> Path:
        return self._user_dir(user_id) / "MEMORY.md"

    def add_entry(self, content: str, user_id: str | None = None) -> None:
        """Add an entry to history."""
        uf = self._cursor_file(user_id)
        cursor = self._get_next_cursor(uf)
        entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            content=content,
            cursor=cursor,
        )
        hf = self._history_file(user_id)
        with open(hf, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": entry.timestamp,
                "content": entry.content,
                "cursor": entry.cursor,
            }, ensure_ascii=False) + "\n")

    @staticmethod
    def _get_next_cursor(cursor_file: Path) -> int:
        """Get next cursor value."""
        if not cursor_file.exists():
            return 0
        try:
            with open(cursor_file, encoding="utf-8") as f:
                return int(f.read().strip()) + 1
        except Exception:
            return 0

    def get_last_cursor(self, user_id: str | None = None) -> int:
        """Get the last processed cursor."""
        uf = self._cursor_file(user_id)
        if not uf.exists():
            return 0
        try:
            with open(uf, encoding="utf-8") as f:
                return int(f.read().strip())
        except Exception:
            return 0

    def update_cursor(self, cursor: int, user_id: str | None = None) -> None:
        """Update the last processed cursor."""
        uf = self._cursor_file(user_id)
        with open(uf, "w", encoding="utf-8") as f:
            f.write(str(cursor))

    def read_unprocessed_history(
        self, since_cursor: int = 0, user_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Read unprocessed history entries."""
        hf = self._history_file(user_id)
        if not hf.exists():
            return []

        entries = []
        with open(hf, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get("cursor", 0) > since_cursor:
                        entries.append(data)
                except Exception:
                    continue

        return sorted(entries, key=lambda x: x.get("cursor", 0))

    def get_memory(self, user_id: str | None = None) -> str:
        """Get current memory content."""
        mf = self._memory_file(user_id)
        if not mf.exists():
            return "# Memory\n\nNo memory yet."
        return mf.read_text(encoding="utf-8")

    def update_memory(self, content: str, user_id: str | None = None) -> None:
        """Update memory content."""
        mf = self._memory_file(user_id)
        mf.write_text(content, encoding="utf-8")


class Dream:
    """Memory consolidator: analyzes history and updates memory files."""

    CONSOLIDATION_PROMPT = """You are analyzing conversation history to update memory files.

You have access to:
- MEMORY.md: Long-term memory
- read_file: Read file contents
- edit_file: Edit files by replacing text

Your task:
1. Read the conversation history provided
2. Read current MEMORY.md
3. Identify important information to preserve or update
4. Use edit_file to make targeted updates to MEMORY.md

Focus on:
- User preferences and requirements
- Important decisions made
- Repeated patterns or questions
- Key information that should be remembered

Rules:
- Keep the structure of MEMORY.md intact
- Make incremental edits, don't replace the entire file
- Be concise and factual
- Add timestamps for new entries in format: <!-- YYYY-MM-DD -->
"""

    def __init__(
        self,
        store: MemoryStore,
        provider: OpenAICompatProvider,
        tool_registry: Any | None = None,
        max_batch_size: int = 20,
        max_iterations: int = 10,
    ):
        self.store = store
        self.provider = provider
        self.max_batch_size = max_batch_size
        self.max_iterations = max_iterations
        self.tools = tool_registry

    async def run(self, user_id: str | None = None) -> ConsolidationResult:
        """Process unprocessed history entries."""
        last_cursor = self.store.get_last_cursor(user_id=user_id)
        entries = self.store.read_unprocessed_history(
            since_cursor=last_cursor, user_id=user_id
        )

        if not entries:
            return ConsolidationResult(success=False, entries_processed=0)

        batch = entries[:self.max_batch_size]
        final_cursor = batch[-1]["cursor"] if batch else last_cursor

        # Build history text
        history_text = "\n".join(
            f"[{e['timestamp']}] {e['content']}" for e in batch
        )

        # Build messages
        messages = [
            {"role": "system", "content": self.CONSOLIDATION_PROMPT},
            {
                "role": "user",
                "content": f"""Conversation history to analyze:

{history_text}

Please analyze this history and update MEMORY.md accordingly."""
            }
        ]

        # Process with agent
        tool_calls_made = 0
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1

            response = await self.provider.chat(
                messages=messages,
                tools=self.tools.get_schemas(),
            )

            if not response.tool_calls:
                break

            # Add assistant message
            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": response.content,
            }
            if response.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                        },
                    }
                    for tc in response.tool_calls
                ]
            messages.append(assistant_msg)

            # Execute tools
            for tc in response.tool_calls:
                tool = self.tools.get(tc.name)
                if tool:
                    try:
                        result = await tool.execute(**tc.arguments)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": result,
                        })
                        tool_calls_made += 1
                    except Exception as e:
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": f"Error: {e}",
                        })

        self.store.update_cursor(final_cursor, user_id=user_id)

        return ConsolidationResult(
            success=True,
            entries_processed=len(batch),
            summary=response.content
        )
