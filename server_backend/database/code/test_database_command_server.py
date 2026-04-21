from __future__ import annotations

import argparse
import inspect
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import database_command as db
import database_synchronize_handle as sync_handle
from database_test_data import get_test_data


INSERT_ORDER = [
    "user",
    "user_match_profile",
    "match_result",
    "sync_state",
    "account",
    "code",
    "category",
    "data",
    "schedule",
    "session",
    "chat",
]

DELETE_ORDER = [
    "chat",
    "session",
    "data",
    "category",
    "schedule",
    "code",
    "account",
    "match_result",
    "sync_state",
    "user_match_profile",
    "user",
]

TABLE_ALIAS = {
    "user": "user",
    "users": "user",
    "user_match_profile": "user_match_profile",
    "match_profile": "user_match_profile",
    "match_result": "match_result",
    "sync_state": "sync_state",
    "account": "account",
    "code": "code",
    "category": "category",
    "data": "data",
    "schedule": "schedule",
    "session": "session",
    "chat": "chat",
    "all": "all",
}


class ServerCommandTestRunner:
    def __init__(self) -> None:
        self.data = get_test_data()
        self._created: set[str] = set()
        self._ids: dict[str, int] = {}
        # 使用正常数据库路径（与database_command.py中的DEFAULT_DB_PATH一致）
        self.db_path = Path(__file__).resolve().parents[1] / "db" / "server.db"
        self.db_was_created = False
        self._ensure_db_ready()

    def close(self) -> None:
        return

    def _ensure_db_ready(self) -> None:
        if not self.db_path.exists():
            self.db_was_created = True
            print(f"[INFO] database not found, creating at: {self.db_path}")
            self._init_schema()
        else:
            print(f"[INFO] using database: {self.db_path}")

    def _init_schema(self) -> None:
        schema_path = Path(__file__).with_name("database_init.sql")
        schema_sql = schema_path.read_text(encoding="utf-8")
        with db._connect(self.db_path) as conn:
            conn.executescript(schema_sql)
            conn.commit()

    def _expect(self, condition: bool, message: str) -> None:
        if not condition:
            raise AssertionError(message)

    def _to_printable(self, value):
        if value is None:
            return None
        if isinstance(value, list):
            return [self._to_printable(item) for item in value]
        if isinstance(value, dict):
            return {key: self._to_printable(item) for key, item in value.items()}
        if hasattr(value, "keys"):
            return {key: self._to_printable(value[key]) for key in value.keys()}
        return value

    def _print_get_result(self, table: str, result) -> None:
        print(f"[RESULT] get {table}")
        print(json.dumps(self._to_printable(result), indent=2, sort_keys=True, default=str))

    def _find_session_with_chat(self) -> tuple[int | None, list]:
        user_id = self.data["user"]["user_id"]
        sessions = db.list_sessions_by_user(user_id, db_path=self.db_path)
        for session in sessions:
            session_id = session["session_id"]
            rows = db.list_chat_by_session(session_id, db_path=self.db_path)
            if rows:
                return session_id, rows
        return None, []

    def _has_table_data(self, table: str) -> bool:
        if table == "user":
            return len(db.list_users(db_path=self.db_path)) > 0
        if table == "personal_information":
            return len(db.list_personal_information(db_path=self.db_path)) > 0
        if table == "sync_state":
            return len(db.list_sync_states(db_path=self.db_path)) > 0
        if table == "account":
            return len(db.list_accounts(db_path=self.db_path)) > 0
        if table == "code":
            return len(db.list_codes(db_path=self.db_path)) > 0
        if table == "category":
            return len(db.list_categories(db_path=self.db_path)) > 0
        if table == "data":
            return len(db.list_all_data(db_path=self.db_path)) > 0
        if table == "schedule":
            return len(db.list_all_schedule(db_path=self.db_path)) > 0
        if table == "session":
            return len(db.list_all_sessions(db_path=self.db_path)) > 0
        if table == "chat":
            _, rows = self._find_session_with_chat()
            return len(rows) > 0
        raise ValueError(f"unsupported table: {table}")

    def _require_existing(self, table: str, action: str) -> None:
        if not self._has_table_data(table):
            raise AssertionError(
                f"{action} {table} requires existing data in persistent test DB. "
                f"Run --action store --table {table} first."
            )

    def _patch_db_path_for_handle(self) -> dict[str, object]:
        originals: dict[str, object] = {}
        for name, obj in vars(db).items():
            if name.startswith("_") or not callable(obj):
                continue

            signature = inspect.signature(obj)
            if "db_path" not in signature.parameters:
                continue

            originals[name] = obj

            def _wrapper(*args, __orig=obj, **kwargs):
                kwargs.setdefault("db_path", self.db_path)
                return __orig(*args, **kwargs)

            setattr(db, name, _wrapper)

        return originals

    def _restore_db_functions(self, originals: dict[str, object]) -> None:
        for name, obj in originals.items():
            setattr(db, name, obj)

    def _ensure_inserted(self, table: str) -> None:
        if table in self._created:
            return

        if table == "user":
            user = self.data["user"]
            db.upsert_user(
                user_id=user["user_id"],
                username=user["username"],
                user_email=user["user_email"],
                user_password_hash=user["user_password_hash"],
                user_salt=user["user_salt"],
                user_is_active=user["user_is_active"],
                user_created_at=user["user_created_at"],
                user_last_login=user["user_last_login"],
                user_auto_login_token=user["user_auto_login_token"],
                user_source_device_id=user["user_source_device_id"],
                db_path=self.db_path,
            )
            self._created.add(table)
            return

        if table == "user_match_profile":
            self._ensure_inserted("user")
            row = self.data["user_match_profile"]
            db.upsert_user_match_profile(
                user_id=row["user_id"],
                answers=row["answers"],
                is_open=row["is_open"],
                last_match_time=row["last_match_time"],
                db_path=self.db_path,
            )
            self._created.add(table)
            return

        if table == "match_result":
            self._ensure_inserted("user")
            existing = db.list_match_results_by_user(self.data["user"]["user_id"], db_path=self.db_path)
            if existing:
                self._ids["match_result_id"] = existing[0]["id"]
                self._created.add(table)
                return
            row = self.data["match_result"]
            self._ids["match_result_id"] = db.create_match_result(
                user_id=row["user_id"],
                matched_user_id=row["matched_user_id"],
                similarity_score=row["similarity_score"],
                created_at=row["created_at"],
                is_shared=row["is_shared"],
                db_path=self.db_path,
            )
            self._created.add(table)
            return

        if table == "sync_state":
            self._ensure_inserted("user")
            row = self.data["sync_state"]
            db.upsert_sync_state(
                user_id=row["user_id"],
                user_data_updated_at=row["user_data_updated_at"],
                user_last_synced_at=row["user_last_synced_at"],
                user_version=row["user_version"],
                sync_updated_at=row["sync_updated_at"],
                db_path=self.db_path,
            )
            self._created.add(table)
            return

        if table == "account":
            self._ensure_inserted("user")
            existing = db.list_accounts_by_user(self.data["user"]["user_id"], db_path=self.db_path)
            if existing:
                self._ids["account_id"] = existing[0]["account_id"]
                self._created.add(table)
                return
            row = self.data["account"]
            self._ids["account_id"] = db.create_account(
                user_id=row["user_id"],
                account_platform_type=row["account_platform_type"],
                account_platform_username=row["account_platform_username"],
                account_mail_password=row["account_mail_password"],
                account_cookie=row["account_cookie"],
                account_bind_time=row["account_bind_time"],
                account_last_sync_time=row["account_last_sync_time"],
                db_path=self.db_path,
            )
            self._created.add(table)
            return

        if table == "code":
            self._ensure_inserted("user")
            existing = db.list_codes_by_user(self.data["user"]["user_id"], db_path=self.db_path)
            if existing:
                self._ids["code_id"] = existing[0]["code_id"]
                self._created.add(table)
                return
            row = self.data["code"]
            self._ids["code_id"] = db.create_code(
                user_id=row["user_id"],
                code_email=row["code_email"],
                code_context=row["code_context"],
                code_purpose=row["code_purpose"],
                code_is_used=row["code_is_used"],
                code_expires_at=row["code_expires_at"],
                code_created_at=row["code_created_at"],
                db_path=self.db_path,
            )
            self._created.add(table)
            return

        if table == "category":
            self._ensure_inserted("user")
            existing = db.list_categories_by_user(self.data["user"]["user_id"], db_path=self.db_path)
            if existing:
                self._ids["category_id"] = existing[0]["category_id"]
                self._created.add(table)
                return
            row = self.data["category"]
            self._ids["category_id"] = db.create_category(
                user_id=row["user_id"],
                category_kind=row["category_kind"],
                category_title=row["category_title"],
                category_content=row["category_content"],
                category_link=row["category_link"],
                category_created_at=row["category_created_at"],
                db_path=self.db_path,
            )
            self._created.add(table)
            return

        if table == "data":
            self._ensure_inserted("category")
            existing = db.list_data_by_user(self.data["user"]["user_id"], db_path=self.db_path)
            if existing:
                self._ids["data_id"] = existing[0]["data_id"]
                self._created.add(table)
                return
            row = self.data["data"]
            self._ids["data_id"] = db.create_data(
                user_id=row["user_id"],
                data_category_id=self._ids["category_id"],
                data_content_type=row["data_content_type"],
                data_classification_code=row["data_classification_code"],
                data_title=row["data_title"],
                data_content_text=row["data_content_text"],
                data_link_url=row["data_link_url"],
                data_release_time=row["data_release_time"],
                data_ddl_time=row["data_ddl_time"],
                data_is_previewable=row["data_is_previewable"],
                data_created_at=row["data_created_at"],
                db_path=self.db_path,
            )
            self._created.add(table)
            return

        if table == "schedule":
            self._ensure_inserted("user")
            existing = db.list_schedule_by_user(self.data["user"]["user_id"], db_path=self.db_path)
            if existing:
                self._ids["schedule_id"] = existing[0]["schedule_id"]
                self._created.add(table)
                return
            row = self.data["schedule"]
            self._ids["schedule_id"] = db.create_schedule(
                user_id=row["user_id"],
                schedule_event_type=row["schedule_event_type"],
                schedule_title=row["schedule_title"],
                schedule_start_time=row["schedule_start_time"],
                schedule_end_time=row["schedule_end_time"],
                schedule_location=row["schedule_location"],
                schedule_description=row["schedule_description"],
                schedule_related_link=row["schedule_related_link"],
                schedule_recurrence_rule=row["schedule_recurrence_rule"],
                schedule_color_tag=row["schedule_color_tag"],
                schedule_priority=row.get("schedule_priority", 2),
                db_path=self.db_path,
            )
            self._created.add(table)
            return

        if table == "session":
            self._ensure_inserted("user")
            existing = db.list_sessions_by_user(self.data["user"]["user_id"], db_path=self.db_path)
            if existing:
                self._ids["session_id"] = existing[0]["session_id"]
                self._created.add(table)
                return
            row = self.data["session"]
            self._ids["session_id"] = db.create_session(
                user_id=row["user_id"],
                session_last_visited_at=row["session_last_visited_at"],
                db_path=self.db_path,
            )
            self._created.add(table)
            return

        if table == "chat":
            self._ensure_inserted("session")
            existing_session_id, existing_rows = self._find_session_with_chat()
            if existing_rows and existing_session_id is not None:
                self._ids["session_id"] = existing_session_id
                self._ids["chat_id"] = existing_rows[0]["chat_id"]
                self._created.add(table)
                return
            row = self.data["chat"]
            self._ids["chat_id"] = db.create_chat(
                session_id=self._ids["session_id"],
                chat_role=row["chat_role"],
                chat_message_content=row["chat_message_content"],
                thought_trace=row["thought_trace"],
                chat_tool_calls=row["chat_tool_calls"],
                chat_tokens_usage=row["chat_tokens_usage"],
                chat_created_at=row["chat_created_at"],
                db_path=self.db_path,
            )
            self._created.add(table)
            return

        raise ValueError(f"unsupported table: {table}")

    def run_store(self, table: str) -> None:
        self._ensure_inserted(table)
        print(f"[PASS] store {table}")

    def run_get(self, table: str) -> None:
        self._require_existing(table, "get")
        result = None

        if table == "user":
            rows = db.list_users(db_path=self.db_path)
            self._expect(len(rows) >= 1, "list_users should contain at least one row")
            user_id = rows[0]["user_id"]
            row = db.get_user(user_id, db_path=self.db_path)
            self._expect(row is not None, "get_user should return one row")
            result = {"get_user": row, "list_users": rows}
        elif table == "personal_information":
            rows = db.list_personal_information(db_path=self.db_path)
            self._expect(len(rows) >= 1, "list_personal_information should contain at least one row")
            user_id = rows[0]["user_id"]
            row = db.get_personal_information(user_id, db_path=self.db_path)
            self._expect(row is not None, "get_personal_information should return one row")
            result = row
        elif table == "match_result":
            rows = db.list_match_results_by_user(user_id, db_path=self.db_path)
            self._expect(len(rows) >= 1, "list_match_results_by_user should contain at least one row")
            result = rows
        elif table == "sync_state":
            rows = db.list_sync_states(db_path=self.db_path)
            self._expect(len(rows) >= 1, "list_sync_states should contain at least one row")
            user_id = rows[0]["user_id"]
            row = db.get_sync_state(user_id, db_path=self.db_path)
            self._expect(row is not None, "get_sync_state should return one row")
            result = row
        elif table == "account":
            rows = db.list_accounts(db_path=self.db_path)
            self._expect(len(rows) >= 1, "list_accounts should contain at least one row")
            user_id = rows[0]["user_id"]
            rows_by_user = db.list_accounts_by_user(user_id, db_path=self.db_path)
            self._expect(len(rows_by_user) >= 1, "list_accounts_by_user should contain at least one row")
            result = rows_by_user
        elif table == "code":
            rows = db.list_codes(db_path=self.db_path)
            self._expect(len(rows) >= 1, "list_codes should contain at least one row")
            user_id = rows[0]["user_id"]
            row = db.get_code_by_context(rows[0]["code_context"], db_path=self.db_path)
            self._expect(row is not None, "get_code_by_context should return one row")
            rows_by_user = db.list_codes_by_user(user_id, db_path=self.db_path)
            self._expect(len(rows_by_user) >= 1, "list_codes_by_user should contain at least one row")
            result = {"get_code_by_context": row, "list_codes_by_user": rows_by_user}
        elif table == "category":
            rows = db.list_categories(db_path=self.db_path)
            self._expect(len(rows) >= 1, "list_categories should contain at least one row")
            user_id = rows[0]["user_id"]
            rows_by_user = db.list_categories_by_user(user_id, db_path=self.db_path)
            self._expect(len(rows_by_user) >= 1, "list_categories_by_user should contain at least one row")
            result = rows_by_user
        elif table == "data":
            rows = db.list_all_data(db_path=self.db_path)
            self._expect(len(rows) >= 1, "list_all_data should contain at least one row")
            user_id = rows[0]["user_id"]
            rows_by_user = db.list_data_by_user(user_id, db_path=self.db_path)
            self._expect(len(rows_by_user) >= 1, "list_data_by_user should contain at least one row")
            result = rows_by_user
        elif table == "schedule":
            rows = db.list_all_schedule(db_path=self.db_path)
            self._expect(len(rows) >= 1, "list_all_schedule should contain at least one row")
            user_id = rows[0]["user_id"]
            rows_by_user = db.list_schedule_by_user(user_id, db_path=self.db_path)
            self._expect(len(rows_by_user) >= 1, "list_schedule_by_user should contain at least one row")
            result = rows_by_user
        elif table == "session":
            rows = db.list_all_sessions(db_path=self.db_path)
            self._expect(len(rows) >= 1, "list_all_sessions should contain at least one row")
            user_id = rows[0]["user_id"]
            rows_by_user = db.list_sessions_by_user(user_id, db_path=self.db_path)
            self._expect(len(rows_by_user) >= 1, "list_sessions_by_user should contain at least one row")
            result = rows_by_user
        elif table == "chat":
            sessions = db.list_all_sessions(db_path=self.db_path)
            self._expect(len(sessions) >= 1, "chat requires one existing session")
            session_id = sessions[0]["session_id"]
            rows = db.list_chat_by_session(session_id, db_path=self.db_path)
            self._expect(len(rows) >= 1, "list_chat_by_session should contain at least one row")
            result = rows
        else:
            raise ValueError(f"unsupported table: {table}")

        self._print_get_result(table, result)
        print(f"[PASS] get {table}")

    def run_delete(self, table: str) -> None:
        user_id = self.data["user"]["user_id"]
        self._require_existing(table, "delete")

        if table == "chat":
            session_id, rows_before = self._find_session_with_chat()
            self._expect(session_id is not None, "chat requires one existing session")
            self._expect(len(rows_before) >= 1, "chat should contain at least one row before delete")
            db.delete_chat(rows_before[0]["chat_id"], db_path=self.db_path)
            rows_after = db.list_chat_by_session(session_id, db_path=self.db_path)
            self._expect(len(rows_after) == len(rows_before) - 1, "chat should delete exactly one row")
        elif table == "session":
            rows_before = db.list_sessions_by_user(user_id, db_path=self.db_path)
            self._expect(len(rows_before) >= 1, "session should contain at least one row before delete")
            db.delete_session(rows_before[0]["session_id"], db_path=self.db_path)
            rows_after = db.list_sessions_by_user(user_id, db_path=self.db_path)
            self._expect(len(rows_after) == len(rows_before) - 1, "session should delete exactly one row")
        elif table == "data":
            rows_before = db.list_data_by_user(user_id, db_path=self.db_path)
            self._expect(len(rows_before) >= 1, "data should contain at least one row before delete")
            db.delete_data(rows_before[0]["data_id"], db_path=self.db_path)
            rows_after = db.list_data_by_user(user_id, db_path=self.db_path)
            self._expect(len(rows_after) == len(rows_before) - 1, "data should delete exactly one row")
        elif table == "category":
            rows_before = db.list_categories_by_user(user_id, db_path=self.db_path)
            self._expect(len(rows_before) >= 1, "category should contain at least one row before delete")
            db.delete_category(rows_before[0]["category_id"], db_path=self.db_path)
            rows_after = db.list_categories_by_user(user_id, db_path=self.db_path)
            self._expect(len(rows_after) == len(rows_before) - 1, "category should delete exactly one row")
        elif table == "schedule":
            rows_before = db.list_schedule_by_user(user_id, db_path=self.db_path)
            self._expect(len(rows_before) >= 1, "schedule should contain at least one row before delete")
            db.delete_schedule(rows_before[0]["schedule_id"], db_path=self.db_path)
            rows_after = db.list_schedule_by_user(user_id, db_path=self.db_path)
            self._expect(len(rows_after) == len(rows_before) - 1, "schedule should delete exactly one row")
        elif table == "code":
            rows_before = db.list_codes_by_user(user_id, db_path=self.db_path)
            self._expect(len(rows_before) >= 1, "code should contain at least one row before delete")
            db.delete_code(rows_before[0]["code_id"], db_path=self.db_path)
            rows_after = db.list_codes_by_user(user_id, db_path=self.db_path)
            self._expect(len(rows_after) == len(rows_before) - 1, "code should delete exactly one row")
        elif table == "account":
            rows_before = db.list_accounts_by_user(user_id, db_path=self.db_path)
            self._expect(len(rows_before) >= 1, "account should contain at least one row before delete")
            db.delete_account(rows_before[0]["account_id"], db_path=self.db_path)
            rows_after = db.list_accounts_by_user(user_id, db_path=self.db_path)
            self._expect(len(rows_after) == len(rows_before) - 1, "account should delete exactly one row")
        elif table == "match_result":
            rows_before = db.list_match_results_by_user(user_id, db_path=self.db_path)
            self._expect(len(rows_before) >= 1, "match_result should contain at least one row before delete")
            db.delete_match_result(rows_before[0]["id"], db_path=self.db_path)
            rows_after = db.list_match_results_by_user(user_id, db_path=self.db_path)
            self._expect(len(rows_after) == len(rows_before) - 1, "match_result should delete exactly one row")
        elif table == "sync_state":
            db.delete_sync_state(user_id, db_path=self.db_path)
            row = db.get_sync_state(user_id, db_path=self.db_path)
            self._expect(row is None, "sync_state should be deleted")
        elif table == "user_match_profile":
            db.delete_user_match_profile(user_id, db_path=self.db_path)
            row = db.get_user_match_profile(user_id, db_path=self.db_path)
            self._expect(row is None, "user_match_profile should be deleted")
        elif table == "user":
            db.delete_user(user_id, db_path=self.db_path)
            row = db.get_user(user_id, db_path=self.db_path)
            self._expect(row is None, "user should be deleted")
        else:
            raise ValueError(f"unsupported table: {table}")

        print(f"[PASS] delete {table}")

    def run_sync(self) -> None:
        user_id = self.data["user"]["user_id"]
        state = self.data["sync_state"]

        for name in INSERT_ORDER:
            self._require_existing(name, "sync")

        originals = self._patch_db_path_for_handle()
        try:
            probe_resp = sync_handle.handle_sync_request(
                {
                    "action": "probe",
                    "payload": {
                        "user_id": user_id,
                        "client_user_data_updated_at": state["user_data_updated_at"],
                        "client_user_last_synced_at": state["user_last_synced_at"],
                        "client_user_version": state["user_version"],
                    },
                }
            )
            self._expect(probe_resp.get("ok") is True, "server probe failed")

            pull_resp = sync_handle.handle_sync_request(
                {
                    "action": "pull",
                    "payload": {
                        "user_id": user_id,
                        "request_id": "server-sync-test-pull",
                    },
                }
            )
            self._expect(pull_resp.get("ok") is True, "server pull failed")

            push_packet = pull_resp["packet"]
            push_packet["meta"]["source"] = "local"
            categories = push_packet.get("payload", {}).get("category")
            self._expect(isinstance(categories, list) and len(categories) > 0, "server pull packet has no category rows")
            marker = f"server-sync-marker-{int(datetime.now(timezone.utc).timestamp())}"
            categories[0]["category_title"] = marker
            push_resp = sync_handle.handle_sync_request(
                {
                    "action": "push",
                    "payload": push_packet,
                }
            )
            self._expect(push_resp.get("ok") is True, "server push failed")

            rows_after_push = db.list_categories_by_user(user_id, db_path=self.db_path)
            self._expect(
                any(row["category_title"] == marker for row in rows_after_push),
                "sync push did not write payload changes into persistent test DB",
            )

            now_iso = datetime.now(timezone.utc).isoformat()
            ack_resp = sync_handle.handle_sync_request(
                {
                    "action": "ack",
                    "payload": {
                        "user_id": user_id,
                        "ack_type": "push_applied",
                        "client_applied_at": now_iso,
                        "client_user_version": int(state["user_version"]),
                        "request_id": "server-sync-test-ack",
                    },
                }
            )
            self._expect(ack_resp.get("ok") is True, "server ack failed")
        finally:
            self._restore_db_functions(originals)

        print(f"[INFO] verified server handle push writes into test DB: {self.db_path}")

        print("[PASS] sync server_handle")

    def run_sync_receive_push(self, packet_file: Path, ack_file: Path | None = None) -> None:
        if not packet_file.exists():
            raise AssertionError(f"packet file not found: {packet_file}")

        payload = json.loads(packet_file.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise AssertionError("packet content must be a JSON object")

        user = payload.get("user")
        if not isinstance(user, dict) or not user.get("user_id"):
            raise AssertionError("packet.user.user_id is required")

        user_id = user["user_id"]
        if db.get_user(user_id, db_path=self.db_path) is None:
            raise AssertionError(
                "server test DB missing sync baseline user; run server --action store --table user first"
            )

        originals = self._patch_db_path_for_handle()
        try:
            push_resp = sync_handle.handle_sync_request(
                {
                    "action": "push",
                    "payload": payload,
                }
            )
            self._expect(push_resp.get("ok") is True, f"server push failed: {push_resp}")
            self._expect(
                push_resp.get("result") == "applied",
                f"server push should be applied in e2e test, got: {push_resp.get('result')}",
            )
        finally:
            self._restore_db_functions(originals)

        ack_payload = {
            "user_id": user_id,
            "server_user_last_synced_at": push_resp.get("server_user_last_synced_at"),
            "server_user_version": push_resp.get("server_user_version"),
            "server_user_data_updated_at": push_resp.get("server_user_data_updated_at"),
            "request_id": "server-sync-e2e-ack",
        }

        self._expect(
            isinstance(ack_payload["server_user_last_synced_at"], str) and bool(ack_payload["server_user_last_synced_at"]),
            "server_user_last_synced_at missing in push response",
        )
        self._expect(
            ack_payload["server_user_version"] is not None,
            "server_user_version missing in push response",
        )

        if ack_file is not None:
            ack_file.parent.mkdir(parents=True, exist_ok=True)
            ack_file.write_text(json.dumps(ack_payload, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"[INFO] server received local push and wrote test DB: {self.db_path}")
        if ack_file is not None:
            print(f"[INFO] server ack written to: {ack_file}")
        print("[PASS] sync_receive_push server_handle")

    def run_sync_build_pull(self, user_id: str, packet_file: Path, marker: str | None = None) -> None:
        user = db.get_user(user_id, db_path=self.db_path)
        if user is None:
            raise AssertionError(
                "server test DB missing sync baseline user; run server --action store --table user first"
            )

        if marker:
            db.upsert_user(
                user_id=user["user_id"],
                username=user["username"],
                user_email=user["user_email"],
                user_password_hash=user["user_password_hash"],
                user_salt=user["user_salt"],
                user_is_active=user["user_is_active"],
                user_created_at=user["user_created_at"],
                user_last_login=user["user_last_login"],
                user_auto_login_token=user["user_auto_login_token"],
                user_source_device_id=marker,
                db_path=self.db_path,
            )

            state = db.get_sync_state(user_id, db_path=self.db_path)
            now_iso = datetime.now(timezone.utc).isoformat()
            next_version = int(state["user_version"]) + 1 if state is not None else 1
            db.upsert_sync_state(
                user_id=user_id,
                user_data_updated_at=now_iso,
                user_last_synced_at=now_iso,
                user_version=next_version,
                sync_updated_at=now_iso,
                db_path=self.db_path,
            )

        originals = self._patch_db_path_for_handle()
        try:
            pull_resp = sync_handle.handle_sync_request(
                {
                    "action": "pull",
                    "payload": {
                        "user_id": user_id,
                        "request_id": "server-sync-e2e-pull",
                    },
                }
            )
            self._expect(pull_resp.get("ok") is True, f"server pull failed: {pull_resp}")
        finally:
            self._restore_db_functions(originals)

        packet = pull_resp.get("packet")
        self._expect(isinstance(packet, dict), "server pull response packet should be a JSON object")

        packet_file.parent.mkdir(parents=True, exist_ok=True)
        packet_file.write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"[INFO] server pull packet written to: {packet_file}")
        if marker:
            print(f"[INFO] server user_source_device_id marker set to: {marker}")
        print("[PASS] sync_build_pull server_handle")


def _normalize_table(table: str) -> str:
    normalized = TABLE_ALIAS.get(table.strip().lower())
    if normalized is None:
        valid = ", ".join(TABLE_ALIAS.keys())
        raise ValueError(f"invalid table '{table}', valid values: {valid}")
    return normalized


def _run_action(
    action: str,
    table: str,
    packet_file: str | None,
    ack_file: str | None,
    user_id: str | None,
    marker: str | None,
) -> None:
    runner = ServerCommandTestRunner()
    try:
        if runner.db_was_created and action in {"get", "delete", "sync"}:
            print(
                f"[SKIP] action '{action}' cannot run in the same run as initial DB creation. "
                "Store data first, then rerun this action."
            )
            return

        if table == "all":
            targets = INSERT_ORDER if action in {"store", "get"} else DELETE_ORDER
        else:
            targets = [table]

        if action == "store":
            for name in targets:
                runner.run_store(name)
        elif action == "get":
            for name in targets:
                runner.run_get(name)
        elif action == "delete":
            for name in targets:
                runner.run_delete(name)
        elif action == "sync":
            raise ValueError(
                "single-end sync test is disabled; use local --action sync --table all for dual-end sync"
            )
        elif action == "sync_receive_push":
            if packet_file is None:
                raise ValueError("sync_receive_push requires --packet-file")
            if runner.db_was_created:
                raise ValueError("sync_receive_push cannot run on first DB initialization; seed server user first")

            packet_path = Path(packet_file)
            ack_path = Path(ack_file) if ack_file else None
            runner.run_sync_receive_push(packet_path, ack_path)
        elif action == "sync_build_pull":
            if packet_file is None:
                raise ValueError("sync_build_pull requires --packet-file")
            if runner.db_was_created:
                raise ValueError("sync_build_pull cannot run on first DB initialization; seed server user first")

            target_user_id = user_id or runner.data["user"]["user_id"]
            packet_path = Path(packet_file)
            runner.run_sync_build_pull(target_user_id, packet_path, marker)
        else:
            raise ValueError(f"unsupported action: {action}")
    finally:
        runner.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run server database command tests by action and table.",
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["store", "get", "delete", "sync", "sync_receive_push", "sync_build_pull"],
        help="Action to test: store/get/delete/sync(disabled)/sync_receive_push/sync_build_pull.",
    )
    parser.add_argument(
        "--table",
        default="all",
        help="Table to test: all or one table name (user, users, user_match_profile, match_result, sync_state, account, code, category, data, schedule, session, chat).",
    )
    parser.add_argument(
        "--packet-file",
        default=None,
        help="JSON packet file used by sync_receive_push.",
    )
    parser.add_argument(
        "--ack-file",
        default=None,
        help="Output JSON ack file used by sync_receive_push.",
    )
    parser.add_argument(
        "--user-id",
        default=None,
        help="User id used by sync_build_pull. Defaults to fixture user id.",
    )
    parser.add_argument(
        "--marker",
        default=None,
        help="Optional marker written to server user_source_device_id before sync_build_pull.",
    )

    args = parser.parse_args()

    try:
        table = _normalize_table(args.table)
        _run_action(args.action, table, args.packet_file, args.ack_file, args.user_id, args.marker)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    print("[DONE] all selected checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
