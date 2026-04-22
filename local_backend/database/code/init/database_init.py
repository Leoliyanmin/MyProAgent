import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR.parent.parent / "db" / "local.db"
DEFAULT_SCHEMA_PATH = BASE_DIR / "database_init.sql"

MIGRATIONS = [
    {
        "check": "SELECT COUNT(*) FROM pragma_table_info('data') WHERE name='data_linked_schedule_id'",
        "sql": "ALTER TABLE data ADD COLUMN data_linked_schedule_id INTEGER",
    },
]


def _run_migrations(conn: sqlite3.Connection) -> None:
    for migration in MIGRATIONS:
        check_result = conn.execute(migration["check"]).fetchone()
        if check_result[0] == 0:
            conn.execute(migration["sql"])


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
