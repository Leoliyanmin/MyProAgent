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
