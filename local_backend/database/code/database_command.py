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


# personal_information

def upsert_personal_information(
    user_id: str,
    personal_information_json: str,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    _execute(
        """
        INSERT INTO personal_information (user_id, personal_information_json)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            personal_information_json = excluded.personal_information_json
        """,
        (user_id, personal_information_json),
        db_path,
    )


def get_personal_information(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> dict | None:
    return _fetch_one("SELECT * FROM personal_information WHERE user_id = ?", (user_id,), db_path)


def list_personal_information(db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM personal_information ORDER BY user_id ASC", (), db_path)


def delete_personal_information(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM personal_information WHERE user_id = ?", (user_id,), db_path)


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


def list_accounts(db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM account ORDER BY account_id DESC", (), db_path)


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


def list_categories(db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM category ORDER BY category_id DESC", (), db_path)


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


def list_data(db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM data ORDER BY data_id DESC", (), db_path)


def list_data_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM data WHERE user_id = ? ORDER BY data_id DESC", (user_id,), db_path)


def get_data(data_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> dict | None:
    return _fetch_one("SELECT * FROM data WHERE data_id = ?", (data_id,), db_path)


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


def list_schedule(db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM schedule ORDER BY schedule_id DESC", (), db_path)


def list_schedule_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM schedule WHERE user_id = ? ORDER BY schedule_id DESC", (user_id,), db_path)


def get_schedule(schedule_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> dict | None:
    return _fetch_one("SELECT * FROM schedule WHERE schedule_id = ?", (schedule_id,), db_path)


def update_schedule(
    schedule_id: int,
    schedule_title: str = None,
    schedule_start_time: str = None,
    schedule_end_time: str = None,
    schedule_location: str | None = None,
    schedule_description: str | None = None,
    schedule_related_link: str | None = None,
    schedule_recurrence_rule: str | None = None,
    schedule_color_tag: str | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    # 构建动态更新语句
    update_fields = []
    params = []
    
    if schedule_title is not None:
        update_fields.append("schedule_title = ?")
        params.append(schedule_title)
    if schedule_start_time is not None:
        update_fields.append("schedule_start_time = ?")
        params.append(schedule_start_time)
    if schedule_end_time is not None:
        update_fields.append("schedule_end_time = ?")
        params.append(schedule_end_time)
    if schedule_location is not None:
        update_fields.append("schedule_location = ?")
        params.append(schedule_location)
    if schedule_description is not None:
        update_fields.append("schedule_description = ?")
        params.append(schedule_description)
    if schedule_related_link is not None:
        update_fields.append("schedule_related_link = ?")
        params.append(schedule_related_link)
    if schedule_recurrence_rule is not None:
        update_fields.append("schedule_recurrence_rule = ?")
        params.append(schedule_recurrence_rule)
    if schedule_color_tag is not None:
        update_fields.append("schedule_color_tag = ?")
        params.append(schedule_color_tag)
    
    if not update_fields:
        return  # 没有更新字段
    
    params.append(schedule_id)
    query = f"UPDATE schedule SET {', '.join(update_fields)} WHERE schedule_id = ?"
    _execute(query, tuple(params), db_path)


def delete_schedule(schedule_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM schedule WHERE schedule_id = ?", (schedule_id,), db_path)


# session

def create_session(user_id: str, session_last_visited_at: str, db_path: str | Path = DEFAULT_DB_PATH) -> int:
    return _execute(
        "INSERT INTO session (user_id, session_last_visited_at) VALUES (?, ?)",
        (user_id, session_last_visited_at),
        db_path,
    )


def list_sessions(db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM session ORDER BY session_id DESC", (), db_path)


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
