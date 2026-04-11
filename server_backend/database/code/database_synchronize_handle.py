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

IDEMPOTENCY_CACHE_MAX = 1024


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


class ServerSyncHandle:
    def __init__(self) -> None:
        self._service = ops.ServerSyncService()
        self._idempotency_cache: dict[str, dict[str, Any]] = {}
        self._idempotency_lock = threading.Lock()

    def _extract_request_id(self, payload: dict[str, Any]) -> str | None:
        request_id = payload.get("request_id")
        if isinstance(request_id, str) and request_id:
            return request_id

        meta = payload.get("meta")
        if isinstance(meta, dict):
            meta_request_id = meta.get("request_id")
            if isinstance(meta_request_id, str) and meta_request_id:
                return meta_request_id

        return None

    def _idempotency_get(self, key: str) -> dict[str, Any] | None:
        with self._idempotency_lock:
            cached = self._idempotency_cache.get(key)
            return dict(cached) if cached is not None else None

    def _idempotency_put(self, key: str, value: dict[str, Any]) -> None:
        with self._idempotency_lock:
            self._idempotency_cache[key] = dict(value)
            while len(self._idempotency_cache) > IDEMPOTENCY_CACHE_MAX:
                first_key = next(iter(self._idempotency_cache))
                self._idempotency_cache.pop(first_key, None)

    def handle_probe(self, probe_payload: dict[str, Any] | str | Path) -> dict[str, Any]:
        try:
            normalized_payload = _load_request(probe_payload)
        except Exception as exc:
            return _error(422, "SYNC_PAYLOAD_INVALID", "probe payload parsing failed", str(exc))

        request_id = self._extract_request_id(normalized_payload)
        result = self._service.probe_action(normalized_payload)
        if not result.get("ok"):
            message = result.get("error", "probe failed")
            if message == "user not found":
                return _error(404, "SYNC_USER_NOT_FOUND", message)
            return _error(400, "SYNC_PROBE_INVALID", message)

        response = {
            "ok": True,
            "status": 200,
            **result,
        }
        if request_id:
            response["request_id"] = request_id
        return response

    def handle_pull(self, user_id: str, request_id: str | None = None) -> dict[str, Any]:
        if not user_id:
            return _error(400, "SYNC_USER_ID_REQUIRED", "user_id is required")

        try:
            packet = self._service.build_pull_packet(user_id)
        except ValueError as exc:
            return _error(404, "SYNC_USER_NOT_FOUND", str(exc))

        response = {
            "ok": True,
            "status": 200,
            "packet": packet,
        }
        if request_id:
            response["request_id"] = request_id
        return response

    def handle_push(self, sync_payload: dict[str, Any] | str | Path) -> dict[str, Any]:
        try:
            normalized_payload = _load_request(sync_payload)
        except Exception as exc:
            return _error(422, "SYNC_PAYLOAD_INVALID", "sync payload parsing failed", str(exc))

        request_id = self._extract_request_id(normalized_payload)
        cache_key = f"push:{request_id}" if request_id else None
        if cache_key:
            cached = self._idempotency_get(cache_key)
            if cached is not None:
                return cached

        result = self._service.apply_push_packet(normalized_payload)
        outcome = result.get("result")

        if outcome == "invalid_payload":
            return _error(422, "SYNC_PAYLOAD_INVALID", "sync payload validation failed", result.get("errors"))

        if outcome == "discarded_stale":
            response = {
                "ok": True,
                "status": 200,
                "reason": result.get("reason", "incoming payload is stale"),
                **result,
            }
            if request_id:
                response["request_id"] = request_id
            if cache_key:
                self._idempotency_put(cache_key, response)
            return response

        if outcome == "applied":
            response = {
                "ok": True,
                "status": 200,
                "reason": result.get("reason", "payload applied on server"),
                **result,
            }
            if request_id:
                response["request_id"] = request_id
            if cache_key:
                self._idempotency_put(cache_key, response)
            return response

        if outcome == "conflict_rejected":
            return _error(409, "SYNC_CONFLICT_PULL_REQUIRED", result.get("reason", "conflict requires pull"), result)

        return _error(500, "SYNC_INTERNAL_ERROR", "unknown push result", result)

    def handle_ack(self, ack_payload: dict[str, Any] | str | Path) -> dict[str, Any]:
        try:
            payload = _load_request(ack_payload)
        except Exception as exc:
            return _error(422, "SYNC_PAYLOAD_INVALID", "ack payload parsing failed", str(exc))

        request_id = self._extract_request_id(payload)
        cache_key = f"ack:{request_id}" if request_id else None
        if cache_key:
            cached = self._idempotency_get(cache_key)
            if cached is not None:
                return cached

        user_id = payload.get("user_id")
        if not user_id:
            return _error(400, "SYNC_USER_ID_REQUIRED", "user_id is required")

        ack_type = payload.get("ack_type")
        if ack_type not in {"pull_applied", "push_applied"}:
            return _error(400, "SYNC_ACK_TYPE_INVALID", "ack_type must be pull_applied or push_applied")

        client_applied_at = payload.get("client_applied_at")
        if _parse_iso_datetime(client_applied_at) is None:
            return _error(422, "SYNC_TIME_INVALID", "client_applied_at must be ISO-8601 datetime")

        client_user_version_raw = payload.get("client_user_version")
        client_user_version = None
        if client_user_version_raw is not None:
            client_user_version = _coerce_int(client_user_version_raw)
            if client_user_version is None:
                return _error(412, "SYNC_VERSION_INVALID", "client_user_version must be integer")

        user = db.get_user(user_id)
        if not user:
            return _error(404, "SYNC_USER_NOT_FOUND", "user not found")

        state = db.get_sync_state(user_id)
        if state is None:
            state = {
                "user_data_updated_at": user.get("user_last_login") or user.get("user_created_at") or client_applied_at,
                "user_version": 1,
            }

        server_synced_at = _now_iso()
        current_version = int(state.get("user_version") or 1)
        if client_user_version is None:
            version = current_version
        else:
            version = max(current_version, client_user_version)

        # ACK only updates sync convergence time; business update time remains server-owned state.
        user_data_updated_at = state.get("user_data_updated_at") or client_applied_at

        db.upsert_sync_state(
            user_id=user_id,
            user_data_updated_at=user_data_updated_at,
            user_last_synced_at=server_synced_at,
            user_version=version,
            sync_updated_at=server_synced_at,
        )

        response = {
            "ok": True,
            "status": 200,
            "ack_type": ack_type,
            "server_user_last_synced_at": server_synced_at,
            "server_user_version": version,
            "server_user_data_updated_at": user_data_updated_at,
        }
        if request_id:
            response["request_id"] = request_id
        if cache_key:
            self._idempotency_put(cache_key, response)
        return response

    def handle(self, action: str, payload: Any = None) -> dict[str, Any]:
        if action == "probe":
            return self.handle_probe(payload or {})

        if action == "pull":
            if isinstance(payload, dict):
                user_id = payload.get("user_id", "")
                request_id = self._extract_request_id(payload)
            else:
                user_id = str(payload or "")
                request_id = None
            return self.handle_pull(user_id, request_id=request_id)

        if action == "push":
            return self.handle_push(payload or {})

        if action == "ack":
            return self.handle_ack(payload or {})

        return _error(400, "SYNC_ACTION_INVALID", f"unsupported action: {action}")


def handle_sync_request(request: dict[str, Any] | str | Path) -> dict[str, Any]:
    content = _load_request(request)
    action = content.get("action")
    if not action:
        return _error(400, "SYNC_ACTION_REQUIRED", "action is required")

    handler = ServerSyncHandle()
    return handler.handle(action=str(action), payload=content.get("payload"))
