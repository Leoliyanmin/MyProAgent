## 1. Session and Chat Import

- [x] 1.1 Create `session_import.py` under `local_backend/database/code/` that reads `.sessions/*.jsonl` files
- [x] 1.2 Implement user_id extraction from session key (email prefix → user_id; "default" → fallback to `local_test_user@mail.sustech.edu.cn`)
- [x] 1.3 Implement session row insertion using ChatOperations (create_session with user_id, session_title=key, timestamps from metadata)
- [x] 1.4 Implement chat message insertion for each message line in each session file
- [x] 1.5 Add skip logic for file-manager sessions and for sessions where user doesn't exist in users table
- [x] 1.6 Add idempotency check: skip sessions with same user_id + session_title already in database

## 2. Memory History Import

- [x] 2.1 Create shared import logic that handles `.memory/history.jsonl` reading
- [x] 2.2 Create a "memory-import" session per user using ChatHandle
- [x] 2.3 Import each history.jsonl line as chat message (role=user, content→message, timestamp→created_at)
- [x] 2.4 Add idempotency check: skip if memory-import session already exists

## 3. Personality Profile Import

- [x] 3.1 Create `profile_import.py` under `local_backend/database/code/` that reads `personality/profiles/*.json`
- [x] 3.2 Extract user_id from filename (`<user_id>.json` → strip extension)
- [x] 3.3 Serialize full profile JSON into `answers` column and upsert into `user_match_profile` using MatchHandle
- [x] 3.4 Set last_match_time from profile's `last_updated` field, is_open = 0

## 4. Integration and Testing

- [x] 4.1 Create unified entry script `database_migrate_local_data.py` that orchestrates all three imports
- [x] 4.2 Add sync_state update after each import batch for affected users
- [x] 4.3 Add summary reporting (counts of sessions/messages/profiles imported)
- [x] 4.4 Test with existing real data files, verify database contents via sqlite3
- [x] 4.5 Test idempotency: run migration twice, verify no duplicates
