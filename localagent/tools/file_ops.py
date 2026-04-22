"""File operation tools (move, copy, delete)."""

from pathlib import Path
import json

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


_DELETE_CONFIRMATION_PREFIX = "[DELETE_CONFIRMATION]"


class DeleteFileTool(BaseTool):
    """Request deletion of a file or directory. Does NOT delete immediately.
    Returns a confirmation request that must be approved by the user before
    actual deletion occurs."""

    name = "delete_file"
    description = "Request deletion of a file or directory. IMPORTANT: This tool does NOT delete immediately. It returns a confirmation request that the user must approve. Use this tool when you believe a file should be deleted."
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

            file_type = "directory" if target_path.is_dir() else "file"
            size_info = ""
            if target_path.is_file():
                size = target_path.stat().st_size
                size_info = f" ({size} bytes)"

            detail = json.dumps({
                "path": path,
                "resolved": str(target_path),
                "type": file_type,
                "size_info": size_info,
            }, ensure_ascii=False)

            return f"{_DELETE_CONFIRMATION_PREFIX}{detail}\nDeletion of {file_type} '{path}' is pending user confirmation. Report this to the user and wait for their approval."
        except Exception as e:
            return f"Error checking file for deletion: {e}"


class DeleteExecutor:
    """Actually executes confirmed deletions. NOT a tool - called by the frontend API."""

    @staticmethod
    def execute(path: str) -> str:
        p = Path(path)
        if not p.exists():
            return f"Error: Path not found: {p}"
        try:
            if p.is_dir():
                import shutil
                shutil.rmtree(p)
            else:
                p.unlink()
            return f"Successfully deleted: {p}"
        except Exception as e:
            return f"Error deleting: {e}"


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