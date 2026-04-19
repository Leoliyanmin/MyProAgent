"""File and text search tools."""

from pathlib import Path

from .base import BaseTool


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
