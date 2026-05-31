from local_backend.database.code.operations.database_activity_log_operations import ActivityLogOperations


class ActivityLogHandle:

    def __init__(self):
        self.operations = ActivityLogOperations()

    def record(self, user_id: str, log_date: str, hour: int, count: int = 1) -> dict:
        if not user_id:
            return {"ok": False, "status": 400, "message": "user_id is required"}
        try:
            self.operations.record(user_id, log_date, hour, count)
            return {"ok": True, "status": 200, "message": "activity recorded"}
        except Exception as e:
            return {"ok": False, "status": 500, "message": f"failed: {e}"}

    def record_batch(self, user_id: str, logs: list[dict]) -> dict:
        if not user_id:
            return {"ok": False, "status": 400, "message": "user_id is required"}
        if not logs:
            return {"ok": True, "status": 200, "message": "nothing to record"}
        try:
            self.operations.record_batch(user_id, logs)
            return {"ok": True, "status": 200, "message": f"{len(logs)} entries recorded"}
        except Exception as e:
            return {"ok": False, "status": 500, "message": f"failed: {e}"}

    def list(self, user_id: str, from_date: str | None = None, to_date: str | None = None) -> dict:
        if not user_id:
            return {"ok": False, "status": 400, "message": "user_id is required"}
        try:
            logs = self.operations.query(user_id, from_date, to_date)
            return {"ok": True, "status": 200, "data": {"logs": logs}}
        except Exception as e:
            return {"ok": False, "status": 500, "message": f"failed: {e}"}

    def heatmap(self, user_id: str, from_date: str | None = None, to_date: str | None = None) -> dict:
        if not user_id:
            return {"ok": False, "status": 400, "message": "user_id is required"}
        try:
            data = self.operations.get_heatmap(user_id, from_date, to_date)
            return {"ok": True, "status": 200, "data": {"heatmap": data}}
        except Exception as e:
            return {"ok": False, "status": 500, "message": f"failed: {e}"}

    def handle(self, action: str, payload: dict = None) -> dict:
        if payload is None:
            payload = {}
        handlers = {
            "record": lambda: self.record(
                payload.get("user_id", ""), payload.get("log_date", ""),
                payload.get("hour", 0), payload.get("count", 1),
            ),
            "record_batch": lambda: self.record_batch(
                payload.get("user_id", ""), payload.get("logs", []),
            ),
            "list": lambda: self.list(
                payload.get("user_id", ""), payload.get("from_date"),
                payload.get("to_date"),
            ),
            "heatmap": lambda: self.heatmap(
                payload.get("user_id", ""), payload.get("from_date"),
                payload.get("to_date"),
            ),
        }
        if action in handlers:
            return handlers[action]()
        return {"ok": False, "status": 400, "message": f"Unknown action: {action}"}
