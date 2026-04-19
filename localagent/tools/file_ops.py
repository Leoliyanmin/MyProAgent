"""File operation tools (move, copy, delete)."""

from pathlib import Path

from .base import BaseTool


class MoveFileTool(BaseTool):
    """Move or rename a file."""

    name = "move_file"
    description = "Move or rename a file or directory. Creates parent directories if needed."
    parameters = {
        "type": "object",
        "properties": {
            "source": {
                "type": "string",
                "description": "Source path to move (relative to workspace or absolute)",
            },
            "destination": {
                "type": "string",
                "description": "Destination path (relative to workspace or absolute)",
            },
        },
        "required": ["source", "destination"],
    }

    def __init__(self, workspace: Path):
        self.workspace = workspace

    def _resolve_path(self, path: str) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        return self.workspace / p

    async def execute(self, source: str, destination: str) -> str:
        try:
            source_path = self._resolve_path(source)
            dest_path = self._resolve_path(destination)

            if not source_path.exists():
                return f"Error: Source not found: {source_path}"

            dest_path.parent.mkdir(parents=True, exist_ok=True)

            if dest_path.exists():
                return f"Error: Destination already exists: {dest_path}"

            source_path.rename(dest_path)
            return f"Successfully moved {source_path} to {dest_path}"
        except Exception as e:
            return f"Error moving file: {e}"


class DeleteFileTool(BaseTool):
    """Delete a file or directory."""

    name = "delete_file"
    description = "Delete a file or directory. Be careful as this operation cannot be undone."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file or directory to delete (relative to workspace or absolute)",
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
            target_path = self._resolve_path(path)

            if not target_path.exists():
                return f"Error: Path not found: {target_path}"

            if target_path.is_dir():
                for item in target_path.iterdir():
                    item.unlink()
                target_path.rmdir()
            else:
                target_path.unlink()

            return f"Successfully deleted: {target_path}"
        except Exception as e:
            return f"Error deleting file: {e}"


class CopyFileTool(BaseTool):
    """Copy a file or directory."""

    name = "copy_file"
    description = "Copy a file or directory to a new location."
    parameters = {
        "type": "object",
        "properties": {
            "source": {
                "type": "string",
                "description": "Source path to copy (relative to workspace or absolute)",
            },
            "destination": {
                "type": "string",
                "description": "Destination path (relative to workspace or absolute)",
            },
        },
        "required": ["source", "destination"],
    }

    def __init__(self, workspace: Path):
        self.workspace = workspace

    def _resolve_path(self, path: str) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        return self.workspace / p

    async def execute(self, source: str, destination: str) -> str:
        try:
            import shutil

            source_path = self._resolve_path(source)
            dest_path = self._resolve_path(destination)

            if not source_path.exists():
                return f"Error: Source not found: {source_path}"

            dest_path.parent.mkdir(parents=True, exist_ok=True)

            if dest_path.exists():
                return f"Error: Destination already exists: {dest_path}"

            if source_path.is_dir():
                shutil.copytree(source_path, dest_path)
            else:
                shutil.copy2(source_path, dest_path)

            return f"Successfully copied {source_path} to {dest_path}"
        except Exception as e:
            return f"Error copying file: {e}"
