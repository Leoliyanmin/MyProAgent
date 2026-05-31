from typing import List, Optional

from local_backend.database.code.command.database_command import (
    DEFAULT_DB_PATH,
    _fetch_all,
    _execute,
)


def insert_quote_history(user_id: str, quote_text: str, source: str = "custom",
                          quote_author: str = "", quote_from: str = "",
                          db_path=DEFAULT_DB_PATH) -> None:
    import datetime
    now = datetime.datetime.utcnow().isoformat()
    _execute(
        """INSERT INTO daily_quote_history (user_id, quote_text, quote_author, quote_from, source, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, quote_text, quote_author, quote_from, source, now),
        db_path,
    )


def get_today_history(user_id: str, db_path=DEFAULT_DB_PATH) -> List[dict]:
    import datetime
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    return _fetch_all(
        """SELECT id, quote_text, quote_author, quote_from, source, created_at
           FROM daily_quote_history
           WHERE user_id = ? AND created_at >= ?
           ORDER BY created_at DESC""",
        (user_id, today),
        db_path,
    )
