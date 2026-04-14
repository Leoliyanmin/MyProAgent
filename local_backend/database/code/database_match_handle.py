from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from .database_match_operations import LocalMatchOperations
except ImportError:
    from database.code.database_match_operations import LocalMatchOperations


def _load_request(request: dict[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(request, dict):
        return request
    if isinstance(request, Path):
        return json.loads(request.read_text(encoding="utf-8"))
    if isinstance(request, str):
        try:
            return json.loads(request)
        except json.JSONDecodeError:
            return json.loads(Path(request).read_text(encoding="utf-8"))
    raise TypeError("request must be dict, json string, or file path")


def _error(status: int, error_code: str, message: str, details: Any = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": False,
        "status": status,
        "error_code": error_code,
        "message": message,
    }
    if details is not None:
        payload["details"] = details
    return payload


class LocalMatchHandle:
    """Local entry for profile JSON storage and synced match results."""

    def __init__(self) -> None:
        self.operations = LocalMatchOperations()

    def upsert_profile(
        self,
        user_id: str,
        profile_json: Any,
        is_open: Any = 1,
        last_match_time: Any = None,
    ) -> dict[str, Any]:
        if not user_id:
            return _error(400, "MATCH_INVALID_ARGUMENT", "user_id is required")
        if profile_json is None:
            return _error(400, "MATCH_INVALID_ARGUMENT", "profile_json is required")

        try:
            profile = self.operations.upsert_profile_json(
                user_id=user_id,
                profile_json=profile_json,
                is_open=is_open,
                last_match_time=last_match_time,
            )
            return {
                "ok": True,
                "status": 200,
                "data": profile,
            }
        except ValueError as exc:
            return _error(422, "MATCH_PROFILE_INVALID", str(exc))
        except Exception as exc:  # pragma: no cover - defensive path
            return _error(500, "MATCH_INTERNAL_ERROR", f"upsert profile failed: {exc}")

    def get_profile(self, user_id: str) -> dict[str, Any]:
        if not user_id:
            return _error(400, "MATCH_INVALID_ARGUMENT", "user_id is required")

        try:
            profile = self.operations.get_profile(user_id)
            if profile is None:
                return _error(404, "MATCH_PROFILE_NOT_FOUND", f"Profile not found: {user_id}")
            return {
                "ok": True,
                "status": 200,
                "data": profile,
            }
        except Exception as exc:  # pragma: no cover - defensive path
            return _error(500, "MATCH_INTERNAL_ERROR", f"get profile failed: {exc}")

    def set_profile_open(self, user_id: str, is_open: Any) -> dict[str, Any]:
        if not user_id:
            return _error(400, "MATCH_INVALID_ARGUMENT", "user_id is required")

        try:
            profile = self.operations.set_profile_open(user_id=user_id, is_open=is_open)
            return {
                "ok": True,
                "status": 200,
                "data": profile,
            }
        except ValueError as exc:
            message = str(exc)
            if message.startswith("Profile not found"):
                return _error(404, "MATCH_PROFILE_NOT_FOUND", message)
            return _error(422, "MATCH_PROFILE_INVALID", message)
        except Exception as exc:  # pragma: no cover - defensive path
            return _error(500, "MATCH_INTERNAL_ERROR", f"set profile open failed: {exc}")

    def delete_profile(self, user_id: str) -> dict[str, Any]:
        if not user_id:
            return _error(400, "MATCH_INVALID_ARGUMENT", "user_id is required")

        try:
            deleted = self.operations.delete_profile(user_id)
            if not deleted:
                return _error(404, "MATCH_PROFILE_NOT_FOUND", f"Profile not found: {user_id}")
            return {
                "ok": True,
                "status": 200,
                "message": "profile deleted",
            }
        except Exception as exc:  # pragma: no cover - defensive path
            return _error(500, "MATCH_INTERNAL_ERROR", f"delete profile failed: {exc}")

    def list_matches(self, user_id: str) -> dict[str, Any]:
        if not user_id:
            return _error(400, "MATCH_INVALID_ARGUMENT", "user_id is required")

        try:
            rows = self.operations.list_match_results(user_id)
            return {
                "ok": True,
                "status": 200,
                "data": rows,
            }
        except Exception as exc:  # pragma: no cover - defensive path
            return _error(500, "MATCH_INTERNAL_ERROR", f"list matches failed: {exc}")

    def handle(self, action: str, payload: Any = None) -> dict[str, Any]:
        action_name = (action or "").strip().lower()

        if action_name in {"upsert_profile", "upsert_profile_json", "save_profile"}:
            if not isinstance(payload, dict):
                return _error(400, "MATCH_INVALID_ARGUMENT", "payload must be object")
            return self.upsert_profile(
                user_id=str(payload.get("user_id") or ""),
                profile_json=payload.get("profile_json", payload.get("answers")),
                is_open=payload.get("is_open", 1),
                last_match_time=payload.get("last_match_time"),
            )

        if action_name in {"get_profile"}:
            if isinstance(payload, dict):
                user_id = payload.get("user_id")
            else:
                user_id = payload
            return self.get_profile(str(user_id or ""))

        if action_name in {"set_profile_open", "open_profile"}:
            if not isinstance(payload, dict):
                return _error(400, "MATCH_INVALID_ARGUMENT", "payload must be object")
            return self.set_profile_open(
                user_id=str(payload.get("user_id") or ""),
                is_open=payload.get("is_open"),
            )

        if action_name in {"delete_profile"}:
            if isinstance(payload, dict):
                user_id = payload.get("user_id")
            else:
                user_id = payload
            return self.delete_profile(str(user_id or ""))

        if action_name in {"list_matches", "get_matches"}:
            if isinstance(payload, dict):
                user_id = payload.get("user_id")
            else:
                user_id = payload
            return self.list_matches(str(user_id or ""))

        return _error(400, "MATCH_ACTION_INVALID", f"unsupported action: {action}")


def handle_match_request(request: dict[str, Any] | str | Path) -> dict[str, Any]:
    content = _load_request(request)
    action = content.get("action")
    if not action:
        return _error(400, "MATCH_ACTION_REQUIRED", "action is required")

    handler = LocalMatchHandle()
    return handler.handle(action=str(action), payload=content.get("payload"))
