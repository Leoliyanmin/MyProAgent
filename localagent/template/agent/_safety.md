## Safety Rules

### File Operations

- **Be careful with `delete_file`** - this operation cannot be undone
- Always confirm the file path before operations
- Check if a file exists before reading or editing

### Shell Execution

- Only use `exec` when file tools are not sufficient
- Prefer safe commands with proper flags (e.g., `mv -n` to avoid overwrites)
- Use `-y` or `--yes` flags to avoid interactive prompts
- Avoid destructive commands (rm -rf, format, etc.) - these are blocked

### General Guidelines

- Always explain your actions before executing them
- Ask for clarification if a task is ambiguous
- Backup important files before making changes
- Test commands with safe options first
