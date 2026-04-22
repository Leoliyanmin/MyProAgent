from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from .database_blackboard_operations import BlackboardOperations
except ImportError:
    from database_blackboard_operations import BlackboardOperations


def _load_request(request: dict[str, Any] | str | Path) -> dict[str, Any]:
    if isinstance(request, dict):
        return request
    if isinstance(request, Path):
        import json

        return json.loads(request.read_text(encoding="utf-8"))
    if isinstance(request, str):
        import json

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


class BlackboardHandle:
    def __init__(self) -> None:
        self._operations = BlackboardOperations()

    def save_crawl_result(
        self,
        user_id: str,
        crawl_result: dict[str, Any] | list[Any],
        crawled_at: Any = None,
    ) -> dict[str, Any]:
        if not user_id:
            return _error(400, "BLACKBOARD_USER_ID_REQUIRED", "user_id is required")

        if crawl_result is None:
            return _error(400, "BLACKBOARD_PAYLOAD_REQUIRED", "crawl_result is required")

        try:
            result = self._operations.import_crawl_result(user_id=user_id, crawl_result=crawl_result, crawled_at=crawled_at)
        except ValueError as exc:
            return _error(422, "BLACKBOARD_PAYLOAD_INVALID", str(exc))
        except Exception as exc:
            return _error(500, "BLACKBOARD_INTERNAL_ERROR", f"failed to save blackboard result: {exc}")

        return {
            "ok": True,
            "status": 200,
            "message": "blackboard crawl result saved",
            "data": result,
        }

    def handle(self, action: str, payload: Any = None) -> dict[str, Any]:
        if action == "save_crawl_result":
            if isinstance(payload, dict):
                user_id = payload.get("user_id")
                crawl_result = payload.get("crawl_result")
                crawled_at = payload.get("crawled_at")
            else:
                user_id = None
                crawl_result = payload
                crawled_at = None
            return self.save_crawl_result(user_id=user_id, crawl_result=crawl_result, crawled_at=crawled_at)
        return _error(400, "BLACKBOARD_ACTION_INVALID", f"unsupported action: {action}")


def handle_blackboard_request(request: dict[str, Any] | str | Path) -> dict[str, Any]:
    payload = _load_request(request)
    handle = BlackboardHandle()
    return handle.handle("save_crawl_result", payload)