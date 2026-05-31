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

CREATE TABLE IF NOT EXISTS event (
    event_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           TEXT NOT NULL,
    event_title       TEXT NOT NULL,
    event_type        TEXT NOT NULL DEFAULT 'manual',
    event_source      TEXT NOT NULL DEFAULT 'manual',
    event_start_time  TEXT,
    event_end_time    TEXT,
    event_location    TEXT,
    event_description TEXT,
    event_link_url    TEXT,
    event_is_completed INTEGER DEFAULT 0,
    event_show_in_todo  INTEGER DEFAULT 1,
    event_priority    INTEGER DEFAULT 2,
    event_color_tag   TEXT DEFAULT '#007aff',
    event_meta_json   TEXT,
    event_created_at  TEXT NOT NULL,
    event_updated_at  TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_event_user_type ON event(user_id, event_type);
CREATE INDEX IF NOT EXISTS idx_event_user_todo ON event(user_id, event_show_in_todo);
CREATE INDEX IF NOT EXISTS idx_event_user_source ON event(user_id, event_source);

CREATE TABLE IF NOT EXISTS user_setting (
    user_id              TEXT PRIMARY KEY,
    avatar_url           TEXT,
    bio                  TEXT,
    full_name            TEXT,
    current_focus        TEXT,
    work_preference      TEXT,
    skills               TEXT,
    theme_config         TEXT,
    daily_quote          TEXT,
    notification_enabled INTEGER NOT NULL DEFAULT 1,
    privacy_share_data   INTEGER NOT NULL DEFAULT 0,
    updated_at           TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS daily_quote_history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      TEXT NOT NULL,
    quote_text   TEXT NOT NULL,
    quote_author TEXT DEFAULT '',
    quote_from   TEXT DEFAULT '',
    source       TEXT NOT NULL DEFAULT 'custom',
    created_at   TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE INDEX IF NOT EXISTS idx_daily_quote_history_user_date ON daily_quote_history(user_id, created_at);

CREATE TABLE IF NOT EXISTS email_account (
    account_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             TEXT NOT NULL,
    email_address       TEXT NOT NULL,
    encrypted_password  TEXT NOT NULL,
    bind_time           TEXT,
    last_sync_time      TEXT,
    last_sync_uid       INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS email_message (
    message_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        TEXT NOT NULL,
    account_id     INTEGER NOT NULL,
    mail_uid       TEXT NOT NULL,
    subject        TEXT NOT NULL,
    sender         TEXT NOT NULL,
    recipients     TEXT,
    body_text      TEXT,
    body_html      TEXT,
    received_at    TEXT,
    is_read        INTEGER DEFAULT 0,
    status         INTEGER DEFAULT 0,
    created_at     TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (account_id) REFERENCES email_account(account_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS starred_emails (
    star_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        TEXT NOT NULL,
    email_id       INTEGER NOT NULL,
    reason         TEXT,
    source         TEXT NOT NULL DEFAULT 'manual' CHECK (source IN ('ai', 'manual')),
    starred_at     TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (email_id) REFERENCES email_message(message_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS api_key (
    api_key_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             TEXT NOT NULL,
    key_id              TEXT NOT NULL UNIQUE,
    provider            TEXT NOT NULL,
    api_key_encrypted   TEXT NOT NULL,
    api_base            TEXT NOT NULL,
    model               TEXT NOT NULL DEFAULT '',
    is_active           INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    last_test_success   INTEGER,
    updated_at          TEXT NOT NULL,
    created_at          TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_api_key_user ON api_key(user_id);
CREATE INDEX IF NOT EXISTS idx_api_key_user_provider ON api_key(user_id, provider);

CREATE TABLE IF NOT EXISTS user_personality (
    user_id                       TEXT PRIMARY KEY,
    interests_json                TEXT,
    skills_json                   TEXT,
    preferences_json              TEXT,
    study_work_patterns_json      TEXT,
    personality_indicators_json   TEXT,
    mbti_type                     TEXT,
    mbti_scores_json              TEXT,
    mbti_confidence               REAL,
    mbti_description              TEXT,
    interaction_count             INTEGER NOT NULL DEFAULT 0,
    mbti_last_updated             TEXT,
    last_updated                  TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS interaction_log (
    log_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id                 TEXT NOT NULL,
    conversation_id         TEXT NOT NULL UNIQUE,
    session_id              TEXT,
    platform                TEXT,
    timestamp               TEXT NOT NULL,
    user_message            TEXT,
    intent_category         TEXT,
    keywords_json           TEXT,
    language                TEXT,
    sentiment               TEXT,
    urgency                 TEXT,
    message_length          INTEGER,
    contains_file_reference TEXT,
    agent_response          TEXT,
    agent_response_length   INTEGER,
    follow_up_required      INTEGER,
    suggested_actions_json  TEXT,
    tools_invoked_json      TEXT,
    files_accessed_json     TEXT,
    total_execution_time_ms INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_interaction_log_user ON interaction_log(user_id, timestamp);

CREATE TABLE IF NOT EXISTS activity_log (
    user_id    TEXT    NOT NULL,
    log_date   TEXT    NOT NULL,
    hour       INTEGER NOT NULL CHECK (hour >= 0 AND hour <= 23),
    count      INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT    NOT NULL,
    PRIMARY KEY (user_id, log_date, hour),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_activity_log_user_date ON activity_log(user_id, log_date);

COMMIT;
