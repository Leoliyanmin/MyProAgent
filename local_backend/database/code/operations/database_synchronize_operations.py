from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..command import database_command as db


def _get_fernet():
    import hashlib
    import base64
    from cryptography.fernet import Fernet
    from local_backend.config import settings
    key = settings.ENCRYPTION_KEY.encode("utf-8")
    derived = base64.urlsafe_b64encode(hashlib.sha256(key).digest())
    return Fernet(derived)


def _encrypt_personality(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return _get_fernet().encrypt(payload.encode("utf-8")).decode("utf-8")


def _decrypt_personality(encrypted: str) -> dict:
    try:
        decrypted = _get_fernet().decrypt(encrypted.encode("utf-8")).decode("utf-8")
        return json.loads(decrypted)
    except Exception:
        return {}

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

EVENT_FIELDS = (
    "event_id",
    "user_id",
    "event_title",
    "event_type",
    "event_source",
    "event_start_time",
    "event_end_time",
    "event_location",
    "event_description",
    "event_link_url",
    "event_is_completed",
    "event_show_in_todo",
    "event_priority",
    "event_color_tag",
    "event_meta_json",
    "event_created_at",
    "event_updated_at",
)

SESSION_FIELDS = (
    "session_id",
    "user_id",
    "session_title",
    "session_created_at",
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

USER_PERSONALITY_FIELDS = (
    "user_id",
    "interests_json",
    "skills_json",
    "preferences_json",
    "study_work_patterns_json",
    "personality_indicators_json",
    "mbti_type",
    "mbti_scores_json",
    "mbti_confidence",
    "mbti_description",
    "interaction_count",
    "mbti_last_updated",
    "last_updated",
)


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

    for row in db.list_events_by_user(user_id):
        db.delete_event(row["event_id"])

    for row in db.list_accounts_by_user(user_id):
        db.delete_account(row["account_id"])

    try:
        db.delete_user_personality(user_id)
    except Exception:
        pass


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

        user_match_profile = db.get_user_match_profile(target_user_id)
        match_results = db.list_match_results_by_user(target_user_id)

        payload = {
            "meta": {
                "schema_version": 1,
                "source": "local",
                "generated_at": _now_iso(),
            },
            "user": user_payload,
            "user_match_profile": (
                _pick(user_match_profile, USER_MATCH_PROFILE_FIELDS)
                if user_match_profile is not None
                else None
            ),
            "match_result": [_pick(row, MATCH_RESULT_FIELDS) for row in match_results],
            "account": [_pick(row, ACCOUNT_FIELDS) for row in db.list_accounts_by_user(target_user_id)],
            "event": [_pick(row, EVENT_FIELDS) for row in db.list_events_by_user(target_user_id)],
            "session": [_pick(row, SESSION_FIELDS) for row in sessions],
            "chat": [_pick(row, CHAT_FIELDS) for row in chats],
            "user_personality": (
                {"encrypted_data": _encrypt_personality(_pick(row, USER_PERSONALITY_FIELDS))}
                if (row := db.get_user_personality(target_user_id))
                else None
            ),
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

            _clear_user_data(user_id)

            for row in content.get("account", []):
                platform = row.get("account_platform_type")
                if not platform:
                    continue
                db.create_account(
                    user_id=user_id,
                    account_platform_type=platform,
                    account_platform_username=row.get("account_platform_username", ""),
                    content=row.get("content"),
                    account_bind_time=row.get("account_bind_time"),
                    account_last_sync_time=row.get("account_last_sync_time"),
                )

            for row in content.get("event", []):
                db.create_event(
                    user_id=user_id,
                    event_title=row.get("event_title", ""),
                    event_type=row.get("event_type", "manual"),
                    event_source=row.get("event_source", "manual"),
                    event_start_time=row.get("event_start_time"),
                    event_end_time=row.get("event_end_time"),
                    event_location=row.get("event_location"),
                    event_description=row.get("event_description"),
                    event_link_url=row.get("event_link_url"),
                    event_is_completed=int(row.get("event_is_completed", 0)),
                    event_show_in_todo=int(row.get("event_show_in_todo", 1)),
                    event_priority=int(row.get("event_priority", 2)),
                    event_color_tag=row.get("event_color_tag", "#007aff"),
                    event_meta_json=row.get("event_meta_json"),
                    event_created_at=row.get("event_created_at", _now_iso()),
                )

            session_id_map: dict[int, int] = {}
            for row in content.get("session", []):
                if "session_id" not in row:
                    continue
                new_id = db.create_session(
                    user_id=user_id,
                    session_title=row.get("session_title", ""),
                    session_created_at=row.get("session_created_at") or row.get("session_last_visited_at", _now_iso()),
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

            personality_row = content.get("user_personality")
            if personality_row and isinstance(personality_row, dict):
                encrypted = personality_row.get("encrypted_data")
                if encrypted:
                    data = _decrypt_personality(encrypted)
                    if data:
                        db.upsert_user_personality(
                            user_id=user_id,
                            interests_json=data.get("interests_json"),
                            skills_json=data.get("skills_json"),
                            preferences_json=data.get("preferences_json"),
                            study_work_patterns_json=data.get("study_work_patterns_json"),
                            personality_indicators_json=data.get("personality_indicators_json"),
                            mbti_type=data.get("mbti_type"),
                            mbti_scores_json=data.get("mbti_scores_json"),
                            mbti_confidence=data.get("mbti_confidence"),
                            mbti_description=data.get("mbti_description"),
                            interaction_count=data.get("interaction_count"),
                            mbti_last_updated=data.get("mbti_last_updated"),
                        )
                else:
                    db.upsert_user_personality(
                        user_id=user_id,
                        interests_json=personality_row.get("interests_json"),
                        skills_json=personality_row.get("skills_json"),
                        preferences_json=personality_row.get("preferences_json"),
                        study_work_patterns_json=personality_row.get("study_work_patterns_json"),
                        personality_indicators_json=personality_row.get("personality_indicators_json"),
                        mbti_type=personality_row.get("mbti_type"),
                        mbti_scores_json=personality_row.get("mbti_scores_json"),
                        mbti_confidence=personality_row.get("mbti_confidence"),
                        mbti_description=personality_row.get("mbti_description"),
                        interaction_count=personality_row.get("interaction_count"),
                        mbti_last_updated=personality_row.get("mbti_last_updated"),
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
