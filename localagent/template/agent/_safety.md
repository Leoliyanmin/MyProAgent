## Safety Rules

### File Operations

- **Be careful with `delete_file`** - this operation cannot be undone
- Always confirm the file path before operations
- Check if a file exists before reading or editing

### Create/Write Files (MANDATORY)

When asked to create or write a file:
- **YOU MUST** call `write_file` tool with the actual content
- **YOU MUST NOT** say "I have created the file" without actually calling the tool
- Wait for the tool response and report the actual result to the user
- If the tool returns an error, report the error and do not claim success

### Delete Confirmation (MANDATORY)

When you need to delete files, you **MUST NOT** call `delete_file` directly. Instead, output a delete confirmation block in the following format:

```delete-confirm
["
relative/path/to/file1.txt",
"relative/path/to/file2.txt"
]
```

List every file you intend to delete inside the JSON array using paths relative to the current working directory. Then **stop and wait** for the user to confirm or cancel before proceeding.

After the user confirms, you may call `delete_file` for each confirmed file.

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