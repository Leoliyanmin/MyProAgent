from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..command import database_command as db

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

USER_MATCH_PROFILE_FIELDS = (
    "user_id",
    "answers",
    "is_open",
    "last_match_time",
)

MATCH_RESULT_FIELDS = (
    "id",
    "user_id",
    "matched_user_id",
    "similarity_score",
    "created_at",
    "is_shared",
)

ACCOUNT_FIELDS = (
    "account_id",
    "user_id",
    "account_platform_type",
    "account_platform_username",
    "content",
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
    "data_classification_code",
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
    "schedule_priority",
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


def _coerce_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_binary_flag(value: Any) -> int | None:
    normalized = _coerce_int(value)
    if normalized in (0, 1):
        return normalized
    return None


def _normalize_data_classification_code(value: Any) -> int | None:
    normalized = _coerce_int(value)
    if normalized in (1, 2, 3):
        return normalized
    return None


def _default_data_classification_code(data_content_type: Any) -> int:
    if isinstance(data_content_type, str) and data_content_type.lower() == "task":
        return 3
    return 1


def _normalize_schedule_priority(value: Any) -> int:
    normalized = _coerce_int(value)
    if normalized in (0, 1, 2, 3):
        return normalized
    return 2


def _normalize_answers_json(value: Any) -> str | None:
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

    user_match_profile = content.get("user_match_profile")
    if "user_match_profile" in content and user_match_profile is not None:
        if not isinstance(user_match_profile, dict):
            errors.append("payload.user_match_profile must be object when provided")
        else:
            profile_user_id = user_match_profile.get("user_id")
            if not profile_user_id:
                errors.append("payload.user_match_profile.user_id is required")
            if profile_user_id is not None and expected_user_id is not None and profile_user_id != expected_user_id:
                errors.append("payload.user_match_profile.user_id must match payload.user.user_id")

            answers = user_match_profile.get("answers")
            if answers is None:
                errors.append("payload.user_match_profile.answers is required")
            elif _normalize_answers_json(answers) is None:
                errors.append("payload.user_match_profile.answers must be valid JSON")

            is_open = user_match_profile.get("is_open")
            if is_open is not None and _normalize_binary_flag(is_open) is None:
                errors.append("payload.user_match_profile.is_open must be 0 or 1")

            last_match_time = user_match_profile.get("last_match_time")
            if last_match_time is not None and _parse_iso_datetime(last_match_time) is None:
                errors.append("payload.user_match_profile.last_match_time must be ISO-8601 datetime")

    match_results = content.get("match_result")
    if "match_result" in content and match_results is not None:
        if not isinstance(match_results, list):
            errors.append("payload.match_result must be list when provided")
        else:
            for index, row in enumerate(match_results):
                prefix = f"payload.match_result[{index}]"
                if not isinstance(row, dict):
                    errors.append(f"{prefix} must be object")
                    continue

                row_user_id = row.get("user_id")
                if not row_user_id:
                    errors.append(f"{prefix}.user_id is required")
                elif expected_user_id is not None and row_user_id != expected_user_id:
                    errors.append(f"{prefix}.user_id must match payload.user.user_id")

                if not row.get("matched_user_id"):
                    errors.append(f"{prefix}.matched_user_id is required")

                if row.get("similarity_score") is None:
                    errors.append(f"{prefix}.similarity_score is required")
                elif _coerce_float(row.get("similarity_score")) is None:
                    errors.append(f"{prefix}.similarity_score must be numeric")

                created_at = row.get("created_at")
                if created_at is None:
                    errors.append(f"{prefix}.created_at is required")
                elif _parse_iso_datetime(created_at) is None:
                    errors.append(f"{prefix}.created_at must be ISO-8601 datetime")

                is_shared = row.get("is_shared")
                if is_shared is not None and _normalize_binary_flag(is_shared) is None:
                    errors.append(f"{prefix}.is_shared must be 0 or 1")

    data_rows = content.get("data")
    if "data" in content and data_rows is not None:
        if not isinstance(data_rows, list):
            errors.append("payload.data must be list when provided")
        else:
            for index, row in enumerate(data_rows):
                prefix = f"payload.data[{index}]"
                if not isinstance(row, dict):
                    errors.append(f"{prefix} must be object")
                    continue

                data_classification_code = row.get("data_classification_code")
                if (
                    data_classification_code is not None
                    and _normalize_data_classification_code(data_classification_code) is None
                ):
                    errors.append(f"{prefix}.data_classification_code must be one of 1, 2, 3")

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


def _is_stale_user_payload(
    incoming_user: dict[str, Any],
    existing_user: dict[str, Any],
    generated_at: Any,
) -> bool:
    existing_version = int(existing_user.get("user_version") or 0)
    incoming_version_raw = incoming_user.get("user_version")

    if incoming_version_raw is not None:
        try:
            incoming_version = int(incoming_version_raw)
        except (TypeError, ValueError):
            incoming_version = existing_version

        if incoming_version < existing_version:
            return True

        if incoming_version > existing_version:
            return False

    existing_synced_at = _parse_iso_datetime(existing_user.get("user_last_synced_at"))
    incoming_synced_at = _parse_iso_datetime(incoming_user.get("user_last_synced_at"))
    if incoming_synced_at is None:
        incoming_synced_at = _parse_iso_datetime(generated_at)

    if existing_synced_at and incoming_synced_at and incoming_synced_at < existing_synced_at:
        return True

    return False


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


class ServerSyncExporter:
    def build_user_sync_json(self, user_id: str, output_path: str | Path | None = None) -> dict[str, Any]:
        user = db.get_user(user_id)
        if not user:
            raise ValueError(f"user not found: {user_id}")

        sync_state = _get_effective_sync_state(user_id, user)
        if sync_state is None:
            raise ValueError(f"sync state not found: {user_id}")

        user_payload = _pick(user, USER_FIELDS)
        user_payload["user_version"] = int(sync_state.get("user_version") or user_payload.get("user_version") or 1)
        user_payload["user_last_synced_at"] = sync_state.get("user_last_synced_at")
        user_payload["user_data_updated_at"] = sync_state.get("user_data_updated_at")

        sessions = db.list_sessions_by_user(user_id)
        session_ids = [s["session_id"] for s in sessions]

        chats: list[dict[str, Any]] = []
        for sid in session_ids:
            chats.extend(db.list_chat_by_session(sid))

        user_match_profile = db.get_user_match_profile(user_id)
        match_results = db.list_match_results_by_user(user_id)

        payload = {
            "meta": {
                "schema_version": 1,
                "source": "server",
                "generated_at": _now_iso(),
            },
            "user": user_payload,
            "user_match_profile": (
                _pick(user_match_profile, USER_MATCH_PROFILE_FIELDS)
                if user_match_profile is not None
                else None
            ),
            "match_result": [_pick(row, MATCH_RESULT_FIELDS) for row in match_results],
            "account": [_pick(row, ACCOUNT_FIELDS) for row in db.list_accounts_by_user(user_id)],
            "category": [_pick(row, CATEGORY_FIELDS) for row in db.list_categories_by_user(user_id)],
            "data": [_pick(row, DATA_FIELDS) for row in db.list_data_by_user(user_id)],
            "schedule": [_pick(row, SCHEDULE_FIELDS) for row in db.list_schedule_by_user(user_id)],
            "session": [_pick(row, SESSION_FIELDS) for row in sessions],
            "chat": [_pick(row, CHAT_FIELDS) for row in chats],
        }

        if output_path is not None:
            path = Path(output_path)
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        return payload

class ServerSyncImporter:
    def apply_user_sync_json(self, payload: dict[str, Any] | str | Path) -> dict[str, Any]:
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
            if source is not None and source != "local":
                return {
                    "applied": False,
                    "result": "invalid_payload",
                    "errors": ["payload.meta.source must be local for server import"],
                }

        user = content.get("user")
        if not isinstance(user, dict):
            raise ValueError("payload.user is required")

        user_id = user.get("user_id")
        if not user_id:
            raise ValueError("payload.user.user_id is required")

        with _get_user_lock(user_id):
            existing_user = db.get_user(user_id)
            if not existing_user:
                raise ValueError("server user not found; cannot apply sync without existing credentials")

            sync_state = _get_effective_sync_state(user_id, existing_user)
            if sync_state is None:
                raise ValueError("server sync state is unavailable")

            if _is_stale_user_payload(user, sync_state, content.get("meta", {}).get("generated_at")):
                return {
                    "applied": False,
                    "result": "discarded_stale",
                    "reason": "incoming payload is older than server state",
                }

            existing_accounts = {
                row["account_platform_type"]: row for row in db.list_accounts_by_user(user_id)
            }

            db.upsert_user(
                user_id=user_id,
                username=user.get("username", existing_user["username"]),
                user_email=user.get("user_email", existing_user["user_email"]),
                user_password_hash=existing_user["user_password_hash"],
                user_salt=existing_user["user_salt"],
                user_is_active=int(user.get("user_is_active", existing_user["user_is_active"])),
                user_created_at=user.get("user_created_at", existing_user["user_created_at"]),
                user_last_login=user.get("user_last_login", existing_user.get("user_last_login")),
                user_auto_login_token=existing_user.get("user_auto_login_token"),
                user_source_device_id=user.get("user_source_device_id", existing_user.get("user_source_device_id")),
            )

            user_match_profile = content.get("user_match_profile")
            if "user_match_profile" in content and user_match_profile is None:
                db.delete_user_match_profile(user_id)
            elif isinstance(user_match_profile, dict):
                answers = _normalize_answers_json(user_match_profile.get("answers"))
                is_open = _normalize_binary_flag(user_match_profile.get("is_open"))
                if is_open is None:
                    is_open = 0
                last_match_time = user_match_profile.get("last_match_time")
                if _parse_iso_datetime(last_match_time) is None:
                    last_match_time = None
                if answers is not None:
                    db.upsert_user_match_profile(
                        user_id=user_id,
                        answers=answers,
                        is_open=is_open,
                        last_match_time=last_match_time,
                    )

            if "match_result" in content:
                db.delete_match_results_by_user(user_id)
                match_results = content.get("match_result")
                if isinstance(match_results, list):
                    for row in match_results:
                        if not isinstance(row, dict):
                            continue
                        if row.get("matched_user_id") is None:
                            continue
                        similarity_score = _coerce_float(row.get("similarity_score"))
                        if similarity_score is None:
                            continue
                        created_at = row.get("created_at")
                        if _parse_iso_datetime(created_at) is None:
                            continue
                        is_shared = _normalize_binary_flag(row.get("is_shared"))
                        if is_shared is None:
                            is_shared = 0
                        db.create_match_result(
                            user_id=user_id,
                            matched_user_id=str(row.get("matched_user_id")),
                            similarity_score=similarity_score,
                            created_at=created_at,
                            is_shared=is_shared,
                        )

            _clear_user_data(user_id)

            for row in content.get("account", []):
                platform = row.get("account_platform_type")
                if not platform:
                    continue
                secrets = existing_accounts.get(platform, {})
                db.create_account(
                    user_id=user_id,
                    account_platform_type=platform,
                    account_platform_username=row.get("account_platform_username", ""),
                    content=row.get("content"),
                    account_mail_password=secrets.get("account_mail_password"),
                    account_cookie=secrets.get("account_cookie"),
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
                normalized_data_classification = _normalize_data_classification_code(
                    row.get("data_classification_code")
                )
                if normalized_data_classification is None:
                    normalized_data_classification = _default_data_classification_code(
                        row.get("data_content_type")
                    )
                db.create_data(
                    user_id=user_id,
                    data_category_id=new_category_id,
                    data_content_type=row.get("data_content_type", ""),
                    data_classification_code=normalized_data_classification,
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
                    schedule_priority=_normalize_schedule_priority(row.get("schedule_priority")),
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

            incoming_version = _coerce_int(user.get("user_version"))
            current_version = int(sync_state.get("user_version") or 1)
            if incoming_version is None:
                final_version = current_version
            else:
                final_version = max(current_version, incoming_version)

            incoming_data_updated_at = user.get("user_data_updated_at")
            if _parse_iso_datetime(incoming_data_updated_at) is not None:
                final_data_updated_at = incoming_data_updated_at
            else:
                final_data_updated_at = sync_state.get("user_data_updated_at") or _now_iso()

            # Server owns sync timestamps after a successful push apply.
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
                "reason": "payload applied on server",
                "user_id": user_id,
                "server_user_version": final_version,
                "server_user_last_synced_at": final_synced_at,
                "server_user_data_updated_at": final_data_updated_at,
                "user_version": final_version,
                "user_last_synced_at": final_synced_at,
                "user_data_updated_at": final_data_updated_at,
            }


class ServerSyncService:
    def __init__(self) -> None:
        self._exporter = ServerSyncExporter()
        self._importer = ServerSyncImporter()

    def probe_action(self, probe_packet: dict[str, Any] | str | Path) -> dict[str, Any]:
        content = _load_payload(probe_packet)
        user_id = content.get("user_id")
        if not user_id:
            return {"ok": False, "error": "user_id is required"}

        with _get_user_lock(user_id):
            user = db.get_user(user_id)
            if not user:
                return {"ok": False, "error": "user not found"}

            sync_state = _get_effective_sync_state(user_id, user)
            if sync_state is None:
                return {"ok": False, "error": "sync state not found"}

            server_updated = _parse_iso_datetime(sync_state.get("user_data_updated_at"))
            server_version = int(sync_state.get("user_version") or 1)

            client_updated = _parse_iso_datetime(content.get("client_user_data_updated_at"))
            client_synced = _parse_iso_datetime(content.get("client_user_last_synced_at"))
            client_version = _coerce_int(content.get("client_user_version"))

            if client_synced is None and client_version is None:
                return {
                    "ok": True,
                    "action": "pull",
                    "reason": "missing sync baseline on client",
                    "server_user_version": server_version,
                    "server_user_data_updated_at": sync_state.get("user_data_updated_at"),
                    "server_user_last_synced_at": sync_state.get("user_last_synced_at"),
                    "server_time": _now_iso(),
                }

            if client_synced is not None and server_updated is not None and server_updated <= client_synced:
                server_changed = False
            else:
                server_changed = server_updated is not None

            if client_synced is not None and client_updated is not None and client_updated <= client_synced:
                client_changed = False
            else:
                client_changed = client_updated is not None

            action = "noop"
            reason = "both sides unchanged"
            if server_changed and not client_changed:
                action = "pull"
                reason = "server has newer data"
            elif client_changed and not server_changed:
                action = "push"
                reason = "client has newer data"
            elif client_changed and server_changed:
                action = "conflict"
                reason = "both sides changed after last sync"

            if not server_changed and not client_changed and client_version is not None:
                if client_version < server_version:
                    action = "pull"
                    reason = "server version is newer"
                elif client_version > server_version:
                    action = "push"
                    reason = "client version is newer"

            return {
                "ok": True,
                "action": action,
                "reason": reason,
                "server_user_version": server_version,
                "server_user_data_updated_at": sync_state.get("user_data_updated_at"),
                "server_user_last_synced_at": sync_state.get("user_last_synced_at"),
                "server_time": _now_iso(),
            }

    def build_pull_packet(self, user_id: str) -> dict[str, Any]:
        with _get_user_lock(user_id):
            return self._exporter.build_user_sync_json(user_id)

    def apply_push_packet(self, payload: dict[str, Any] | str | Path) -> dict[str, Any]:
        return self._importer.apply_user_sync_json(payload)
