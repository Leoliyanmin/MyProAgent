"""File management tools for local agent."""

import os
import fnmatch
from pathlib import Path
from typing import Any
from dataclasses import dataclass


@dataclass
class ToolSchema:
    """Tool schema definition."""
    name: str
    description: str
    parameters: dict[str, Any]

    def to_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class BaseTool:
    """Base class for tools."""

    name: str = ""
    description: str = ""
    parameters: dict[str, Any] = {}

    def to_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    async def execute(self, **kwargs) -> str:
        raise NotImplementedError


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


class ListDirTool(BaseTool):
    """List directory contents."""

    name = "list_dir"
    description = "List files and directories in a directory. Use this to explore the file structure."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to directory to list (defaults to workspace root)",
            },
        },
        "required": [],
    }

    def __init__(self, workspace: Path):
        self.workspace = workspace

    def _resolve_path(self, path: str | None) -> Path:
        if path is None:
            return self.workspace
        p = Path(path)
        if p.is_absolute():
            return p
        return self.workspace / p

    async def execute(self, path: str | None = None) -> str:
        try:
            dir_path = self._resolve_path(path)
            if not dir_path.exists():
                return f"Error: Directory not found: {dir_path}"
            if not dir_path.is_dir():
                return f"Error: Not a directory: {dir_path}"
            items = []
            for item in sorted(dir_path.iterdir()):
                if item.is_dir():
                    items.append(f"[DIR]  {item.name}/")
                else:
                    size = item.stat().st_size
                    items.append(f"[FILE] {item.name} ({size} bytes)")
            if not items:
                return f"Directory {dir_path} is empty"
            return f"Contents of {dir_path}:\n" + "\n".join(items)
        except Exception as e:
            return f"Error listing directory: {e}"


class SearchFilesTool(BaseTool):
    """Search for files by pattern."""

    name = "search_files"
    description = "Search for files matching a pattern. Supports glob patterns like *.py or **/*.md"
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Glob pattern to match files (e.g., *.py, **/*.md, test_*.txt)",
            },
            "path": {
                "type": "string",
                "description": "Directory to search in (defaults to workspace root)",
            },
        },
        "required": ["pattern"],
    }

    def __init__(self, workspace: Path):
        self.workspace = workspace

    def _resolve_path(self, path: str | None) -> Path:
        if path is None:
            return self.workspace
        p = Path(path)
        if p.is_absolute():
            return p
        return self.workspace / p

    async def execute(self, pattern: str, path: str | None = None) -> str:
        try:
            search_path = self._resolve_path(path)
            if not search_path.exists():
                return f"Error: Directory not found: {search_path}"
            matches = list(search_path.glob(pattern))
            if not matches:
                return f"No files matching '{pattern}' found in {search_path}"
            results = []
            for match in sorted(matches)[:50]:
                rel_path = match.relative_to(search_path)
                if match.is_dir():
                    results.append(f"[DIR]  {rel_path}/")
                else:
                    results.append(f"[FILE] {rel_path}")
            if len(matches) > 50:
                results.append(f"\n... ({len(matches) - 50} more results)")
            return f"Found {len(matches)} matches:\n" + "\n".join(results)
        except Exception as e:
            return f"Error searching files: {e}"


class GrepTool(BaseTool):
    """Search for text in files."""

    name = "grep"
    description = "Search for text patterns in files. Use this to find code or text containing specific strings."
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Text pattern to search for",
            },
            "path": {
                "type": "string",
                "description": "File or directory to search in (defaults to workspace root)",
            },
            "glob": {
                "type": "string",
                "description": "File pattern to limit search (e.g., *.py)",
            },
        },
        "required": ["pattern"],
    }

    def __init__(self, workspace: Path):
        self.workspace = workspace

    def _resolve_path(self, path: str | None) -> Path:
        if path is None:
            return self.workspace
        p = Path(path)
        if p.is_absolute():
            return p
        return self.workspace / p

    async def execute(
        self,
        pattern: str,
        path: str | None = None,
        glob: str | None = None,
    ) -> str:
        try:
            search_path = self._resolve_path(path)
            if not search_path.exists():
                return f"Error: Path not found: {search_path}"

            results = []
            files_to_search = []

            if search_path.is_file():
                files_to_search = [search_path]
            else:
                pattern_glob = glob or "*"
                files_to_search = [
                    f for f in search_path.rglob(pattern_glob)
                    if f.is_file()
                ]

            for file_path in files_to_search[:100]:
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    lines = content.splitlines()
                    for i, line in enumerate(lines, 1):
                        if pattern.lower() in line.lower():
                            rel_path = file_path.relative_to(self.workspace)
                            results.append(f"{rel_path}:{i}: {line.strip()[:100]}")
                except Exception:
                    continue

            if not results:
                return f"No matches found for '{pattern}'"
            if len(results) > 30:
                return "\n".join(results[:30]) + f"\n\n... ({len(results) - 30} more matches)"
            return "\n".join(results)
        except Exception as e:
            return f"Error searching: {e}"


class FileTools:
    """Collection of file management tools."""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self._tools: dict[str, BaseTool] = {
            "read_file": ReadFileTool(workspace),
            "write_file": WriteFileTool(workspace),
            "edit_file": EditFileTool(workspace),
            "list_dir": ListDirTool(workspace),
            "search_files": SearchFilesTool(workspace),
            "grep": GrepTool(workspace),
        }

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def all_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    def get_schemas(self) -> list[dict[str, Any]]:
        return [t.to_schema() for t in self._tools.values()]
