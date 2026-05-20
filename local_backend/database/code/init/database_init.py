import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR.parent.parent / "db" / "local.db"
DEFAULT_SCHEMA_PATH = BASE_DIR / "database_init.sql"
DEFAULT_SCHEMA_V2_PATH = BASE_DIR / "database_init_v2.sql"

MIGRATIONS = [
    {
        "check": "SELECT COUNT(*) FROM pragma_table_info('data') WHERE name='data_linked_schedule_id'",
        "sql": "ALTER TABLE data ADD COLUMN data_linked_schedule_id INTEGER",
    },
]

DATA_TABLE_SQL_V4 = """CREATE TABLE IF NOT EXISTS data (
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
)"""


def _run_migrations(conn: sqlite3.Connection) -> None:
    for migration in MIGRATIONS:
        check_result = conn.execute(migration["check"]).fetchone()
        if check_result[0] == 0:
            conn.execute(migration["sql"])

    check_old_check = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='data' AND sql LIKE '%CHECK (data_classification_code IN (1, 2, 3))%'"
    ).fetchone()
    if check_old_check[0] > 0:
        conn.execute("PRAGMA foreign_keys = OFF;")
        conn.execute("ALTER TABLE data RENAME TO data_old;")
        conn.execute(DATA_TABLE_SQL_V4)
        conn.execute(
            """INSERT INTO data (
                data_id, user_id, data_category_id, data_content_type, data_classification_code,
                data_title, data_content_text, data_link_url, data_release_time, data_ddl_time,
                data_is_previewable, data_source, data_external_id, data_term, data_week,
                data_weekday, data_period_start, data_period_end, data_start_time, data_end_time,
                data_meta_json, data_raw_json, data_updated_at, data_created_at, data_linked_schedule_id
            ) SELECT
                data_id, user_id, data_category_id, data_content_type, data_classification_code,
                data_title, data_content_text, data_link_url, data_release_time, data_ddl_time,
                data_is_previewable, data_source, data_external_id, data_term, data_week,
                data_weekday, data_period_start, data_period_end, data_start_time, data_end_time,
                data_meta_json, data_raw_json, data_updated_at, data_created_at, data_linked_schedule_id
            FROM data_old"""
        )
        conn.execute("DROP TABLE data_old;")
        conn.execute("PRAGMA foreign_keys = ON;")


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

    v2_path = Path(DEFAULT_SCHEMA_V2_PATH)
    if v2_path.exists():
        v2_script = v2_path.read_text(encoding="utf-8")
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.executescript(v2_script)
            conn.commit()


if __name__ == "__main__":
    init_database()
    print(f"Local database initialized: {DEFAULT_DB_PATH}")
