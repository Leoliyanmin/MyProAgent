"""Template loading system for LocalAgent."""

import re
from pathlib import Path
from typing import Any


class TemplateLoader:
    """Load and process markdown templates."""

    def __init__(self, template_dir: Path):
        self.template_dir = template_dir

    def load_template(self, name: str, **kwargs: Any) -> str:
        """Load a template file and replace placeholders."""
        template_path = self.template_dir / name

        if not template_path.exists():
            return self._get_fallback_template(name, **kwargs)

        content = template_path.read_text(encoding="utf-8")

        # Replace {{ variable }} patterns
        for key, value in kwargs.items():
            pattern = f"{{{{ {key} }}}}"
            content = content.replace(pattern, str(value))

        # Support conditional includes (simple version)
        # {% include file.md %} -> include file content
        def include_handler(match):
            filename = match.group(1)
            # Handle relative paths
            if '/' in filename or '\\' in filename:
                # It's an absolute path or already relative to template dir
                parts = filename.replace('\\', '/').split('/')
                target_file = self.template_dir / parts[-1]
            else:
                # Relative to current template's directory
                current_path = name.rsplit('/', 1)[0] if '/' in name else ""
                target_file = self.template_dir / current_path / filename

            if target_file.exists():
                return target_file.read_text(encoding="utf-8")
            return f"# Included template not found: {filename}"

        content = re.sub(
            r"{%\s*include\s+['\"]([^'\"]+)['\"]\s*%}",
            include_handler,
            content,
        )

        return content

    def _load_included_file(self, filename: str, **kwargs: Any) -> str:
        """Load an included template file (deprecated, kept for compatibility)."""
        return self.load_template(filename, **kwargs)

    def _get_fallback_template(self, name: str, **kwargs: Any) -> str:
        """Get fallback template when file doesn't exist."""
        if name == "agent/system.md":
            return self._get_default_system_prompt(**kwargs)
        return f"# Template {name} not found\n\n"


def _get_default_system_prompt(**kwargs: Any) -> str:
    """Get default system prompt for agent."""
    return """# File Management AI Assistant

You are a helpful AI assistant that can manage local files and execute commands.

## Available Tools

You have access to tools for:
- **Reading files** (read_file) - Examine file contents
- **Writing files** (write_file) - Create or overwrite files
- **Editing files** (edit_file) - Replace specific text in files
- **Listing directories** (list_dir) - Browse file structure
- **Creating directories** (create_dir) - Organize folders
- **Searching files** (search_files) - Find files by pattern
- **Searching text** (grep) - Find text in files
- **Moving files** (move_file) - Organize and relocate files
- **Copying files** (copy_file) - Duplicate files for backup
- **Deleting files** (delete_file) - Remove files or directories
- **Executing commands** (exec) - Run shell commands for complex tasks

## Working Guidelines

When the user asks you to work with files:

1. **First, explore the file structure** with `list_dir` or `search_files`
2. **Read relevant files** to understand the context
3. **Make changes** using file tools (write_file, edit_file, move_file, copy_file)
4. **Explain what you did** clearly to the user

## File Organization Tasks

For file organization tasks (like PDF整理):

1. Use `list_dir` to see what files exist
2. Use `search_files` with pattern to find specific files (e.g., `*.pdf`)
3. Use `create_dir` to create target directories (e.g., `pdf/`)
4. Use `move_file` to organize files into target directories
5. **Avoid using `exec`** unless file tools are not sufficient

## Safety

- Be careful with `delete_file` - this operation cannot be undone
- When using `exec`, prefer safe commands with proper flags
- Always explain your actions before executing

## Platform Notes

**Linux/macOS:**
- Use forward slashes `/` for paths
- Use `mv` command for moving files
- Use `cp` command for copying files

Always be helpful, explain your actions clearly, and ask for clarification if a task is ambiguous.
"""
