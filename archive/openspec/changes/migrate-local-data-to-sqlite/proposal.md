## Why

The project currently stores user interaction data (chat histories, session records, personality profiles) in local JSONL and JSON files under `.sessions/`, `.memory/`, and `personality/profiles/`. The database module already defines the corresponding SQLite tables (`session`, `chat`, `user_match_profile`) and provides handle APIs (`ChatHandle`, `MatchHandle`) to work with them. However, these tables remain empty — the existing local data has never been imported. Migrating this data into SQLite centralizes all user data, makes the existing database handles functional with real data, and aligns with the sync infrastructure that relies on `sync_state`.

## What Changes

- Add a migration script that reads `.sessions/*.jsonl` files and imports each session into the `session` table and each message into the `chat` table (one session per file, with user_id derived from the session key)
- Add a migration script that reads `.memory/history.jsonl` and imports entries as `chat` messages under a dedicated default session for each user
- Add a migration script that reads `personality/profiles/*.json` and imports profile data into the `user_match_profile` table, storing the full profile as serialized JSON in the `answers` column

## Capabilities

### New Capabilities
- `session-chat-import`: Import local JSONL session and chat history files into the `session` and `chat` SQLite tables. Each `.sessions/*.jsonl` file becomes one session row; each message line becomes one chat row. User identity is extracted from the session key.
- `personality-profile-import`: Import local JSON personality profile files into the `user_match_profile` SQLite table. The full profile object is serialized as JSON text into the `answers` column, with user_id mapped from the profile filename.

### Modified Capabilities
<!-- No existing capabilities are being modified. This is a new data import feature. -->

## Impact

- **New files**: Migration scripts in `local_backend/database/code/` (likely as part of `database_init.py` or standalone migration scripts)
- **Existing handles**: `ChatHandle` and `MatchHandle` are used as-is for writing imported data; no changes needed
- **Existing data sources**: `.sessions/`, `.memory/`, `personality/profiles/` are read-only during migration; files are preserved after import by default
- **Database tables**: `session`, `chat`, `user_match_profile` will receive new rows
- **Sync state**: Each import should update `sync_state` for affected users to maintain consistency
