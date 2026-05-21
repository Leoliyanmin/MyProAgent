PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS task (
    task_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id            TEXT NOT NULL,
    title              TEXT NOT NULL,
    description        TEXT,
    priority           INTEGER NOT NULL DEFAULT 2 CHECK (priority IN (0, 1, 2, 3)),
    status             TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed')),
    due_date           TEXT,
    linked_schedule_id INTEGER,
    source             TEXT DEFAULT 'manual',
    created_at         TEXT NOT NULL,
    updated_at         TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS user_setting (
    user_id              TEXT PRIMARY KEY,
    avatar_url           TEXT,
    bio                  TEXT,
    current_focus        TEXT,
    work_preference      TEXT,
    skills               TEXT,
    theme_config         TEXT,
    notification_enabled INTEGER NOT NULL DEFAULT 1,
    privacy_share_data   INTEGER NOT NULL DEFAULT 0,
    updated_at           TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

COMMIT;
