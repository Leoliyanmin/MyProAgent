from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from . import database_command as db
    from . import database_synchronize_operations as ops
except ImportError:
    import database_command as db
    import database_synchronize_operations as ops


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


def _coerce_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _resolve_local_user_id(explicit_user_id: Any) -> str | None:
    if isinstance(explicit_user_id, str) and explicit_user_id:
        return explicit_user_id

    users = db.list_users()
    if not users:
        return None

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


class LocalSyncHandle:
    def __init__(self) -> None:
        self._service = ops.LocalSyncService()
        self._sync_lock = threading.RLock()

    def build_probe(self, user_id: str | None = None) -> dict[str, Any]:
        with self._sync_lock:
            result = self._service.build_probe_packet(user_id=user_id)
            if not result.get("ok"):
                message = result.get("error", "build probe failed")
                if message == "user not found":
                    return _error(404, "SYNC_USER_NOT_FOUND", message)
                return _error(400, "SYNC_PROBE_INVALID", message)

            return {
                "ok": True,
                "status": 200,
                "payload": result,
            }

    def resolve_probe_result(self, server_probe_response: dict[str, Any]) -> dict[str, Any]:
        action = server_probe_response.get("action")
        if action not in {"noop", "pull", "push", "conflict"}:
            return _error(422, "SYNC_PROBE_RESPONSE_INVALID", "invalid probe action", server_probe_response)

        if action == "noop":
            return {
                "ok": True,
                "status": 200,
                "next_step": "noop",
                "reason": server_probe_response.get("reason", "both sides unchanged"),
            }

        if action == "pull":
            return {
                "ok": True,
                "status": 200,
                "next_step": "pull",
                "reason": server_probe_response.get("reason", "server has newer data"),
            }

        if action == "push":
            return {
                "ok": True,
                "status": 200,
                "next_step": "push",
                "reason": server_probe_response.get("reason", "client has newer data"),
            }

        # conflict
        return {
            "ok": True,
            "status": 200,
            "next_step": "pull",
            "reason": server_probe_response.get("reason", "conflict detected; prefer pull first"),
            "conflict": True,
        }

    def build_push(self, user_id: str | None = None) -> dict[str, Any]:
        with self._sync_lock:
            try:
                payload = self._service.build_push_packet(user_id=user_id)
            except ValueError as exc:
                return _error(404, "SYNC_USER_NOT_FOUND", str(exc))

            return {
                "ok": True,
                "status": 200,
                "payload": payload,
            }

    def apply_pull(self, pull_payload: dict[str, Any] | str | Path) -> dict[str, Any]:
        with self._sync_lock:
            validation = ops.validate_sync_packet(pull_payload)
            if not validation.get("ok"):
                return _error(422, "SYNC_PAYLOAD_INVALID", "pull payload validation failed", validation.get("errors"))

            result = self._service.apply_pull_packet(validation["content"])
            outcome = result.get("result")

            if outcome == "invalid_payload":
                return _error(422, "SYNC_PAYLOAD_INVALID", "pull payload validation failed", result.get("errors"))

            if outcome == "discarded_stale":
                return {
                    "ok": True,
                    "status": 200,
                    **result,
                }

            if outcome == "applied":
                return {
                    "ok": True,
                    "status": 200,
                    **result,
                }

            return _error(500, "SYNC_INTERNAL_ERROR", "unknown pull result", result)

    def apply_server_ack(self, ack_payload: dict[str, Any] | str | Path) -> dict[str, Any]:
        with self._sync_lock:
            try:
                payload = _load_request(ack_payload)
            except Exception as exc:
                return _error(422, "SYNC_PAYLOAD_INVALID", "ack payload parsing failed", str(exc))

            user_id = _resolve_local_user_id(payload.get("user_id"))
            if not user_id:
                return _error(400, "SYNC_USER_ID_REQUIRED", "user_id is required")

            user = db.get_user(user_id)
            if not user:
                return _error(404, "SYNC_USER_NOT_FOUND", "user not found")

            state = db.get_sync_state(user_id)
            if state is None:
                state = {
                    "user_version": 1,
                    "user_data_updated_at": user.get("user_last_login") or user.get("user_created_at") or _now_iso(),
                }

            final_synced_at = payload.get("server_user_last_synced_at")
            if _parse_iso_datetime(final_synced_at) is None:
                return _error(422, "SYNC_TIME_INVALID", "server_user_last_synced_at must be ISO-8601 datetime")

            server_user_version_raw = payload.get("server_user_version")
            server_user_version = None
            if server_user_version_raw is not None:
                server_user_version = _coerce_int(server_user_version_raw)
                if server_user_version is None:
                    return _error(412, "SYNC_VERSION_INVALID", "server_user_version must be integer")

            server_data_updated_at = payload.get("server_user_data_updated_at")
            if server_data_updated_at is not None and _parse_iso_datetime(server_data_updated_at) is None:
                return _error(422, "SYNC_TIME_INVALID", "server_user_data_updated_at must be ISO-8601 datetime")

            current_version = int(state.get("user_version") or 1)
            if server_user_version is None:
                final_version = current_version
            else:
                final_version = max(current_version, server_user_version)

            if server_data_updated_at is not None:
                final_data_updated_at = server_data_updated_at
            else:
                final_data_updated_at = state.get("user_data_updated_at") or final_synced_at

            db.upsert_sync_state(
                user_id=user_id,
                user_data_updated_at=final_data_updated_at,
                user_last_synced_at=final_synced_at,
                user_version=final_version,
                sync_updated_at=_now_iso(),
            )

            response = {
                "ok": True,
                "status": 200,
                "user_id": user_id,
                "user_last_synced_at": final_synced_at,
                "user_version": final_version,
                "user_data_updated_at": final_data_updated_at,
            }
            request_id = payload.get("request_id")
            if isinstance(request_id, str) and request_id:
                response["request_id"] = request_id
            return response

    def handle(self, action: str, payload: Any = None) -> dict[str, Any]:
        if action == "build_probe":
            if isinstance(payload, dict):
                user_id = payload.get("user_id")
            else:
                user_id = payload if isinstance(payload, str) else None
            return self.build_probe(user_id=user_id)

        if action == "resolve_probe_result":
            if not isinstance(payload, dict):
                return _error(400, "SYNC_PROBE_RESPONSE_INVALID", "payload must be object")
            return self.resolve_probe_result(payload)

        if action == "build_push":
            if isinstance(payload, dict):
                user_id = payload.get("user_id")
            else:
                user_id = payload if isinstance(payload, str) else None
            return self.build_push(user_id=user_id)

        if action == "apply_pull":
            return self.apply_pull(payload or {})

        if action == "apply_server_ack":
            return self.apply_server_ack(payload or {})

        return _error(400, "SYNC_ACTION_INVALID", f"unsupported action: {action}")


def handle_sync_request(request: dict[str, Any] | str | Path) -> dict[str, Any]:
    content = _load_request(request)
    action = content.get("action")
    if not action:
        return _error(400, "SYNC_ACTION_REQUIRED", "action is required")

    handler = LocalSyncHandle()
    return handler.handle(action=str(action), payload=content.get("payload"))
