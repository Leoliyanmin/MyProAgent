## ADDED Requirements

### Requirement: Session import from JSONL files

The system SHALL import each `.jsonl` file in the `.sessions/` directory into the `session` and `chat` SQLite tables, preserving original timestamps and message content.

#### Scenario: Import a session with messages
- **WHEN** a `.jsonl` file contains a metadata line (`_type: "metadata"`) followed by message lines with `role`, `content`, and `timestamp`
- **THEN** the system creates one row in `session` with `session_title` set to the original session key, and one row in `chat` per message line, preserving `chat_role`, `chat_message_content`, and `chat_created_at`

#### Scenario: Extract user_id from session key
- **WHEN** the session key follows pattern `<email>_<scope>` (e.g., `12311022@mail.sustech.edu.cn_default`)
- **THEN** the system extracts the email portion as `user_id`
- **WHEN** the session key is `default`
- **THEN** the system uses `local_test_user@mail.sustech.edu.cn` as `user_id`

#### Scenario: Skip file-manager sessions
- **WHEN** the session key contains `file-manager`
- **THEN** the system skips the file (no `session`/`chat` rows created)

#### Scenario: Skip on duplicate session
- **WHEN** a session with the same `user_id` and `session_title` (original key) already exists in the database
- **THEN** the system skips that session and all its messages

#### Scenario: Skip if user does not exist
- **WHEN** the extracted `user_id` does not exist in the `users` table
- **THEN** the system logs a warning and skips that session

### Requirement: Memory history import

The system SHALL import `.memory/history.jsonl` entries as `chat` messages under a dedicated import session.

#### Scenario: Import history entries
- **WHEN** `.memory/history.jsonl` contains entries with `timestamp` and `content`
- **THEN** the system creates a session with `session_title = "memory-import"`, then inserts each entry as a `chat` message with `chat_role = "user"`, `chat_message_content = content`, and `chat_created_at = timestamp`

#### Scenario: Skip if memory import session already exists
- **WHEN** a session with `session_title = "memory-import"` already exists for the target user
- **THEN** the system skips the memory import for that user
