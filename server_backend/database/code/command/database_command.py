import sqlite3
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR.parent.parent / "db" / "server.db"
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
    user_password_hash: str,
    user_salt: str,
    user_is_active: int,
    user_created_at: str,
    user_last_login: str | None,
    user_auto_login_token: str | None,
    user_source_device_id: str | None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    _execute(
        """
        INSERT INTO users (
            user_id, username, user_email, user_password_hash, user_salt,
            user_is_active, user_created_at, user_last_login, user_auto_login_token,
            user_source_device_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            user_email = excluded.user_email,
            user_password_hash = excluded.user_password_hash,
            user_salt = excluded.user_salt,
            user_is_active = excluded.user_is_active,
            user_created_at = excluded.user_created_at,
            user_last_login = excluded.user_last_login,
            user_auto_login_token = excluded.user_auto_login_token,
            user_source_device_id = excluded.user_source_device_id
        """,
        (
            user_id,
            username,
            user_email,
            user_password_hash,
            user_salt,
            user_is_active,
            user_created_at,
            user_last_login,
            user_auto_login_token,
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


def create_server_task(user_id: str, title: str, description: str = None,
                       priority: int = 2, status: str = "pending",
                       due_date: str = None, created_at: str = None,
                       db_path: str | Path = DEFAULT_DB_PATH) -> int:
    import datetime
    now = created_at or datetime.datetime.utcnow().isoformat()
    return _execute(
        "INSERT INTO task (user_id, title, description, priority, status, due_date, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, title, description, priority, status, due_date, now, now),
        db_path,
    )


def list_server_tasks_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM task WHERE user_id = ?", (user_id,), db_path)


def delete_server_tasks_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM task WHERE user_id = ?", (user_id,), db_path)


def upsert_user_setting(user_id: str, db_path: str | Path = DEFAULT_DB_PATH, **kwargs) -> None:
    import datetime
    now = datetime.datetime.utcnow().isoformat()
    existing = _fetch_one("SELECT * FROM user_setting WHERE user_id = ?", (user_id,), db_path)
    if existing:
        allowed = {"bio", "current_focus", "work_preference", "skills", "theme_config",
                   "notification_enabled", "privacy_share_data"}
        fields = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not fields:
            return
        fields["updated_at"] = now
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [user_id]
        _execute(f"UPDATE user_setting SET {set_clause} WHERE user_id = ?", tuple(values), db_path)
    else:
        _execute(
            "INSERT INTO user_setting (user_id, bio, current_focus, work_preference, skills, theme_config, notification_enabled, privacy_share_data, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, kwargs.get("bio"), kwargs.get("current_focus"), kwargs.get("work_preference"),
             kwargs.get("skills"), kwargs.get("theme_config"),
             kwargs.get("notification_enabled", 1), kwargs.get("privacy_share_data", 0), now),
            db_path,
        )


def delete_server_tis_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM tis_schedule_event WHERE user_id = ?", (user_id,), db_path)
    _execute("DELETE FROM tis_course WHERE user_id = ?", (user_id,), db_path)


def create_server_tis_course(user_id: str, course_name: str, teacher: str = None,
                             location: str = None, weeks: str = None,
                             term: str = None, raw_data: str = None,
                             db_path: str | Path = DEFAULT_DB_PATH) -> int:
    import datetime
    now = datetime.datetime.utcnow().isoformat()
    return _execute(
        "INSERT INTO tis_course (user_id, course_name, teacher, location, weeks, term, raw_data, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, course_name, teacher, location, weeks, term, raw_data, now),
        db_path,
    )


def create_server_tis_event(course_id: int, user_id: str, day_of_week: int,
                            week_num: int, period_start: int, period_end: int,
                            start_time: str = None, end_time: str = None,
                            db_path: str | Path = DEFAULT_DB_PATH) -> int:
    return _execute(
        "INSERT INTO tis_schedule_event (course_id, user_id, day_of_week, week_num, period_start, period_end, start_time, end_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (course_id, user_id, day_of_week, week_num, period_start, period_end, start_time, end_time),
        db_path,
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
    content: str | None,
    account_mail_password: str | None,
    account_cookie: str | None,
    account_bind_time: str | None,
    account_last_sync_time: str | None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    return _execute(
        """
        INSERT INTO account (
            user_id, account_platform_type, account_platform_username,
            content, account_mail_password, account_cookie, account_bind_time, account_last_sync_time
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            account_platform_type,
            account_platform_username,
            content,
            account_mail_password,
            account_cookie,
            account_bind_time,
            account_last_sync_time,
        ),
        db_path,
    )


def list_accounts(db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM account ORDER BY account_id DESC", (), db_path)


def list_accounts_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM account WHERE user_id = ? ORDER BY account_id DESC", (user_id,), db_path)


def update_account_credentials(
    account_id: int,
    account_mail_password: str | None,
    account_cookie: str | None,
    account_last_sync_time: str | None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    _execute(
        """
        UPDATE account
        SET account_mail_password = ?, account_cookie = ?, account_last_sync_time = ?
        WHERE account_id = ?
        """,
        (account_mail_password, account_cookie, account_last_sync_time, account_id),
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
            data_updated_at, data_created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        ),
        db_path,
    )


def list_all_data(db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM data ORDER BY data_id DESC", (), db_path)


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
    data_classification_code: int,
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
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    update_fields = [
        "data_title = ?",
        "data_content_text = ?",
        "data_link_url = ?",
        "data_release_time = ?",
        "data_ddl_time = ?",
        "data_is_previewable = ?",
        "data_classification_code = ?",
    ]
    params: list[object] = [
        data_title,
        data_content_text,
        data_link_url,
        data_release_time,
        data_ddl_time,
        data_is_previewable,
        data_classification_code,
    ]

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

    params.append(data_id)
    _execute(
        f"UPDATE data SET {', '.join(update_fields)} WHERE data_id = ?",
        tuple(params),
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
    schedule_priority: int = 2,
) -> int:
    return _execute(
        """
        INSERT INTO schedule (
            user_id, schedule_event_type, schedule_priority, schedule_title, schedule_start_time,
            schedule_end_time, schedule_location, schedule_description,
            schedule_related_link, schedule_recurrence_rule, schedule_color_tag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            schedule_event_type,
            schedule_priority,
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


def list_all_schedule(db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM schedule ORDER BY schedule_id DESC", (), db_path)


def list_schedule_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM schedule WHERE user_id = ? ORDER BY schedule_id DESC", (user_id,), db_path)


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
    schedule_priority: int | None = None,
) -> None:
    _execute(
        """
        UPDATE schedule
        SET schedule_title = ?, schedule_start_time = ?, schedule_end_time = ?,
            schedule_location = ?, schedule_description = ?, schedule_related_link = ?,
            schedule_recurrence_rule = ?, schedule_color_tag = ?,
            schedule_priority = COALESCE(?, schedule_priority)
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
            schedule_priority,
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


def list_all_sessions(db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
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


# code (server only)

def create_code(
    user_id: str,
    code_email: str,
    code_context: str,
    code_purpose: str,
    code_is_used: int,
    code_expires_at: str,
    code_created_at: str,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    return _execute(
        """
        INSERT INTO code (
            user_id, code_email, code_context, code_purpose,
            code_is_used, code_expires_at, code_created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            code_email,
            code_context,
            code_purpose,
            code_is_used,
            code_expires_at,
            code_created_at,
        ),
        db_path,
    )


def get_code_by_context(code_context: str, db_path: str | Path = DEFAULT_DB_PATH) -> dict | None:
    return _fetch_one("SELECT * FROM code WHERE code_context = ?", (code_context,), db_path)


def list_codes(db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM code ORDER BY code_id DESC", (), db_path)


def list_codes_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> list[dict]:
    return _fetch_all("SELECT * FROM code WHERE user_id = ? ORDER BY code_id DESC", (user_id,), db_path)


def mark_code_used(code_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("UPDATE code SET code_is_used = 1 WHERE code_id = ?", (code_id,), db_path)


def delete_code(code_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM code WHERE code_id = ?", (code_id,), db_path)


def delete_expired_codes(now_time: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM code WHERE code_expires_at < ?", (now_time,), db_path)


# ==================== event (sync) ====================

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


def delete_events_by_user(user_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> None:
    _execute("DELETE FROM event WHERE user_id = ?", (user_id,), db_path)


def upsert_event(user_id: str, e: dict, db_path: str | Path = DEFAULT_DB_PATH) -> int:
    import datetime
    now = datetime.datetime.utcnow().isoformat()
    return _execute(
        """INSERT INTO event (user_id, event_title, event_type, event_source,
           event_start_time, event_end_time, event_location, event_description,
           event_link_url, event_is_completed, event_show_in_todo,
           event_priority, event_color_tag, event_meta_json, event_created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT DO NOTHING""",
        (user_id, e.get("event_title", ""),
         e.get("event_type", "manual"), e.get("event_source", "manual"),
         e.get("event_start_time"), e.get("event_end_time"),
         e.get("event_location"), e.get("event_description"),
         e.get("event_link_url"),
         e.get("event_is_completed", 0), e.get("event_show_in_todo", 1),
         e.get("event_priority", 2), e.get("event_color_tag", "#007aff"),
         e.get("event_meta_json"), e.get("event_created_at", now)),
        db_path,
    )


def list_events_by_user(
    user_id: str,
    event_type: str | None = None,
    event_source: str | None = None,
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
    where = " AND ".join(conditions)
    return _fetch_all(
        f"SELECT * FROM event WHERE {where} ORDER BY event_id",
        tuple(params), db_path,
    )
