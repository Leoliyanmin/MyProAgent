"""Directory management tools."""

from pathlib import Path

from .base import BaseTool


class ListDirTool(BaseTool):
    """List directory contents."""

    name = "list_dir"
    description = "List files and directories in a directory. Use this to explore file structure."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the directory to list (defaults to workspace root)",
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


class CreateDirTool(BaseTool):
    """Create a directory."""

    name = "create_dir"
    description = "Create a directory. Creates parent directories if they don't exist."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the directory to create (relative to workspace or absolute)",
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
            dir_path = self._resolve_path(path)
            if dir_path.exists():
                return f"Directory already exists: {dir_path}"
            dir_path.mkdir(parents=True, exist_ok=True)
            return f"Successfully created directory: {dir_path}"
        except Exception as e:
            return f"Error creating directory: {e}"
