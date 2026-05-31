import sqlite3
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR.parent.parent / "db" / "local.db"
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


def set_user_password(user_id: str, password_hash: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute(
        "UPDATE users SET password_hash = ? WHERE user_id = ?",
        (password_hash, user_id),
        db_path,
    )


# task

def create_task(
    user_id: str,
    title: str,
    description: str | None = None,
    priority: int = 2,
    status: str = "pending",
    due_date: str | None = None,
    linked_schedule_id: int | None = None,
    source: str = "manual",
    created_at: str | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    import datetime
    now = created_at or datetime.datetime.utcnow().isoformat()
    return _execute(
        """INSERT INTO task (user_id, title, description, priority, status,
           due_date, linked_schedule_id, source, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, title, description, priority, status, due_date, linked_schedule_id, source, now),
        db_path,
    )


def update_task(task_id: int, db_path: str | Path = DEFAULT_DB_PATH, **kwargs) -> None:
    if not kwargs:
        return
    allowed = {"title", "description", "priority", "status", "due_date", "linked_schedule_id", "updated_at"}
    fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [task_id]
    _execute(f"UPDATE task SET {set_clause} WHERE task_id = ?", tuple(values), db_path)


def delete_task(task_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM task WHERE task_id = ?", (task_id,), db_path)


# user_setting

def get_user_setting(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> dict | None:
    return _fetch_one("SELECT * FROM user_setting WHERE user_id = ?", (user_id,), db_path)


def upsert_user_setting(user_id: str, db_path: str | Path = DEFAULT_DB_PATH, **kwargs) -> None:
    existing = get_user_setting(user_id, db_path)
    import datetime
    now = datetime.datetime.utcnow().isoformat()
    if existing:
        allowed = {"avatar_url", "bio", "current_focus", "work_preference",
                   "skills", "theme_config", "notification_enabled", "privacy_share_data",
                   "full_name", "daily_quote"}
        fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not fields:
            return
        fields["updated_at"] = now
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [user_id]
        _execute(f"UPDATE user_setting SET {set_clause} WHERE user_id = ?", tuple(values), db_path)
    else:
        _execute(
            """INSERT INTO user_setting (user_id, avatar_url, bio, current_focus,
               work_preference, skills, theme_config, daily_quote, notification_enabled,
               privacy_share_data, full_name, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, kwargs.get("avatar_url"), kwargs.get("bio"),
             kwargs.get("current_focus"), kwargs.get("work_preference"),
             kwargs.get("skills"), kwargs.get("theme_config"),
             kwargs.get("daily_quote"),
             kwargs.get("notification_enabled", 1), kwargs.get("privacy_share_data", 0),
             kwargs.get("full_name"), now),
            db_path,
        )


# email_account

def create_email_account(
    user_id: str,
    email_address: str,
    encrypted_password: str,
    bind_time: str | None = None,
    last_sync_time: str | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    import datetime
    now = datetime.datetime.utcnow().isoformat()
    return _execute(
        """INSERT INTO email_account (user_id, email_address, encrypted_password,
           bind_time, last_sync_time)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, email_address, encrypted_password, bind_time or now, last_sync_time),
        db_path,
    )


def get_email_account(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> dict | None:
    return _fetch_one("SELECT * FROM email_account WHERE user_id = ?", (user_id,), db_path)


def update_email_account_sync_time(account_id: int, sync_time: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("UPDATE email_account SET last_sync_time = ? WHERE account_id = ?", (sync_time, account_id), db_path)


def update_email_account_sync_uid(account_id: int, last_uid: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("UPDATE email_account SET last_sync_uid = ? WHERE account_id = ?", (last_uid, account_id), db_path)


def delete_email_account(account_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM email_account WHERE account_id = ?", (account_id,), db_path)


# email_message

def create_email_message(
    user_id: str,
    account_id: int,
    mail_uid: str,
    subject: str,
    sender: str,
    recipients: str | None = None,
    body_text: str | None = None,
    body_html: str | None = None,
    received_at: str | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    import datetime
    now = datetime.datetime.utcnow().isoformat()
    return _execute(
        """INSERT INTO email_message (user_id, account_id, mail_uid, subject,
           sender, recipients, body_text, body_html, received_at, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, account_id, mail_uid, subject, sender, recipients, body_text, body_html, received_at, now),
        db_path,
    )


def list_email_messages_by_user(user_id: str, status: int = 0, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all(
        "SELECT * FROM email_message WHERE user_id = ? AND status = ? ORDER BY received_at DESC",
        (user_id, status), db_path,
    )


def delete_email_message(message_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("UPDATE email_message SET status = 1 WHERE message_id = ?", (message_id,), db_path)


def restore_email_message(message_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("UPDATE email_message SET status = 0 WHERE message_id = ?", (message_id,), db_path)


def permanent_delete_email_message(message_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("UPDATE email_message SET status = 2 WHERE message_id = ?", (message_id,), db_path)


def delete_email_messages_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM email_message WHERE user_id = ?", (user_id,), db_path)


def delete_starred_emails_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM starred_emails WHERE user_id = ?", (user_id,), db_path)


def create_starred_email(user_id, email_id, reason=None, source='manual', starred_at=None, db_path=DEFAULT_DB_PATH):
    import datetime
    if not starred_at:
        starred_at = datetime.datetime.utcnow().isoformat()
    return _execute(
        """INSERT INTO starred_emails (user_id, email_id, reason, source, starred_at)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, email_id, reason, source, starred_at), db_path
    )


def list_starred_emails_by_user(user_id, db_path=DEFAULT_DB_PATH):
    return _fetch_all(
        "SELECT * FROM starred_emails WHERE user_id = ? ORDER BY source = 'ai' DESC, starred_at DESC",
        (user_id,), db_path
    )


def get_starred_email(user_id, email_id, db_path=DEFAULT_DB_PATH):
    rows = _fetch_all(
        "SELECT * FROM starred_emails WHERE user_id = ? AND email_id = ? LIMIT 1",
        (user_id, email_id), db_path
    )
    return rows[0] if rows else None


def delete_starred_email(user_id, email_id, db_path=DEFAULT_DB_PATH):
    _execute(
        "DELETE FROM starred_emails WHERE user_id = ? AND email_id = ?",
        (user_id, email_id), db_path
    )


def delete_starred_emails_by_email_id(email_id, db_path=DEFAULT_DB_PATH):
    _execute(
        "DELETE FROM starred_emails WHERE email_id = ?",
        (email_id,), db_path
    )


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
    content: str | None = None,
    account_bind_time: str | None = None,
    account_last_sync_time: str | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    return _execute(
        """
        INSERT INTO account (
            user_id, account_platform_type, account_platform_username,
            content, account_bind_time, account_last_sync_time
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            account_platform_type,
            account_platform_username,
            content,
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
    category_source: str | None = None,
    category_external_id: str | None = None,
    category_term: str | None = None,
    category_meta_json: str | None = None,
    category_updated_at: str | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    return _execute(
        """
        INSERT INTO category (
            user_id, category_kind, category_title, category_content,
            category_link, category_source, category_external_id,
            category_term, category_meta_json, category_updated_at,
            category_created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            category_kind,
            category_title,
            category_content,
            category_link,
            category_source,
            category_external_id,
            category_term,
            category_meta_json,
            category_updated_at,
            category_created_at,
        ),
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
    category_source: str | None = None,
    category_external_id: str | None = None,
    category_term: str | None = None,
    category_meta_json: str | None = None,
    category_updated_at: str | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    update_fields = [
        "category_kind = ?",
        "category_title = ?",
        "category_content = ?",
        "category_link = ?",
    ]
    params: list[object] = [category_kind, category_title, category_content, category_link]

    if category_source is not None:
        update_fields.append("category_source = ?")
        params.append(category_source)
    if category_external_id is not None:
        update_fields.append("category_external_id = ?")
        params.append(category_external_id)
    if category_term is not None:
        update_fields.append("category_term = ?")
        params.append(category_term)
    if category_meta_json is not None:
        update_fields.append("category_meta_json = ?")
        params.append(category_meta_json)
    if category_updated_at is not None:
        update_fields.append("category_updated_at = ?")
        params.append(category_updated_at)

    params.append(category_id)
    _execute(
        f"UPDATE category SET {', '.join(update_fields)} WHERE category_id = ?",
        tuple(params),
        db_path,
    )


def delete_category(category_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM category WHERE category_id = ?", (category_id,), db_path)


# data

def create_data(
    user_id: str,
    data_category_id: int,
    data_content_type: str,
    data_classification_code: int,
    data_title: str,
    data_content_text: str | None,
    data_link_url: str | None,
    data_release_time: str | None,
    data_ddl_time: str | None,
    data_is_previewable: int,
    data_created_at: str,
    data_source: str | None = None,
    data_external_id: str | None = None,
    data_term: str | None = None,
    data_week: str | None = None,
    data_weekday: int | None = None,
    data_period_start: int | None = None,
    data_period_end: int | None = None,
    data_start_time: str | None = None,
    data_end_time: str | None = None,
    data_meta_json: str | None = None,
    data_raw_json: str | None = None,
    data_updated_at: str | None = None,
    data_linked_schedule_id: int | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    return _execute(
        """
        INSERT INTO data (
            user_id, data_category_id, data_content_type, data_classification_code, data_title,
            data_content_text, data_link_url, data_release_time,
            data_ddl_time, data_is_previewable, data_source, data_external_id,
            data_term, data_week, data_weekday, data_period_start, data_period_end,
            data_start_time, data_end_time, data_meta_json, data_raw_json,
            data_updated_at, data_created_at, data_linked_schedule_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            data_category_id,
            data_content_type,
            data_classification_code,
            data_title,
            data_content_text,
            data_link_url,
            data_release_time,
            data_ddl_time,
            data_is_previewable,
            data_source,
            data_external_id,
            data_term,
            data_week,
            data_weekday,
            data_period_start,
            data_period_end,
            data_start_time,
            data_end_time,
            data_meta_json,
            data_raw_json,
            data_updated_at,
            data_created_at,
            data_linked_schedule_id,
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
    data_title: str | None = None,
    data_content_text: str | None = None,
    data_link_url: str | None = None,
    data_release_time: str | None = None,
    data_ddl_time: str | None = None,
    data_is_previewable: int | None = None,
    data_classification_code: int | None = None,
    data_source: str | None = None,
    data_external_id: str | None = None,
    data_term: str | None = None,
    data_week: str | None = None,
    data_weekday: int | None = None,
    data_period_start: int | None = None,
    data_period_end: int | None = None,
    data_start_time: str | None = None,
    data_end_time: str | None = None,
    data_meta_json: str | None = None,
    data_raw_json: str | None = None,
    data_updated_at: str | None = None,
    data_linked_schedule_id: int | None | object = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    update_fields = []
    params = []

    if data_title is not None:
        update_fields.append("data_title = ?")
        params.append(data_title)
    if data_content_text is not None:
        update_fields.append("data_content_text = ?")
        params.append(data_content_text)
    if data_link_url is not None:
        update_fields.append("data_link_url = ?")
        params.append(data_link_url)
    if data_release_time is not None:
        update_fields.append("data_release_time = ?")
        params.append(data_release_time)
    if data_ddl_time is not None:
        update_fields.append("data_ddl_time = ?")
        params.append(data_ddl_time)
    if data_is_previewable is not None:
        update_fields.append("data_is_previewable = ?")
        params.append(data_is_previewable)
    if data_classification_code is not None:
        update_fields.append("data_classification_code = ?")
        params.append(data_classification_code)
    if data_source is not None:
        update_fields.append("data_source = ?")
        params.append(data_source)
    if data_external_id is not None:
        update_fields.append("data_external_id = ?")
        params.append(data_external_id)
    if data_term is not None:
        update_fields.append("data_term = ?")
        params.append(data_term)
    if data_week is not None:
        update_fields.append("data_week = ?")
        params.append(data_week)
    if data_weekday is not None:
        update_fields.append("data_weekday = ?")
        params.append(data_weekday)
    if data_period_start is not None:
        update_fields.append("data_period_start = ?")
        params.append(data_period_start)
    if data_period_end is not None:
        update_fields.append("data_period_end = ?")
        params.append(data_period_end)
    if data_start_time is not None:
        update_fields.append("data_start_time = ?")
        params.append(data_start_time)
    if data_end_time is not None:
        update_fields.append("data_end_time = ?")
        params.append(data_end_time)
    if data_meta_json is not None:
        update_fields.append("data_meta_json = ?")
        params.append(data_meta_json)
    if data_raw_json is not None:
        update_fields.append("data_raw_json = ?")
        params.append(data_raw_json)
    if data_updated_at is not None:
        update_fields.append("data_updated_at = ?")
        params.append(data_updated_at)
    if data_linked_schedule_id is not None:
        if isinstance(data_linked_schedule_id, int) or data_linked_schedule_id == 0:
            update_fields.append("data_linked_schedule_id = ?")
            params.append(data_linked_schedule_id if data_linked_schedule_id != 0 else None)

    if not update_fields:
        return

    params.append(data_id)
    query = f"UPDATE data SET {', '.join(update_fields)} WHERE data_id = ?"
    _execute(query, tuple(params), db_path)


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
    schedule_priority: int = 2,
    schedule_is_completed: int = 0,
) -> int:
    return _execute(
        """
        INSERT INTO schedule (
            user_id, schedule_event_type, schedule_priority, schedule_is_completed, schedule_title, schedule_start_time,
            schedule_end_time, schedule_location, schedule_description,
            schedule_related_link, schedule_recurrence_rule, schedule_color_tag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            schedule_event_type,
            schedule_priority,
            schedule_is_completed,
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
    schedule_priority: int | None = None,
    schedule_is_completed: int | None = None,
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
    if schedule_priority is not None:
        update_fields.append("schedule_priority = ?")
        params.append(schedule_priority)
    if schedule_is_completed is not None:
        update_fields.append("schedule_is_completed = ?")
        params.append(schedule_is_completed)
    
    if not update_fields:
        return  # 没有更新字段
    
    params.append(schedule_id)
    query = f"UPDATE schedule SET {', '.join(update_fields)} WHERE schedule_id = ?"
    _execute(query, tuple(params), db_path)


def delete_schedule(schedule_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM schedule WHERE schedule_id = ?", (schedule_id,), db_path)


# session

def create_session(
    user_id: str,
    session_last_visited_at: str,
    session_title: str = "",
    session_created_at: str | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    if session_created_at is None:
        session_created_at = session_last_visited_at
    return _execute(
        "INSERT INTO session (user_id, session_title, session_created_at, session_last_visited_at) VALUES (?, ?, ?, ?)",
        (user_id, session_title, session_created_at, session_last_visited_at),
        db_path,
    )


def list_sessions(db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM session ORDER BY session_id DESC", (), db_path)


def list_sessions_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM session WHERE user_id = ? ORDER BY session_id DESC", (user_id,), db_path)


def get_session(session_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> dict | None:
    rows = _fetch_all("SELECT * FROM session WHERE session_id = ?", (session_id,), db_path)
    return rows[0] if rows else None


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


# ==================== event ====================

def create_event(
    user_id: str, event_title: str,
    event_type: str = "manual", event_source: str = "manual",
    event_start_time: str | None = None, event_end_time: str | None = None,
    event_location: str | None = None, event_description: str | None = None,
    event_link_url: str | None = None,
    event_is_completed: int = 0, event_show_in_todo: int = 1,
    event_priority: int = 2, event_color_tag: str = "#007aff",
    event_meta_json: str | None = None,
    event_created_at: str | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    import datetime
    now = event_created_at or datetime.datetime.utcnow().isoformat()
    return _execute(
        """INSERT INTO event (user_id, event_title, event_type, event_source,
           event_start_time, event_end_time, event_location, event_description,
           event_link_url, event_is_completed, event_show_in_todo,
           event_priority, event_color_tag, event_meta_json, event_created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, event_title, event_type, event_source,
         event_start_time, event_end_time, event_location, event_description,
         event_link_url, event_is_completed, event_show_in_todo,
         event_priority, event_color_tag, event_meta_json, now),
        db_path,
    )


def list_events_by_user(
    user_id: str,
    event_type: str | None = None,
    event_source: str | None = None,
    show_in_todo: int | None = None,
    completed: int | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> list[dict]:
    conditions = ["user_id = ?"]
    params: list = [user_id]
    if event_type is not None:
        conditions.append("event_type = ?")
        params.append(event_type)
    if event_source is not None:
        conditions.append("event_source = ?")
        params.append(event_source)
    if show_in_todo is not None:
        conditions.append("event_show_in_todo = ?")
        params.append(show_in_todo)
    if completed is not None:
        conditions.append("event_is_completed = ?")
        params.append(completed)
    where = " AND ".join(conditions)
    return _fetch_all(
        f"SELECT * FROM event WHERE {where} ORDER BY event_start_time ASC, event_id DESC",
        tuple(params), db_path,
    )


def get_event(event_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> dict | None:
    return _fetch_one("SELECT * FROM event WHERE event_id = ?", (event_id,), db_path)


def update_event(
    event_id: int,
    event_title: str | None = None,
    event_type: str | None = None,
    event_start_time: str | None = None,
    event_end_time: str | None = None,
    event_location: str | None = None,
    event_description: str | None = None,
    event_link_url: str | None = None,
    event_is_completed: int | None = None,
    event_show_in_todo: int | None = None,
    event_priority: int | None = None,
    event_color_tag: str | None = None,
    event_meta_json: str | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    import datetime
    fields = []
    params: list = []
    mapping = {
        "event_title": event_title, "event_type": event_type,
        "event_start_time": event_start_time, "event_end_time": event_end_time,
        "event_location": event_location, "event_description": event_description,
        "event_link_url": event_link_url, "event_is_completed": event_is_completed,
        "event_show_in_todo": event_show_in_todo, "event_priority": event_priority,
        "event_color_tag": event_color_tag, "event_meta_json": event_meta_json,
    }
    for col, val in mapping.items():
        if val is not None:
            fields.append(f"{col} = ?")
            params.append(val)
    fields.append("event_updated_at = ?")
    params.append(datetime.datetime.utcnow().isoformat())
    params.append(event_id)
    _execute(
        f"UPDATE event SET {', '.join(fields)} WHERE event_id = ?",
        tuple(params), db_path,
    )


def delete_event(event_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM event WHERE event_id = ?", (event_id,), db_path)


# ==================== api_key ====================

def _get_fernet():
    import hashlib
    import base64
    from cryptography.fernet import Fernet
    from local_backend.config import settings
    key = settings.ENCRYPTION_KEY.encode("utf-8")
    derived = base64.urlsafe_b64encode(hashlib.sha256(key).digest())
    return Fernet(derived)


def _encrypt_api(value: str) -> str:
    return _get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def _decrypt_api(encrypted: str) -> str:
    try:
        return _get_fernet().decrypt(encrypted.encode("utf-8")).decode("utf-8")
    except Exception:
        return encrypted


def create_api_key(
    user_id: str,
    key_id: str,
    provider: str,
    api_key_plain: str,
    api_base: str,
    model: str = "",
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    import datetime
    now = datetime.datetime.utcnow().isoformat()
    encrypted = _encrypt_api(api_key_plain)
    return _execute(
        """INSERT INTO api_key (user_id, key_id, provider, api_key_encrypted,
           api_base, model, updated_at, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, key_id, provider, encrypted, api_base, model, now, now),
        db_path,
    )


def list_api_keys_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all(
        "SELECT * FROM api_key WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,), db_path,
    )


def get_api_key(key_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> dict | None:
    return _fetch_one("SELECT * FROM api_key WHERE key_id = ?", (key_id,), db_path)


def update_api_key(
    key_id: str,
    provider: str | None = None,
    api_key_plain: str | None = None,
    api_base: str | None = None,
    model: str | None = None,
    is_active: int | None = None,
    last_test_success: int | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    import datetime
    fields = ["updated_at = ?"]
    params: list = [datetime.datetime.utcnow().isoformat()]
    if provider is not None:
        fields.append("provider = ?"); params.append(provider)
    if api_key_plain is not None:
        fields.append("api_key_encrypted = ?"); params.append(_encrypt_api(api_key_plain))
    if api_base is not None:
        fields.append("api_base = ?"); params.append(api_base)
    if model is not None:
        fields.append("model = ?"); params.append(model)
    if is_active is not None:
        fields.append("is_active = ?"); params.append(is_active)
    if last_test_success is not None:
        fields.append("last_test_success = ?"); params.append(last_test_success)
    params.append(key_id)
    _execute(f"UPDATE api_key SET {', '.join(fields)} WHERE key_id = ?", tuple(params), db_path)


def delete_api_key(key_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM api_key WHERE key_id = ?", (key_id,), db_path)


def get_active_api_keys(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    rows = _fetch_all(
        "SELECT * FROM api_key WHERE user_id = ? AND is_active = 1",
        (user_id,), db_path,
    )
    for r in rows:
        r["api_key"] = _decrypt_api(r["api_key_encrypted"])
    return rows


def get_api_key_by_id(key_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> dict | None:
    row = _fetch_one("SELECT * FROM api_key WHERE key_id = ?", (key_id,), db_path)
    if row:
        row["api_key"] = _decrypt_api(row["api_key_encrypted"])
    return row


# ==================== user_personality ====================

def upsert_user_personality(
    user_id: str,
    interests_json: str | None = None,
    skills_json: str | None = None,
    preferences_json: str | None = None,
    study_work_patterns_json: str | None = None,
    personality_indicators_json: str | None = None,
    mbti_type: str | None = None,
    mbti_scores_json: str | None = None,
    mbti_confidence: float | None = None,
    mbti_description: str | None = None,
    interaction_count: int | None = None,
    mbti_last_updated: str | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    import datetime
    now = datetime.datetime.utcnow().isoformat()
    existing = _fetch_one("SELECT * FROM user_personality WHERE user_id = ?", (user_id,), db_path)
    if existing:
        field_map = {
            "interests_json": interests_json, "skills_json": skills_json,
            "preferences_json": preferences_json, "study_work_patterns_json": study_work_patterns_json,
            "personality_indicators_json": personality_indicators_json,
            "mbti_type": mbti_type, "mbti_scores_json": mbti_scores_json,
            "mbti_confidence": mbti_confidence, "mbti_description": mbti_description,
            "interaction_count": interaction_count, "mbti_last_updated": mbti_last_updated,
        }
        fields = [f"{k} = ?" for k, v in field_map.items() if v is not None]
        params = [v for v in field_map.values() if v is not None]
        if fields:
            fields.append("last_updated = ?")
            params.append(now)
            params.append(user_id)
            _execute(f"UPDATE user_personality SET {', '.join(fields)} WHERE user_id = ?", tuple(params), db_path)
    else:
        _execute(
            """INSERT INTO user_personality (user_id, interests_json, skills_json,
               preferences_json, study_work_patterns_json, personality_indicators_json,
               mbti_type, mbti_scores_json, mbti_confidence, mbti_description,
               interaction_count, mbti_last_updated, last_updated)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, interests_json, skills_json, preferences_json,
             study_work_patterns_json, personality_indicators_json,
             mbti_type, mbti_scores_json, mbti_confidence, mbti_description,
             interaction_count or 0, mbti_last_updated, now),
            db_path,
        )


def get_user_personality(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> dict | None:
    return _fetch_one("SELECT * FROM user_personality WHERE user_id = ?", (user_id,), db_path)


def delete_user_personality(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM user_personality WHERE user_id = ?", (user_id,), db_path)


# ==================== interaction_log ====================

def create_interaction_log(
    user_id: str,
    conversation_id: str,
    timestamp: str,
    session_id: str | None = None,
    platform: str | None = None,
    user_message: str | None = None,
    intent_category: str | None = None,
    keywords_json: str | None = None,
    language: str | None = None,
    sentiment: str | None = None,
    urgency: str | None = None,
    message_length: int | None = None,
    contains_file_reference: str | None = None,
    agent_response: str | None = None,
    agent_response_length: int | None = None,
    follow_up_required: int | None = None,
    suggested_actions_json: str | None = None,
    tools_invoked_json: str | None = None,
    files_accessed_json: str | None = None,
    total_execution_time_ms: int | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    return _execute(
        """INSERT INTO interaction_log (user_id, conversation_id, session_id, platform,
           timestamp, user_message, intent_category, keywords_json, language,
           sentiment, urgency, message_length, contains_file_reference,
           agent_response, agent_response_length, follow_up_required,
           suggested_actions_json, tools_invoked_json, files_accessed_json,
           total_execution_time_ms)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, conversation_id, session_id, platform, timestamp,
         user_message, intent_category, keywords_json, language,
         sentiment, urgency, message_length, contains_file_reference,
         agent_response, agent_response_length, follow_up_required,
         suggested_actions_json, tools_invoked_json, files_accessed_json,
         total_execution_time_ms),
        db_path,
    )


def list_interaction_logs_by_user(
    user_id: str,
    limit: int = 100,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> list[dict]:
    return _fetch_all(
        "SELECT * FROM interaction_log WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
        (user_id, limit), db_path,
    )


def get_interaction_log(conversation_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> dict | None:
    return _fetch_one("SELECT * FROM interaction_log WHERE conversation_id = ?", (conversation_id,), db_path)


def delete_interaction_log(conversation_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM interaction_log WHERE conversation_id = ?", (conversation_id,), db_path)




def count_interaction_logs_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> int:
    row = _fetch_one("SELECT COUNT(*) as cnt FROM interaction_log WHERE user_id = ?", (user_id,), db_path)
    return row["cnt"] if row else 0


# ==================== activity_log ====================

def upsert_activity_log(
    user_id: str,
    log_date: str,
    hour: int,
    count: int = 1,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    import datetime
    now = datetime.datetime.utcnow().isoformat()
    _execute(
        """
        INSERT INTO activity_log (user_id, log_date, hour, count, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, log_date, hour) DO UPDATE SET
            count = count + excluded.count,
            updated_at = excluded.updated_at
        """,
        (user_id, log_date, hour, count, now),
        db_path,
    )


def upsert_activity_logs_batch(
    logs: list[dict],
    user_id: str,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    import datetime
    now = datetime.datetime.utcnow().isoformat()
    for log in logs:
        _execute(
            """
            INSERT INTO activity_log (user_id, log_date, hour, count, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, log_date, hour) DO UPDATE SET
                count = count + excluded.count,
                updated_at = excluded.updated_at
            """,
            (user_id, log.get("log_date"), log.get("hour"), log.get("count", 1), now),
            db_path,
        )


def list_activity_logs(
    user_id: str,
    from_date: str | None = None,
    to_date: str | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> list[dict]:
    conditions = ["user_id = ?"]
    params: list = [user_id]
    if from_date:
        conditions.append("log_date >= ?")
        params.append(from_date)
    if to_date:
        conditions.append("log_date <= ?")
        params.append(to_date)
    where = " AND ".join(conditions)
    return _fetch_all(
        f"SELECT * FROM activity_log WHERE {where} ORDER BY log_date ASC, hour ASC",
        tuple(params), db_path,
    )
