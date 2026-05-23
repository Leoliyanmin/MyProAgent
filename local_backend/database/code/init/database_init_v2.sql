PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

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

CREATE TABLE IF NOT EXISTS tis_course (
    course_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        TEXT NOT NULL,
    course_name    TEXT NOT NULL,
    teacher        TEXT,
    location       TEXT,
    weeks          TEXT,
    term           TEXT,
    raw_data       TEXT,
    created_at     TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, course_name, term)
);

CREATE TABLE IF NOT EXISTS tis_schedule_event (
    event_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id      INTEGER NOT NULL,
    user_id        TEXT NOT NULL,
    day_of_week    INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    week_num       INTEGER NOT NULL,
    period_start   INTEGER NOT NULL,
    period_end     INTEGER NOT NULL,
    start_time     TEXT,
    end_time       TEXT,
    FOREIGN KEY (course_id) REFERENCES tis_course(course_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(course_id, day_of_week, week_num, period_start)
);

CREATE TABLE IF NOT EXISTS bb_course (
    course_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        TEXT NOT NULL,
    bb_course_id   TEXT,
    course_name    TEXT NOT NULL,
    course_link    TEXT,
    raw_data       TEXT,
    created_at     TEXT NOT NULL,
    updated_at     TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, bb_course_id)
);

CREATE TABLE IF NOT EXISTS bb_assignment (
    assignment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id      INTEGER NOT NULL,
    user_id        TEXT NOT NULL,
    title          TEXT NOT NULL,
    description    TEXT,
    link           TEXT,
    due_date       TEXT,
    status         TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'submitted', 'graded')),
    raw_data       TEXT,
    created_at     TEXT NOT NULL,
    FOREIGN KEY (course_id) REFERENCES bb_course(course_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, course_id, link)
);

CREATE TABLE IF NOT EXISTS bb_announcement (
    announcement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id       INTEGER NOT NULL,
    user_id         TEXT NOT NULL,
    title           TEXT NOT NULL,
    content         TEXT,
    link            TEXT,
    posted_at       TEXT,
    created_at      TEXT NOT NULL,
    FOREIGN KEY (course_id) REFERENCES bb_course(course_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, course_id, link)
);

CREATE TABLE IF NOT EXISTS bb_material (
    material_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id     INTEGER NOT NULL,
    user_id       TEXT NOT NULL,
    title         TEXT NOT NULL,
    content       TEXT,
    link          TEXT,
    created_at    TEXT NOT NULL,
    FOREIGN KEY (course_id) REFERENCES bb_course(course_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, course_id, link)
);

CREATE TABLE IF NOT EXISTS email_account (
    account_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             TEXT NOT NULL,
    email_address       TEXT NOT NULL,
    encrypted_password  TEXT NOT NULL,
    bind_time           TEXT,
    last_sync_time      TEXT,
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
    FOREIGN KEY (account_id) REFERENCES email_account(account_id)
);

CREATE TABLE IF NOT EXISTS starred_emails (
    star_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        TEXT NOT NULL,
    email_id       INTEGER NOT NULL,
    reason         TEXT,
    source         TEXT NOT NULL DEFAULT 'manual' CHECK (source IN ('ai', 'manual')),
    starred_at     TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (email_id) REFERENCES email_message(message_id)
);

COMMIT;
