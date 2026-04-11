from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from . import database_command as db
except ImportError:
    import database_command as db

USER_FIELDS = (
    "user_id",
    "username",
    "user_email",
    "user_is_active",
    "user_created_at",
    "user_last_login",
    "user_version",
    "user_source_device_id",
    "user_last_synced_at",
)

PERSONAL_INFORMATION_FIELDS = (
    "user_id",
    "personal_information_json",
)

ACCOUNT_FIELDS = (
    "account_id",
    "user_id",
    "account_platform_type",
    "account_platform_username",
    "account_bind_time",
    "account_last_sync_time",
)

CATEGORY_FIELDS = (
    "category_id",
    "user_id",
    "category_kind",
    "category_title",
    "category_content",
    "category_link",
    "category_created_at",
)

DATA_FIELDS = (
    "data_id",
    "user_id",
    "data_category_id",
    "data_content_type",
    "data_title",
    "data_content_text",
    "data_link_url",
    "data_release_time",
    "data_ddl_time",
    "data_is_previewable",
    "data_created_at",
)

SCHEDULE_FIELDS = (
    "schedule_id",
    "user_id",
    "schedule_event_type",
    "schedule_title",
    "schedule_start_time",
    "schedule_end_time",
    "schedule_location",
    "schedule_description",
    "schedule_related_link",
    "schedule_recurrence_rule",
    "schedule_color_tag",
)

SESSION_FIELDS = (
    "session_id",
    "user_id",
    "session_last_visited_at",
)

CHAT_FIELDS = (
    "chat_id",
    "session_id",
    "chat_role",
    "chat_message_content",
    "thought_trace",
    "chat_tool_calls",
    "chat_tokens_usage",
    "chat_created_at",
)

_USER_LOCKS: dict[str, threading.RLock] = {}
_USER_LOCKS_GUARD = threading.Lock()


