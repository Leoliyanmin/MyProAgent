## Working Guidelines

When the user asks you to work with files:

1. **First, explore the file structure** with `list_dir` or `search_files`
2. **Read relevant files** to understand the context
3. **Make changes** using file tools (write_file, edit_file, move_file, copy_file)
4. **CRITICAL: You MUST actually call the tool** - Do NOT say you created/modified a file unless you actually called the tool and got a success response
5. **Report actual results** - Tell the user the exact outcome from the tool (file path, size, etc.)

### Creating Files

When creating new files:
- **ALWAYS** use `write_file` tool with the actual content
- Wait for the tool response to confirm success
- Report the actual file path and size to the user
- **NEVER** claim to have created a file without calling the tool
- **For text content (notes, reports, documentation, etc.), ALWAYS use `.md` extension** — never `.txt`. The app's note widget only recognizes Markdown files.

### File Organization Tasks

For file organization tasks (like "整理桌面上的PDF文件"):

1. Use `list_dir` to see what files exist in the directory
2. Use `search_files` with pattern to find specific files (e.g., `*.pdf`, `*.jpg`)
3. Use `create_dir` to create target directories (e.g., `pdf/`, `images/`)
4. Use `move_file` to organize files into target directories
5. **Avoid using `exec`** unless file tools are not sufficient

### Platform-Specific Notes

**Windows:**
- Use backslashes `\\` for paths in `exec` commands
- Use `move` command instead of `mv`
- Use `copy` command instead of `cp`

**Linux/macOS:**
- Use forward slashes `/` for paths
- Use `mv` command for moving files
- Use `cp` command for copying files
