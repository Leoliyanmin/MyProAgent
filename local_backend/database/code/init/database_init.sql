-- Local client SQLite database initialization
-- Mode: local storage (authoritative on device)

PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    user_email TEXT NOT NULL UNIQUE,
    user_is_active INTEGER NOT NULL DEFAULT 1 CHECK (user_is_active IN (0, 1)),
    user_created_at TEXT NOT NULL,
    user_last_login TEXT,
    user_source_device_id TEXT
);

CREATE TABLE IF NOT EXISTS user_match_profile (
    user_id TEXT PRIMARY KEY,
    answers TEXT NOT NULL,
    is_open INTEGER NOT NULL DEFAULT 0 CHECK (is_open IN (0, 1)),
    last_match_time TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS match_result (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    matched_user_id TEXT NOT NULL,
    similarity_score REAL NOT NULL,
    created_at TEXT NOT NULL,
    is_shared INTEGER NOT NULL DEFAULT 0 CHECK (is_shared IN (0, 1)),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS sync_state (
    user_id TEXT PRIMARY KEY,
    user_data_updated_at TEXT NOT NULL,
    user_last_synced_at TEXT,
    user_version INTEGER NOT NULL DEFAULT 1,
    sync_updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS account (
    account_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    account_platform_type TEXT NOT NULL,
    account_platform_username TEXT NOT NULL,
    content TEXT,
    account_bind_time TEXT,
    account_last_sync_time TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE (user_id, account_platform_type)
);

CREATE TABLE IF NOT EXISTS category (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    category_kind TEXT NOT NULL,
    category_title TEXT NOT NULL,
    category_content TEXT,
    category_link TEXT,
    category_source TEXT,
    category_external_id TEXT,
    category_term TEXT,
    category_meta_json TEXT,
    category_updated_at TEXT,
    category_created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_category_user_kind_link
ON category (
    user_id,
    category_kind,
    COALESCE(category_link, '')
);

CREATE TABLE IF NOT EXISTS data (
    data_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    data_category_id INTEGER NOT NULL,
    data_content_type TEXT NOT NULL,
    data_classification_code INTEGER NOT NULL DEFAULT 1 CHECK (data_classification_code IN (1, 2, 3, 4)),
    data_title TEXT NOT NULL,
    data_content_text TEXT,
    data_link_url TEXT,
    data_release_time TEXT,
    data_ddl_time TEXT,
    data_is_previewable INTEGER NOT NULL CHECK (data_is_previewable IN (0, 1)),
    data_source TEXT,
    data_external_id TEXT,
    data_term TEXT,
    data_week TEXT,
    data_weekday INTEGER,
    data_period_start INTEGER,
    data_period_end INTEGER,
    data_start_time TEXT,
    data_end_time TEXT,
    data_meta_json TEXT,
    data_raw_json TEXT,
    data_updated_at TEXT,
    data_created_at TEXT NOT NULL,
    data_linked_schedule_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (data_category_id) REFERENCES category(category_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_data_user_category_type_link
ON data (
    user_id,
    data_category_id,
    data_content_type,
    COALESCE(data_link_url, '')
);

CREATE TABLE IF NOT EXISTS schedule (
    schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    schedule_event_type TEXT NOT NULL,
    schedule_priority INTEGER NOT NULL DEFAULT 2 CHECK (schedule_priority IN (0, 1, 2, 3)),
    schedule_is_completed INTEGER NOT NULL DEFAULT 0 CHECK (schedule_is_completed IN (0, 1)),
    schedule_title TEXT NOT NULL,
    schedule_start_time TEXT NOT NULL,
    schedule_end_time TEXT NOT NULL,
    schedule_location TEXT,
    schedule_description TEXT,
    schedule_related_link TEXT,
    schedule_recurrence_rule TEXT,
    schedule_color_tag TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS session (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    session_title TEXT NOT NULL DEFAULT '',
    session_created_at TEXT NOT NULL,
    session_last_visited_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS chat (
    chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    chat_role TEXT NOT NULL CHECK (chat_role IN ('user', 'assistant')),
    chat_message_content TEXT NOT NULL,
    thought_trace TEXT,
    chat_tool_calls TEXT,
    chat_tokens_usage TEXT,
    chat_created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES session(session_id)
);

CREATE TABLE IF NOT EXISTS perm (
    perm_id INTEGER PRIMARY KEY AUTOINCREMENT,
    perm_category TEXT NOT NULL,
    perm_is_allowed INTEGER NOT NULL CHECK (perm_is_allowed IN (0, 1)),
    perm_require_confirmation INTEGER NOT NULL CHECK (perm_require_confirmation IN (0, 1)),
    perm_last_modified TEXT NOT NULL,
    perm_call_method TEXT NOT NULL
);

COMMIT;

-- Migration: for existing databases that lack the data_linked_schedule_id column,
-- run this manually: ALTER TABLE data ADD COLUMN data_linked_schedule_id INTEGER;
