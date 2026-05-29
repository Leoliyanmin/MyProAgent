## Context

The project has three local data stores outside SQLite:
1. `.sessions/*.jsonl` — Session files managed by `localagent/session.py` (SessionManager). Each file contains a metadata line (`_type: "metadata"`) and message lines (`role`, `content`, `timestamp`). Session keys follow pattern `<user_id>_<scope>` (e.g., `default`, `12311022@mail.sustech.edu.cn_default`).
2. `.memory/history.jsonl` — User prompt history managed by `localagent/memory.py` (MemoryStore). Each line is `{timestamp, content, cursor}`.
3. `personality/profiles/*.json` — Personality profiles managed by `personality/user_profile_store.py`. Keyed by `<user_id>.json`, containing interests, skills, MBTI, preferences, etc.

The SQLite database (`local.db`) already has tables `session`, `chat`, and `user_match_profile` with matching handles (`ChatHandle`, `MatchHandle`) — but these tables are empty. The existing command/operations/handle layers are ready to accept data.

## Goals / Non-Goals

**Goals:**
- Import all `.sessions/*.jsonl` data into `session` + `chat` tables with correct user_id and timestamp preservation
- Import `.memory/history.jsonl` entries into `chat` table under a dedicated session per user
- Import `personality/profiles/*.json` into `user_match_profile` table
- Use existing `ChatHandle` and `MatchHandle` APIs (no new command/operations needed)
- Preserve original JSONL/JSON files (read-only migration)
- Update `sync_state` rows after each import to maintain consistency
- Handle edge cases: duplicate prevention, missing user records, empty files

**Non-Goals:**
- Changing the database schema (no new tables or columns)
- Modifying `localagent/memory.py` or `localagent/session.py` to use SQLite (out of scope; this is a one-time migration)
- Creating a live sync between JSONL files and SQLite
- Importing `.sessions/file-manager*.jsonl` — these are file-manager scope sessions with no SQLite destination

## Decisions

### 1. Script placement: standalone migration script

**Chosen**: A single `database_migrate_local_data.py` script under `local_backend/database/code/`.

**Rationale**: One-time operation, not part of regular init flow. Standalone = easy to re-run, test, or skip. Avoids bloating `database_init.py`.

**Alternatives considered**:
- Integrating into `database_init.py` — rejected because init runs every setup; migration should be opt-in
- Adding to `ChatHandle`/`MatchHandle` — rejected because handles are for business logic, not one-off data migration

### 2. Session → user_id mapping

**Chosen**: Extract user_id from the session key as follows:
- `"default"` → user_id = `"local_test_user@mail.sustech.edu.cn"` (hardcoded fallback, since this is the only user in the system)
- `"<email>_<scope>"` → user_id = the email portion (before first underscore)

**Rationale**: The session key format is `<user_identity>_<scope_name>`. The existing user table has `local_test_user@mail.sustech.edu.cn` as the known user. For ambiguous keys like "default", we infer the user.

**Alternatives considered**:
- Scanning all session messages for user_id → overkill, same result

### 3. .memory/history.jsonl → session mapping

**Chosen**: Create a session per user with `session_title = "memory-import"` and insert each history line as a `user` role `chat` message.

**Rationale**: History entries are user prompts only (no assistant responses). A dedicated import session groups them logically. No cursor/timestamp loss.

**Alternatives considered**:
- Skipping .memory entries — rejected, these contain useful interaction history
- Merging into the "default" session — rejected, different data source, cleaner to separate

### 4. Personality profile → user_match_profile mapping

**Chosen**: `user_id` from filename (`<user_id>.json` → strip `.json`), `answers` = `json.dumps(entire_profile, ensure_ascii=False)`, `is_open` = `0`, `last_match_time` = profile's `last_updated`.

**Rationale**: The `answers` column is TEXT and documented as "Serialized profile answers, stored as text JSON." The full profile JSON fits naturally here. The profile contains interests, skills, MBTI, preferences—all relevant for matching.

### 5. Duplicate handling (idempotency)

**Chosen**: 
- **sessions**: Skip if a session with same `user_id` and `session_title` (the original key) already exists
- **chat messages**: Skip if a chat with same `session_id`, `chat_role`, `chat_message_content` exists (approximate dedup)
- **profiles**: Use `MatchHandle.upsert_profile()` which handles idempotency via `INSERT OR REPLACE`

**Rationale**: The script should be safe to re-run. Not using complex dedup logic — reasonable effort to avoid obvious duplicates.

### 6. Execution: sequential, not parallel

**Chosen**: Process sources sequentially: sessions → memory → profiles. Within each source, process files one at a time.

**Rationale**: Migration is a one-time operation run locally. No performance pressure. Sequential execution is simpler and avoids SQLite concurrency issues.

## Risks / Trade-offs

- **[Risk] File-manager sessions skipped**: `file-manager.jsonl` and `file-manager__Users_yanmin_Downloads_test.jsonl` have no database destination → skipped. Minimal impact.
- **[Risk] Duplicate chat inserts**: Dedup is approximate (role + content match). In rare cases, genuinely duplicate messages might be skipped. Mitigation: dedup is essential for idempotency.
- **[Risk] User doesn't exist in users table**: If a session key maps to a user_id not in `users` table, the FK constraint will reject inserts. Mitigation: script checks for user existence before importing; logs warnings for missing users.
- **[Risk] Large memory file**: `.memory/history.jsonl` is currently 120 lines. If it grows, import time increases linearly. Mitigation: batch inserts using transactions (one per user).
- **[Trade-off] Migration is manual**: User must run the script manually. This is intentional — avoids accidental data duplication. Documentation will specify when/how to run.
