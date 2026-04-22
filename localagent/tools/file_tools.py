"""File reading and writing tools."""

from pathlib import Path

from .base import BaseTool


class ReadFileTool(BaseTool):
    """Read file content."""

    name = "read_file"
    description = "Read the content of a file. Use this to examine file contents."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to read (relative to workspace or absolute)",
            },
        },
        "required": ["path"],
    }

    def __init__(self, workspace: Path):
        self.workspace = workspace

    def _resolve_path(self, path: str) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        return self.workspace / p

    async def execute(self, path: str) -> str:
        try:
            file_path = self._resolve_path(path)
            if not file_path.exists():
                return f"Error: File not found: {file_path}"
            if not file_path.is_file():
                return f"Error: Not a file: {file_path}"
            content = file_path.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            if len(lines) > 500:
                return "\n".join(
                    lines[:500] + [f"\n... (truncated, {len(lines) - 500} more lines)"]
                )
            return content
        except Exception as e:
            return f"Error reading file: {e}"


class WriteFileTool(BaseTool):
    """Write content to a file."""

    name = "write_file"
    description = "Write content to a file. Creates the file if it doesn't exist, overwrites if it does."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to write (relative to workspace or absolute)",
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file",
            },
        },
        "required": ["path", "content"],
    }

    def __init__(self, workspace: Path):
        self.workspace = workspace

    def _resolve_path(self, path: str) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        return self.workspace / p

    async def execute(self, path: str, content: str) -> str:
        try:
            file_path = self._resolve_path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return f"Successfully wrote {len(content)} characters to {file_path}"
        except Exception as e:
            return f"Error writing file: {e}"


class EditFileTool(BaseTool):
    """Edit a file by replacing text."""

    name = "edit_file"
    description = "Edit a file by replacing specific text. Use this for targeted modifications."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file to edit",
            },
            "old_text": {
                "type": "string",
                "description": "Text to find and replace",
            },
            "new_text": {
                "type": "string",
                "description": "Text to replace with",
            },
        },
        "required": ["path", "old_text", "new_text"],
    }

    def __init__(self, workspace: Path):
        self.workspace = workspace

    def _resolve_path(self, path: str) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        return self.workspace / p

    async def execute(self, path: str, old_text: str, new_text: str) -> str:
        try:
            file_path = self._resolve_path(path)
            if not file_path.exists():
                return f"Error: File not found: {file_path}"
            content = file_path.read_text(encoding="utf-8")
            if old_text not in content:
                return f"Error: Text not found in file: {old_text[:50]}..."
            new_content = content.replace(old_text, new_text)
            file_path.write_text(new_content, encoding="utf-8")
            return f"Successfully edited {file_path}"
        except Exception as e:
            return f"Error editing file: {e}"
