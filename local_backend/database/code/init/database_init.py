import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR.parent.parent / "db" / "local.db"
DEFAULT_SCHEMA_PATH = BASE_DIR / "database_init.sql"

EVENT_TABLE_SQL = """CREATE TABLE IF NOT EXISTS event (
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
)"""

EVENT_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_event_user_type ON event(user_id, event_type)",
    "CREATE INDEX IF NOT EXISTS idx_event_user_todo ON event(user_id, event_show_in_todo)",
    "CREATE INDEX IF NOT EXISTS idx_event_user_source ON event(user_id, event_source)",
]


def _run_migrations(conn: sqlite3.Connection) -> None:
    # password_hash migration
    check = conn.execute(
        "SELECT COUNT(*) FROM pragma_table_info('users') WHERE name='password_hash'"
    ).fetchone()
    if check[0] == 0:
        conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")

    # event table migration
    event_exists = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='event'"
    ).fetchone()
    if event_exists[0] == 0:
        conn.execute(EVENT_TABLE_SQL)
        for idx_sql in EVENT_INDEXES:
            conn.execute(idx_sql)

    # api_key table migration
    api_key_exists = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='api_key'"
    ).fetchone()
    if api_key_exists[0] == 0:
        conn.execute("""CREATE TABLE IF NOT EXISTS api_key (
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
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_api_key_user ON api_key(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_api_key_user_provider ON api_key(user_id, provider)")

    # user_personality table migration
    user_personality_exists = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='user_personality'"
    ).fetchone()
    if user_personality_exists[0] == 0:
        conn.execute("""CREATE TABLE IF NOT EXISTS user_personality (
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
        )""")

    # interaction_log table migration
    interaction_log_exists = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='interaction_log'"
    ).fetchone()
    if interaction_log_exists[0] == 0:
        conn.execute("""CREATE TABLE IF NOT EXISTS interaction_log (
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
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_interaction_log_user ON interaction_log(user_id, timestamp)")


def init_database(db_path: str | Path = DEFAULT_DB_PATH, schema_path: str | Path = DEFAULT_SCHEMA_PATH) -> None:
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    sql_script = schema_path.read_text(encoding="utf-8")
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(sql_script)
        _run_migrations(conn)
        conn.commit()


if __name__ == "__main__":
    init_database()
    print(f"Local database initialized: {DEFAULT_DB_PATH}")
