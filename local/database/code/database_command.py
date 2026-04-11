import sqlite3
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR.parent / "db" / "local.db"
SQLITE_BUSY_TIMEOUT_MS = 5000
SQLITE_RETRY_COUNT = 5
SQLITE_RETRY_DELAY_SEC = 0.05


def _connect(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=SQLITE_BUSY_TIMEOUT_MS / 1000)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS};")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _is_locked_error(exc: sqlite3.OperationalError) -> bool:
    message = str(exc).lower()
    return "database is locked" in message or "database table is locked" in message


def _execute(sql: str, params: tuple = (), db_path: str | Path = DEFAULT_DB_PATH) -> int:
    for attempt in range(SQLITE_RETRY_COUNT + 1):
        try:
            with _connect(db_path) as conn:
                cursor = conn.execute(sql, params)
                conn.commit()
                return cursor.lastrowid
        except sqlite3.OperationalError as exc:
            if not _is_locked_error(exc) or attempt == SQLITE_RETRY_COUNT:
                raise
            time.sleep(SQLITE_RETRY_DELAY_SEC * (attempt + 1))
    raise RuntimeError("unreachable")


def _fetch_one(sql: str, params: tuple = (), db_path: str | Path = DEFAULT_DB_PATH) -> dict | None:
    for attempt in range(SQLITE_RETRY_COUNT + 1):
        try:
            with _connect(db_path) as conn:
                row = conn.execute(sql, params).fetchone()
                return dict(row) if row else None
        except sqlite3.OperationalError as exc:
            if not _is_locked_error(exc) or attempt == SQLITE_RETRY_COUNT:
                raise
            time.sleep(SQLITE_RETRY_DELAY_SEC * (attempt + 1))
    raise RuntimeError("unreachable")


