import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR.parent.parent / "db" / "server.db"
DEFAULT_SCHEMA_PATH = BASE_DIR / "database_init.sql"


def init_database(db_path: str | Path = DEFAULT_DB_PATH, schema_path: str | Path = DEFAULT_SCHEMA_PATH) -> None:
    """Initialize server mirror SQLite database by executing the schema SQL file."""
    db_path = Path(db_path)
    schema_path = Path(schema_path)

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    sql_script = schema_path.read_text(encoding="utf-8")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(sql_script)
        conn.commit()


if __name__ == "__main__":
    init_database()
    print(f"Server database initialized: {DEFAULT_DB_PATH}")