def _get_user_lock(user_id: str) -> threading.RLock:
    with _USER_LOCKS_GUARD:
        lock = _USER_LOCKS.get(user_id)
        if lock is None:
            lock = threading.RLock()
            _USER_LOCKS[user_id] = lock
        return lock


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pick(row: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    return {k: row.get(k) for k in keys if k in row}


def _load_payload(payload: dict[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload

    if isinstance(payload, Path):
        return json.loads(payload.read_text(encoding="utf-8"))

    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            return json.loads(Path(payload).read_text(encoding="utf-8"))

    raise TypeError("payload must be dict, json string, or file path")


def _parse_iso_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None

    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _coerce_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_personal_information_json(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, str):
        try:
            json.loads(value)
        except json.JSONDecodeError:
            return None
        return value

    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)

    return None


def _sync_state_from_user_row(user: dict[str, Any]) -> dict[str, Any]:
    now = _now_iso()
    return {
        "user_id": user["user_id"],
        "user_data_updated_at": user.get("user_last_login") or user.get("user_created_at") or now,
        "user_last_synced_at": None,
        "user_version": 1,
        "sync_updated_at": now,
    }


def _get_effective_sync_state(user_id: str, user_row: dict[str, Any] | None = None) -> dict[str, Any] | None:
    state = db.get_sync_state(user_id)
    if state:
        return state

    user = user_row or db.get_user(user_id)
    if not user:
        return None

    fallback = _sync_state_from_user_row(user)
    db.upsert_sync_state(
        user_id=fallback["user_id"],
        user_data_updated_at=fallback["user_data_updated_at"],
        user_last_synced_at=fallback["user_last_synced_at"],
        user_version=fallback["user_version"],
        sync_updated_at=fallback["sync_updated_at"],
    )
    return db.get_sync_state(user_id)


def _is_stale_user_payload(
    incoming_user: dict[str, Any],
    existing_state: dict[str, Any],
    generated_at: Any,
) -> bool:
    existing_version = int(existing_state.get("user_version") or 0)
    incoming_version_raw = incoming_user.get("user_version")

    if incoming_version_raw is not None:
        incoming_version = _coerce_int(incoming_version_raw)
        if incoming_version is not None:
            if incoming_version < existing_version:
                return True
            if incoming_version > existing_version:
                return False

    existing_synced_at = _parse_iso_datetime(existing_state.get("user_last_synced_at"))
    incoming_synced_at = _parse_iso_datetime(incoming_user.get("user_last_synced_at"))
    if incoming_synced_at is None:
        incoming_synced_at = _parse_iso_datetime(generated_at)

    if existing_synced_at and incoming_synced_at and incoming_synced_at < existing_synced_at:
        return True

    return False


def validate_sync_packet(payload: dict[str, Any] | str | Path) -> dict[str, Any]:
    try:
        content = _load_payload(payload)
    except Exception as exc:  # pragma: no cover - defensive parsing path
        return {
            "ok": False,
            "errors": [f"invalid_payload: {exc}"],
        }

    errors: list[str] = []
    user = content.get("user")
    expected_user_id = user.get("user_id") if isinstance(user, dict) else None
    if not isinstance(user, dict):
        errors.append("payload.user is required and must be object")
    else:
        if not user.get("user_id"):
            errors.append("payload.user.user_id is required")

        version = user.get("user_version")
        if version is None:
            errors.append("payload.user.user_version is required")
        elif _coerce_int(version) is None:
            errors.append("payload.user.user_version must be integer")

        data_updated_at = user.get("user_data_updated_at")
        if data_updated_at is None:
            errors.append("payload.user.user_data_updated_at is required")
        elif _parse_iso_datetime(data_updated_at) is None:
            errors.append("payload.user.user_data_updated_at must be ISO-8601 datetime")

        synced_at = user.get("user_last_synced_at")
        if synced_at is not None and _parse_iso_datetime(synced_at) is None:
            errors.append("payload.user.user_last_synced_at must be ISO-8601 datetime")

    personal_information = content.get("personal_information")
    if personal_information is not None:
        if not isinstance(personal_information, dict):
            errors.append("payload.personal_information must be object when provided")
        else:
            personal_user_id = personal_information.get("user_id")
            if not personal_user_id:
                errors.append("payload.personal_information.user_id is required")
            if personal_user_id is not None and expected_user_id is not None and personal_user_id != expected_user_id:
                errors.append("payload.personal_information.user_id must match payload.user.user_id")

            pi_json = personal_information.get("personal_information_json")
            if pi_json is None:
                errors.append("payload.personal_information.personal_information_json is required")
            elif _normalize_personal_information_json(pi_json) is None:
                errors.append("payload.personal_information.personal_information_json must be valid JSON")

    meta = content.get("meta", {})
    if isinstance(meta, dict):
        generated_at = meta.get("generated_at")
        if generated_at is not None and _parse_iso_datetime(generated_at) is None:
            errors.append("payload.meta.generated_at must be ISO-8601 datetime")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "content": content,
    }


def _resolve_user_id(user_id: str | None) -> str:
    if user_id:
        return user_id

    users = db.list_users()
    if not users:
        raise ValueError("no local user found")

    active_users = [u for u in users if int(u.get("user_is_active", 0)) == 1]
    if active_users:
        active_users.sort(
            key=lambda u: (
                u.get("user_last_login") or "",
                u.get("user_created_at") or "",
            ),
            reverse=True,
        )
        return active_users[0]["user_id"]

    return users[0]["user_id"]


def _clear_user_data(user_id: str) -> None:
    sessions = db.list_sessions_by_user(user_id)
    for session in sessions:
        chats = db.list_chat_by_session(session["session_id"])
        for chat in chats:
            db.delete_chat(chat["chat_id"])

    for session in sessions:
        db.delete_session(session["session_id"])

    for row in db.list_data_by_user(user_id):
        db.delete_data(row["data_id"])

    for row in db.list_categories_by_user(user_id):
        db.delete_category(row["category_id"])

    for row in db.list_schedule_by_user(user_id):
        db.delete_schedule(row["schedule_id"])

    for row in db.list_accounts_by_user(user_id):
        db.delete_account(row["account_id"])


class LocalSyncExporter:
    def build_local_user_sync_json(
        self,
        user_id: str | None = None,
        output_path: str | Path | None = None,
    ) -> dict[str, Any]:
        target_user_id = _resolve_user_id(user_id)

        user = db.get_user(target_user_id)
        if not user:
            raise ValueError(f"local user not found: {target_user_id}")

        sync_state = _get_effective_sync_state(target_user_id, user)
        if sync_state is None:
            raise ValueError(f"sync state not found: {target_user_id}")

        user_payload = _pick(user, USER_FIELDS)
        user_payload["user_version"] = int(sync_state.get("user_version") or user_payload.get("user_version") or 1)
        user_payload["user_last_synced_at"] = sync_state.get("user_last_synced_at")
        user_payload["user_data_updated_at"] = sync_state.get("user_data_updated_at")

        sessions = db.list_sessions_by_user(target_user_id)
        session_ids = [s["session_id"] for s in sessions]

        chats: list[dict[str, Any]] = []
        for sid in session_ids:
            chats.extend(db.list_chat_by_session(sid))

        personal_information = db.get_personal_information(target_user_id)

        payload = {
            "meta": {
                "schema_version": 1,
                "source": "local",
                "generated_at": _now_iso(),
            },
            "user": user_payload,
            "personal_information": (
                _pick(personal_information, PERSONAL_INFORMATION_FIELDS)
                if personal_information is not None
                else None
            ),
            "account": [_pick(row, ACCOUNT_FIELDS) for row in db.list_accounts_by_user(target_user_id)],
            "category": [_pick(row, CATEGORY_FIELDS) for row in db.list_categories_by_user(target_user_id)],
            "data": [_pick(row, DATA_FIELDS) for row in db.list_data_by_user(target_user_id)],
            "schedule": [_pick(row, SCHEDULE_FIELDS) for row in db.list_schedule_by_user(target_user_id)],
            "session": [_pick(row, SESSION_FIELDS) for row in sessions],
            "chat": [_pick(row, CHAT_FIELDS) for row in chats],
        }

        if output_path is not None:
            path = Path(output_path)
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        return payload


class LocalSyncImporter:
    def apply_local_sync_json(self, payload: dict[str, Any] | str | Path) -> dict[str, Any]:
        validation = validate_sync_packet(payload)
        if not validation["ok"]:
            return {
                "applied": False,
                "result": "invalid_payload",
                "errors": validation["errors"],
            }

        content = validation["content"]
        meta = content.get("meta", {})
        if isinstance(meta, dict):
            source = meta.get("source")
            if source is not None and source != "server":
                return {
                    "applied": False,
                    "result": "invalid_payload",
                    "errors": ["payload.meta.source must be server for local import"],
                }

        user = content.get("user")
        if not isinstance(user, dict):
            raise ValueError("payload.user is required")

        user_id = user.get("user_id")
        if not user_id:
            raise ValueError("payload.user.user_id is required")

        with _get_user_lock(user_id):
            existing_user = db.get_user(user_id)
            existing_state = _get_effective_sync_state(user_id, existing_user) if existing_user else None
            if existing_state and _is_stale_user_payload(user, existing_state, content.get("meta", {}).get("generated_at")):
                return {
                    "applied": False,
                    "result": "discarded_stale",
                    "reason": "incoming payload is older than local state",
                }

            db.upsert_user(
                user_id=user_id,
                username=user.get("username", ""),
                user_email=user.get("user_email", ""),
                user_is_active=int(user.get("user_is_active", 1)),
                user_created_at=user.get("user_created_at", _now_iso()),
                user_last_login=user.get("user_last_login"),
                user_source_device_id=user.get("user_source_device_id"),
            )

            personal_information = content.get("personal_information")
            if "personal_information" in content and personal_information is None:
                db.delete_personal_information(user_id)
            elif isinstance(personal_information, dict):
                personal_information_json = _normalize_personal_information_json(
                    personal_information.get("personal_information_json")
                )
                if personal_information_json is not None:
                    db.upsert_personal_information(
                        user_id=user_id,
                        personal_information_json=personal_information_json,
                    )

            _clear_user_data(user_id)

            for row in content.get("account", []):
                platform = row.get("account_platform_type")
                if not platform:
                    continue
                db.create_account(
                    user_id=user_id,
                    account_platform_type=platform,
                    account_platform_username=row.get("account_platform_username", ""),
                    account_bind_time=row.get("account_bind_time"),
                    account_last_sync_time=row.get("account_last_sync_time"),
                )

            category_id_map: dict[int, int] = {}
            for row in content.get("category", []):
                if "category_id" not in row:
                    continue
                new_id = db.create_category(
                    user_id=user_id,
                    category_kind=row.get("category_kind", ""),
                    category_title=row.get("category_title", ""),
                    category_content=row.get("category_content"),
                    category_link=row.get("category_link"),
                    category_created_at=row.get("category_created_at", _now_iso()),
                )
                category_id_map[int(row["category_id"])] = new_id

            for row in content.get("data", []):
                old_category_id = row.get("data_category_id")
                if old_category_id is None:
                    continue
                new_category_id = category_id_map.get(int(old_category_id))
                if new_category_id is None:
                    continue
                db.create_data(
                    user_id=user_id,
                    data_category_id=new_category_id,
                    data_content_type=row.get("data_content_type", ""),
                    data_title=row.get("data_title", ""),
                    data_content_text=row.get("data_content_text"),
                    data_link_url=row.get("data_link_url"),
                    data_release_time=row.get("data_release_time"),
                    data_ddl_time=row.get("data_ddl_time"),
                    data_is_previewable=int(row.get("data_is_previewable", 0)),
                    data_created_at=row.get("data_created_at", _now_iso()),
                )

            for row in content.get("schedule", []):
                db.create_schedule(
                    user_id=user_id,
                    schedule_event_type=row.get("schedule_event_type", ""),
                    schedule_title=row.get("schedule_title", ""),
                    schedule_start_time=row.get("schedule_start_time", _now_iso()),
                    schedule_end_time=row.get("schedule_end_time", _now_iso()),
                    schedule_location=row.get("schedule_location"),
                    schedule_description=row.get("schedule_description"),
                    schedule_related_link=row.get("schedule_related_link"),
                    schedule_recurrence_rule=row.get("schedule_recurrence_rule"),
                    schedule_color_tag=row.get("schedule_color_tag"),
                )

            session_id_map: dict[int, int] = {}
            for row in content.get("session", []):
                if "session_id" not in row:
                    continue
                new_id = db.create_session(
                    user_id=user_id,
                    session_last_visited_at=row.get("session_last_visited_at", _now_iso()),
                )
                session_id_map[int(row["session_id"])] = new_id

            chats = sorted(content.get("chat", []), key=lambda r: r.get("chat_id", 0))
            for row in chats:
                old_session_id = row.get("session_id")
                if old_session_id is None:
                    continue
                new_session_id = session_id_map.get(int(old_session_id))
                if new_session_id is None:
                    continue
                db.create_chat(
                    session_id=new_session_id,
                    chat_role=row.get("chat_role", "user"),
                    chat_message_content=row.get("chat_message_content", ""),
                    thought_trace=row.get("thought_trace"),
                    chat_tool_calls=row.get("chat_tool_calls"),
                    chat_tokens_usage=row.get("chat_tokens_usage"),
                    chat_created_at=row.get("chat_created_at", _now_iso()),
                )

            previous_version = int(existing_state.get("user_version") or 1) if existing_state else 1
            incoming_version = _coerce_int(user.get("user_version"))
            if incoming_version is None:
                final_version = previous_version
            else:
                final_version = max(previous_version, incoming_version)

            incoming_data_updated_at = user.get("user_data_updated_at")
            if _parse_iso_datetime(incoming_data_updated_at) is not None:
                final_data_updated_at = incoming_data_updated_at
            elif existing_state is not None:
                final_data_updated_at = existing_state.get("user_data_updated_at") or _now_iso()
            else:
                final_data_updated_at = _now_iso()

            # Local marks its own completion time for pull application.
            final_synced_at = _now_iso()
            db.upsert_sync_state(
                user_id=user_id,
                user_data_updated_at=final_data_updated_at,
                user_last_synced_at=final_synced_at,
                user_version=final_version,
                sync_updated_at=final_synced_at,
            )

            return {
                "applied": True,
                "result": "applied",
                "reason": "payload applied on local",
                "user_id": user_id,
                "user_version": final_version,
                "user_last_synced_at": final_synced_at,
                "user_data_updated_at": final_data_updated_at,
            }


class LocalSyncService:
    def __init__(self) -> None:
        self._exporter = LocalSyncExporter()
        self._importer = LocalSyncImporter()

    def build_probe_packet(self, user_id: str | None = None) -> dict[str, Any]:
        target_user_id = _resolve_user_id(user_id)
        with _get_user_lock(target_user_id):
            user = db.get_user(target_user_id)
            if not user:
                return {"ok": False, "error": "user not found"}

            sync_state = _get_effective_sync_state(target_user_id, user)
            if sync_state is None:
                return {"ok": False, "error": "sync state not found"}

            return {
                "ok": True,
                "user_id": target_user_id,
                "client_user_data_updated_at": sync_state.get("user_data_updated_at"),
                "client_user_last_synced_at": sync_state.get("user_last_synced_at"),
                "client_user_version": int(sync_state.get("user_version") or 1),
                "client_device_id": user.get("user_source_device_id"),
                "client_time": _now_iso(),
            }

    def build_push_packet(self, user_id: str | None = None) -> dict[str, Any]:
        target_user_id = _resolve_user_id(user_id)
        with _get_user_lock(target_user_id):
            return self._exporter.build_local_user_sync_json(user_id=target_user_id)

    def apply_pull_packet(self, payload: dict[str, Any] | str | Path) -> dict[str, Any]:
        return self._importer.apply_local_sync_json(payload)
