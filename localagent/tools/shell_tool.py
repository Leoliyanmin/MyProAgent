"""Shell command execution tool."""

import asyncio
import os
import sys
from pathlib import Path

from .base import BaseTool


class ExecTool(BaseTool):
    """Execute shell commands."""

    name = "exec"
    description = (
        "Execute a shell command and return its output. "
        "Prefer file tools (read_file, write_file, move_file) over shell commands when possible. "
        "Use -y or --yes flags to avoid interactive prompts. "
        "Output is truncated at 10,000 characters; timeout defaults to 60 seconds."
    )
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute",
            },
            "working_dir": {
                "type": "string",
                "description": "Optional working directory for the command",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default 60, max 300)",
                "minimum": 1,
                "maximum": 300,
            },
        },
        "required": ["command"],
    }

    def __init__(
        self,
        workspace: Path | None = None,
        allow_patterns: list[str] | None = None,
    ):
        self.workspace = workspace
        self.default_timeout = 60
        self.max_timeout = 300
        self.max_output = 10_000
        self._is_windows = sys.platform == "win32"

        # Safety: deny dangerous commands by default
        self.deny_patterns = [
            r"\brm\s+-[rf]{1,2}\b",          # rm -r, rm -rf
            r"\bdel\s+/[fq]\b",              # del /f, del /q
            r"\brmdir\s+/s\b",               # rmdir /s
            r"(?:^|[;&|]\s*)format\b",       # format
            r"\b(mkfs|diskpart)\b",          # disk operations
            r"\bdd\s+if=",                   # dd
            r">\s*/dev/sd",                  # write to disk
            r"\b(shutdown|reboot|poweroff)\b",  # system power
        ]
        self.allow_patterns = allow_patterns or []

    async def execute(
        self,
        command: str,
        working_dir: str | None = None,
        timeout: int | None = None,
    ) -> str:
        """Execute a shell command."""
        # Safety check
        guard_error = self._guard_command(command)
        if guard_error:
            return guard_error

        # Set working directory
        cwd = working_dir or os.getcwd()
        if self.workspace and not Path(working_dir or cwd).is_absolute():
            cwd = str(self.workspace)

        # Set timeout
        effective_timeout = min(timeout or self.default_timeout, self.max_timeout)

        try:
            # Execute command
            if self._is_windows:
                comspec = os.environ.get("COMSPEC", "cmd.exe")
                process = await asyncio.create_subprocess_exec(
                    comspec,
                    "/c",
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd,
                )
            else:
                bash = os.path.join("/bin", "bash")
                if not os.path.exists(bash):
                    bash = "/bin/bash"
                process = await asyncio.create_subprocess_exec(
                    bash,
                    "-c",
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd,
                )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=effective_timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    pass
                return f"Error: Command timed out after {effective_timeout} seconds"

            # Format output
            output_parts = []
            if stdout:
                output_parts.append(stdout.decode("utf-8", errors="replace"))
            if stderr:
                stderr_text = stderr.decode("utf-8", errors="replace")
                if stderr_text.strip():
                    output_parts.append(f"STDERR:\n{stderr_text}")

            output_parts.append(f"\nExit code: {process.returncode}")

            result = "\n".join(output_parts) if output_parts else "(no output)"

            # Truncate if too long
            if len(result) > self.max_output:
                half = self.max_output // 2
                result = (
                    result[:half]
                    + f"\n\n... ({len(result) - self.max_output:,} chars truncated) ...\n\n"
                    + result[-half:]
                )

            return result

        except Exception as e:
            return f"Error executing command: {str(e)}"

    def _guard_command(self, command: str) -> str | None:
        """Check if command is blocked by safety rules."""
        import re

        cmd = command.strip().lower()

        # Check deny patterns
        for pattern in self.deny_patterns:
            if re.search(pattern, cmd):
                return f"Error: Command blocked by safety guard (dangerous pattern detected)"

        # Check allow patterns (if specified)
        if self.allow_patterns:
            if not any(re.search(p, cmd) for p in self.allow_patterns):
                return "Error: Command blocked by safety guard (not in allowlist)"

        return None
