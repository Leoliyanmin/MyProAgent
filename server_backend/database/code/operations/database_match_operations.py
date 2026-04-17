from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from typing import Any

from server_backend.database.code.command import database_command as db

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


def _parse_iso_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _normalize_profile_json(value: Any) -> str:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid profile_json: {exc}") from None
        return json.dumps(parsed, ensure_ascii=False)

    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)

    raise ValueError("profile_json must be JSON object, list, or JSON string")


def _deserialize_profile_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _normalize_binary_flag(value: Any, default: int = 0) -> int:
    if value is None:
        return default

    try:
        normalized = int(value)
    except (TypeError, ValueError):
        raise ValueError("is_open must be 0 or 1") from None

    if normalized not in (0, 1):
        raise ValueError("is_open must be 0 or 1")

    return normalized


class ServerMatchOperations:
    """Server-side database operations for profile and match result persistence."""

    def upsert_profile_json(
        self,
        user_id: str,
        profile_json: Any,
        is_open: Any = 1,
        last_match_time: Any = None,
        touch_sync_state: bool = True,
    ) -> dict[str, Any]:
        with _get_user_lock(user_id):
            self._require_user(user_id)

            answers = _normalize_profile_json(profile_json)
            open_flag = _normalize_binary_flag(is_open, default=1)
            normalized_last_match_time = None
            if last_match_time is not None:
                if isinstance(last_match_time, datetime):
                    normalized_last_match_time = last_match_time.isoformat()
                elif _parse_iso_datetime(last_match_time) is not None:
                    normalized_last_match_time = str(last_match_time)
                else:
                    raise ValueError("last_match_time must be ISO-8601 datetime")

            db.upsert_user_match_profile(
                user_id=user_id,
                answers=answers,
                is_open=open_flag,
                last_match_time=normalized_last_match_time,
            )

            if touch_sync_state:
                self._bump_sync_state(user_id)

            profile = db.get_user_match_profile(user_id)
            if profile is None:
                raise ValueError("profile upsert failed")
            return self._format_profile(profile)

    def get_profile(self, user_id: str) -> dict[str, Any] | None:
        with _get_user_lock(user_id):
            profile = db.get_user_match_profile(user_id)
            if profile is None:
                return None
            return self._format_profile(profile)

    def set_profile_open(self, user_id: str, is_open: Any, touch_sync_state: bool = True) -> dict[str, Any]:
        with _get_user_lock(user_id):
            profile = db.get_user_match_profile(user_id)
            if profile is None:
                raise ValueError(f"Profile not found: {user_id}")

            open_flag = _normalize_binary_flag(is_open)
            db.update_user_match_profile_open(user_id, open_flag)
            if touch_sync_state:
                self._bump_sync_state(user_id)

            updated = db.get_user_match_profile(user_id)
            if updated is None:
                raise ValueError(f"Profile not found: {user_id}")
            return self._format_profile(updated)

    def delete_profile(self, user_id: str, touch_sync_state: bool = True) -> bool:
        with _get_user_lock(user_id):
            profile = db.get_user_match_profile(user_id)
            if profile is None:
                return False

            db.delete_user_match_profile(user_id)
            db.delete_match_results_by_user(user_id)
            if touch_sync_state:
                self._bump_sync_state(user_id)
            return True

    def list_match_results(self, user_id: str) -> list[dict]:
        with _get_user_lock(user_id):
            return db.list_match_results_by_user(user_id)

    def replace_match_results(
        self,
        user_id: str,
        matches: list[dict[str, Any]],
        generated_at: str | None = None,
        touch_sync_state: bool = True,
    ) -> dict[str, Any]:
        with _get_user_lock(user_id):
            self._require_user(user_id)

            if generated_at is None:
                normalized_generated_at = _now_iso()
            elif _parse_iso_datetime(generated_at) is not None:
                normalized_generated_at = generated_at
            else:
                raise ValueError("generated_at must be ISO-8601 datetime")

            db.delete_match_results_by_user(user_id)

            for row in matches:
                if not isinstance(row, dict):
                    raise ValueError("matches must contain objects")

                matched_user_id = row.get("matched_user_id")
                if not matched_user_id:
                    raise ValueError("matched_user_id is required")

                try:
                    similarity_score = float(row.get("similarity_score"))
                except (TypeError, ValueError):
                    raise ValueError("similarity_score must be numeric") from None

                is_shared = _normalize_binary_flag(row.get("is_shared"), default=0)
                db.create_match_result(
                    user_id=user_id,
                    matched_user_id=str(matched_user_id),
                    similarity_score=similarity_score,
                    created_at=normalized_generated_at,
                    is_shared=is_shared,
                )

            profile = db.get_user_match_profile(user_id)
            if profile is not None:
                db.update_user_match_profile_last_match_time(user_id, normalized_generated_at)

            if touch_sync_state:
                self._bump_sync_state(user_id)

            persisted_matches = db.list_match_results_by_user(user_id)
            return {
                "user_id": user_id,
                "matched_count": len(persisted_matches),
                "matches": persisted_matches,
                "generated_at": normalized_generated_at,
                "result": "matches_replaced",
            }

    def get_sync_state(self, user_id: str) -> dict[str, Any] | None:
        return db.get_sync_state(user_id)

    def _format_profile(self, profile_row: dict[str, Any]) -> dict[str, Any]:
        data = dict(profile_row)
        data["profile_json"] = _deserialize_profile_json(profile_row.get("answers"))
        return data

    def _require_user(self, user_id: str) -> None:
        if db.get_user(user_id) is None:
            raise ValueError(f"User not found: {user_id}")

    def _bump_sync_state(self, user_id: str) -> None:
        now = _now_iso()
        sync_state = db.get_sync_state(user_id)

        if sync_state is None:
            db.upsert_sync_state(
                user_id=user_id,
                user_data_updated_at=now,
                user_last_synced_at=None,
                user_version=1,
                sync_updated_at=now,
            )
            return

        current_version = int(sync_state.get("user_version") or 1)
        db.upsert_sync_state(
            user_id=user_id,
            user_data_updated_at=now,
            user_last_synced_at=sync_state.get("user_last_synced_at"),
            user_version=current_version + 1,
            sync_updated_at=now,
        )