def _fetch_all(sql: str, params: tuple = (), db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    for attempt in range(SQLITE_RETRY_COUNT + 1):
        try:
            with _connect(db_path) as conn:
                rows = conn.execute(sql, params).fetchall()
                return [dict(r) for r in rows]
        except sqlite3.OperationalError as exc:
            if not _is_locked_error(exc) or attempt == SQLITE_RETRY_COUNT:
                raise
            time.sleep(SQLITE_RETRY_DELAY_SEC * (attempt + 1))
    raise RuntimeError("unreachable")


# users

def upsert_user(
    user_id: str,
    username: str,
    user_email: str,
    user_is_active: int,
    user_created_at: str,
    user_last_login: str | None,
    user_source_device_id: str | None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    _execute(
        """
        INSERT INTO users (
            user_id, username, user_email, user_is_active, user_created_at,
            user_last_login, user_source_device_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            user_email = excluded.user_email,
            user_is_active = excluded.user_is_active,
            user_created_at = excluded.user_created_at,
            user_last_login = excluded.user_last_login,
            user_source_device_id = excluded.user_source_device_id
        """,
        (
            user_id,
            username,
            user_email,
            user_is_active,
            user_created_at,
            user_last_login,
            user_source_device_id,
        ),
        db_path,
    )


def get_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> dict | None:
    return _fetch_one("SELECT * FROM users WHERE user_id = ?", (user_id,), db_path)


def list_users(db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM users ORDER BY user_created_at DESC", (), db_path)


def delete_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM users WHERE user_id = ?", (user_id,), db_path)


# user_match_profile

def upsert_user_match_profile(
    user_id: str,
    answers: str,
    is_open: int = 0,
    last_match_time: str | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    _execute(
        """
        INSERT INTO user_match_profile (user_id, answers, is_open, last_match_time)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            answers = excluded.answers,
            is_open = excluded.is_open,
            last_match_time = excluded.last_match_time
        """,
        (user_id, answers, is_open, last_match_time),
        db_path,
    )


def get_user_match_profile(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> dict | None:
    return _fetch_one("SELECT * FROM user_match_profile WHERE user_id = ?", (user_id,), db_path)


def list_user_match_profiles(db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM user_match_profile ORDER BY user_id ASC", (), db_path)


def list_open_user_match_profiles(
    exclude_user_id: str | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> list[dict]:
    if exclude_user_id is None:
        return _fetch_all(
            """
            SELECT * FROM user_match_profile
            WHERE is_open = 1
            ORDER BY COALESCE(last_match_time, '') ASC, user_id ASC
            """,
            (),
            db_path,
        )

    return _fetch_all(
        """
        SELECT * FROM user_match_profile
        WHERE is_open = 1 AND user_id <> ?
        ORDER BY COALESCE(last_match_time, '') ASC, user_id ASC
        """,
        (exclude_user_id,),
        db_path,
    )


def update_user_match_profile_open(
    user_id: str,
    is_open: int,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    _execute(
        "UPDATE user_match_profile SET is_open = ? WHERE user_id = ?",
        (is_open, user_id),
        db_path,
    )


def update_user_match_profile_last_match_time(
    user_id: str,
    last_match_time: str | None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    _execute(
        "UPDATE user_match_profile SET last_match_time = ? WHERE user_id = ?",
        (last_match_time, user_id),
        db_path,
    )


def delete_user_match_profile(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM user_match_profile WHERE user_id = ?", (user_id,), db_path)


# match_result

def create_match_result(
    user_id: str,
    matched_user_id: str,
    similarity_score: float,
    created_at: str,
    is_shared: int,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    return _execute(
        """
        INSERT INTO match_result (
            user_id, matched_user_id, similarity_score, created_at, is_shared
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, matched_user_id, similarity_score, created_at, is_shared),
        db_path,
    )


def list_match_results_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all(
        "SELECT * FROM match_result WHERE user_id = ? ORDER BY created_at DESC, id DESC",
        (user_id,),
        db_path,
    )


def list_match_results_between_users(
    user_a_id: str,
    user_b_id: str,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> list[dict]:
    return _fetch_all(
        """
        SELECT * FROM match_result
        WHERE (user_id = ? AND matched_user_id = ?)
           OR (user_id = ? AND matched_user_id = ?)
        ORDER BY created_at DESC, id DESC
        """,
        (user_a_id, user_b_id, user_b_id, user_a_id),
        db_path,
    )


def list_matched_user_ids(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> list[str]:
    rows = _fetch_all(
        """
        SELECT DISTINCT
            CASE
                WHEN user_id = ? THEN matched_user_id
                ELSE user_id
            END AS matched_user_id
        FROM match_result
        WHERE user_id = ? OR matched_user_id = ?
        ORDER BY matched_user_id ASC
        """,
        (user_id, user_id, user_id),
        db_path,
    )
    return [str(row["matched_user_id"]) for row in rows if row.get("matched_user_id") is not None]


def list_unshared_match_results_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all(
        "SELECT * FROM match_result WHERE user_id = ? AND is_shared = 0 ORDER BY created_at DESC, id DESC",
        (user_id,),
        db_path,
    )


def list_match_results_by_matched_user(matched_user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all(
        "SELECT * FROM match_result WHERE matched_user_id = ? ORDER BY created_at DESC, id DESC",
        (matched_user_id,),
        db_path,
    )


def list_unshared_match_results_by_matched_user(
    matched_user_id: str,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> list[dict]:
    return _fetch_all(
        "SELECT * FROM match_result WHERE matched_user_id = ? AND is_shared = 0 ORDER BY created_at DESC, id DESC",
        (matched_user_id,),
        db_path,
    )


def update_match_result_shared(
    result_id: int,
    is_shared: int,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    _execute(
        "UPDATE match_result SET is_shared = ? WHERE id = ?",
        (is_shared, result_id),
        db_path,
    )


def update_match_result_shared_by_users(
    user_id: str,
    matched_user_id: str,
    is_shared: int,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    _execute(
        "UPDATE match_result SET is_shared = ? WHERE user_id = ? AND matched_user_id = ?",
        (is_shared, user_id, matched_user_id),
        db_path,
    )


def delete_match_result(result_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM match_result WHERE id = ?", (result_id,), db_path)


def delete_match_results_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM match_result WHERE user_id = ?", (user_id,), db_path)


def delete_match_results_by_matched_user(matched_user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM match_result WHERE matched_user_id = ?", (matched_user_id,), db_path)


# sync_state

def upsert_sync_state(
    user_id: str,
    user_data_updated_at: str,
    user_last_synced_at: str | None,
    user_version: int,
    sync_updated_at: str,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    _execute(
        """
        INSERT INTO sync_state (
            user_id, user_data_updated_at, user_last_synced_at, user_version, sync_updated_at
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            user_data_updated_at = excluded.user_data_updated_at,
            user_last_synced_at = excluded.user_last_synced_at,
            user_version = excluded.user_version,
            sync_updated_at = excluded.sync_updated_at
        """,
        (user_id, user_data_updated_at, user_last_synced_at, user_version, sync_updated_at),
        db_path,
    )


def get_sync_state(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> dict | None:
    return _fetch_one("SELECT * FROM sync_state WHERE user_id = ?", (user_id,), db_path)


def list_sync_states(db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM sync_state ORDER BY sync_updated_at DESC", (), db_path)


def delete_sync_state(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM sync_state WHERE user_id = ?", (user_id,), db_path)


# account

def create_account(
    user_id: str,
    account_platform_type: str,
    account_platform_username: str,
    account_bind_time: str | None,
    account_last_sync_time: str | None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    return _execute(
        """
        INSERT INTO account (
            user_id, account_platform_type, account_platform_username,
            account_bind_time, account_last_sync_time
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            account_platform_type,
            account_platform_username,
            account_bind_time,
            account_last_sync_time,
        ),
        db_path,
    )


def list_accounts_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM account WHERE user_id = ? ORDER BY account_id DESC", (user_id,), db_path)


def update_account_sync_time(account_id: int, account_last_sync_time: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute(
        "UPDATE account SET account_last_sync_time = ? WHERE account_id = ?",
        (account_last_sync_time, account_id),
        db_path,
    )


def delete_account(account_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM account WHERE account_id = ?", (account_id,), db_path)


# category

def create_category(
    user_id: str,
    category_kind: str,
    category_title: str,
    category_content: str | None,
    category_link: str | None,
    category_created_at: str,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    return _execute(
        """
        INSERT INTO category (
            user_id, category_kind, category_title, category_content,
            category_link, category_created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, category_kind, category_title, category_content, category_link, category_created_at),
        db_path,
    )


def list_categories_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM category WHERE user_id = ? ORDER BY category_id DESC", (user_id,), db_path)


def update_category(
    category_id: int,
    category_kind: str,
    category_title: str,
    category_content: str | None,
    category_link: str | None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    _execute(
        """
        UPDATE category
        SET category_kind = ?, category_title = ?, category_content = ?, category_link = ?
        WHERE category_id = ?
        """,
        (category_kind, category_title, category_content, category_link, category_id),
        db_path,
    )


def delete_category(category_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM category WHERE category_id = ?", (category_id,), db_path)


# data

def create_data(
    user_id: str,
    data_category_id: int,
    data_content_type: str,
    data_title: str,
    data_content_text: str | None,
    data_link_url: str | None,
    data_release_time: str | None,
    data_ddl_time: str | None,
    data_is_previewable: int,
    data_created_at: str,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    return _execute(
        """
        INSERT INTO data (
            user_id, data_category_id, data_content_type, data_title,
            data_content_text, data_link_url, data_release_time,
            data_ddl_time, data_is_previewable, data_created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            data_category_id,
            data_content_type,
            data_title,
            data_content_text,
            data_link_url,
            data_release_time,
            data_ddl_time,
            data_is_previewable,
            data_created_at,
        ),
        db_path,
    )


def list_data_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM data WHERE user_id = ? ORDER BY data_id DESC", (user_id,), db_path)


def update_data(
    data_id: int,
    data_title: str,
    data_content_text: str | None,
    data_link_url: str | None,
    data_release_time: str | None,
    data_ddl_time: str | None,
    data_is_previewable: int,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    _execute(
        """
        UPDATE data
        SET data_title = ?, data_content_text = ?, data_link_url = ?,
            data_release_time = ?, data_ddl_time = ?, data_is_previewable = ?
        WHERE data_id = ?
        """,
        (
            data_title,
            data_content_text,
            data_link_url,
            data_release_time,
            data_ddl_time,
            data_is_previewable,
            data_id,
        ),
        db_path,
    )


def delete_data(data_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM data WHERE data_id = ?", (data_id,), db_path)


# schedule

def create_schedule(
    user_id: str,
    schedule_event_type: str,
    schedule_title: str,
    schedule_start_time: str,
    schedule_end_time: str,
    schedule_location: str | None,
    schedule_description: str | None,
    schedule_related_link: str | None,
    schedule_recurrence_rule: str | None,
    schedule_color_tag: str | None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    return _execute(
        """
        INSERT INTO schedule (
            user_id, schedule_event_type, schedule_title, schedule_start_time,
            schedule_end_time, schedule_location, schedule_description,
            schedule_related_link, schedule_recurrence_rule, schedule_color_tag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            schedule_event_type,
            schedule_title,
            schedule_start_time,
            schedule_end_time,
            schedule_location,
            schedule_description,
            schedule_related_link,
            schedule_recurrence_rule,
            schedule_color_tag,
        ),
        db_path,
    )


def list_schedule_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM schedule WHERE user_id = ? ORDER BY schedule_start_time ASC", (user_id,), db_path)


def update_schedule(
    schedule_id: int,
    schedule_title: str,
    schedule_start_time: str,
    schedule_end_time: str,
    schedule_location: str | None,
    schedule_description: str | None,
    schedule_related_link: str | None,
    schedule_recurrence_rule: str | None,
    schedule_color_tag: str | None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    _execute(
        """
        UPDATE schedule
        SET schedule_title = ?, schedule_start_time = ?, schedule_end_time = ?,
            schedule_location = ?, schedule_description = ?, schedule_related_link = ?,
            schedule_recurrence_rule = ?, schedule_color_tag = ?
        WHERE schedule_id = ?
        """,
        (
            schedule_title,
            schedule_start_time,
            schedule_end_time,
            schedule_location,
            schedule_description,
            schedule_related_link,
            schedule_recurrence_rule,
            schedule_color_tag,
            schedule_id,
        ),
        db_path,
    )


def delete_schedule(schedule_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM schedule WHERE schedule_id = ?", (schedule_id,), db_path)


# session

def create_session(user_id: str, session_last_visited_at: str, db_path: str | Path = DEFAULT_DB_PATH) -> int:
    return _execute(
        "INSERT INTO session (user_id, session_last_visited_at) VALUES (?, ?)",
        (user_id, session_last_visited_at),
        db_path,
    )


def list_sessions_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM session WHERE user_id = ? ORDER BY session_id DESC", (user_id,), db_path)


def update_session_last_visited(session_id: int, session_last_visited_at: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute(
        "UPDATE session SET session_last_visited_at = ? WHERE session_id = ?",
        (session_last_visited_at, session_id),
        db_path,
    )


def delete_session(session_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM session WHERE session_id = ?", (session_id,), db_path)


# chat

def create_chat(
    session_id: int,
    chat_role: str,
    chat_message_content: str,
    thought_trace: str | None,
    chat_tool_calls: str | None,
    chat_tokens_usage: str | None,
    chat_created_at: str,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    return _execute(
        """
        INSERT INTO chat (
            session_id, chat_role, chat_message_content, thought_trace,
            chat_tool_calls, chat_tokens_usage, chat_created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            chat_role,
            chat_message_content,
            thought_trace,
            chat_tool_calls,
            chat_tokens_usage,
            chat_created_at,
        ),
        db_path,
    )


def list_chat_by_session(session_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM chat WHERE session_id = ? ORDER BY chat_id ASC", (session_id,), db_path)


def update_chat_trace(
    chat_id: int,
    thought_trace: str | None,
    chat_tool_calls: str | None,
    chat_tokens_usage: str | None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    _execute(
        """
        UPDATE chat
        SET thought_trace = ?, chat_tool_calls = ?, chat_tokens_usage = ?
        WHERE chat_id = ?
        """,
        (thought_trace, chat_tool_calls, chat_tokens_usage, chat_id),
        db_path,
    )


def delete_chat(chat_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM chat WHERE chat_id = ?", (chat_id,), db_path)
