from local_backend.database.code.operations.database_interaction_log_operations import InteractionLogOperations


class InteractionLogHandle:

    def __init__(self):
        self.operations = InteractionLogOperations()

    def log_interaction(self, interaction_data: dict) -> dict:
        try:
            conv_id = self.operations.log(interaction_data)
            return {"ok": True, "status": 201, "data": {"conversation_id": conv_id}}
        except Exception as e:
            return {"ok": False, "status": 500, "message": f"\u8bb0\u5f55\u5931\u8d25: {e}"}

    def get_interaction(self, conversation_id: str) -> dict:
        if not conversation_id:
            return {"ok": False, "status": 400, "message": "conversation_id \u4e0d\u80fd\u4e3a\u7a7a"}
        try:
            data = self.operations.get(conversation_id)
            if not data:
                return {"ok": False, "status": 404, "message": "\u4ea4\u4e92\u8bb0\u5f55\u4e0d\u5b58\u5728"}
            return {"ok": True, "status": 200, "data": data}
        except Exception as e:
            return {"ok": False, "status": 500, "message": f"\u83b7\u53d6\u5931\u8d25: {e}"}

    def get_user_interactions(self, user_id: str, limit: int = 100) -> dict:
        if not user_id:
            return {"ok": False, "status": 400, "message": "user_id \u4e0d\u80fd\u4e3a\u7a7a"}
        try:
            data = self.operations.list_for_user(user_id, limit)
            return {"ok": True, "status": 200, "data": data, "count": len(data)}
        except Exception as e:
            return {"ok": False, "status": 500, "message": f"\u83b7\u53d6\u5931\u8d25: {e}"}

    def delete_interaction(self, conversation_id: str) -> dict:
        if not conversation_id:
            return {"ok": False, "status": 400, "message": "conversation_id \u4e0d\u80fd\u4e3a\u7a7a"}
        try:
            deleted = self.operations.delete(conversation_id)
            if not deleted:
                return {"ok": False, "status": 404, "message": "\u8bb0\u5f55\u4e0d\u5b58\u5728"}
            return {"ok": True, "status": 200, "message": "\u5220\u9664\u6210\u529f"}
        except Exception as e:
            return {"ok": False, "status": 500, "message": f"\u5220\u9664\u5931\u8d25: {e}"}

    def count_interactions(self, user_id: str) -> dict:
        if not user_id:
            return {"ok": False, "status": 400, "message": "user_id \u4e0d\u80fd\u4e3a\u7a7a"}
        try:
            cnt = self.operations.count_for_user(user_id)
            return {"ok": True, "status": 200, "count": cnt}
        except Exception as e:
            return {"ok": False, "status": 500, "message": f"\u7edf\u8ba1\u5931\u8d25: {e}"}

    def handle(self, action: str, payload: dict = None) -> dict:
        if payload is None:
            payload = {}
        handlers = {
            "log": lambda: self.log_interaction(payload.get("interaction_data", {})),
            "get": lambda: self.get_interaction(payload.get("conversation_id", "")),
            "list": lambda: self.get_user_interactions(payload.get("user_id", ""), payload.get("limit", 100)),
            "delete": lambda: self.delete_interaction(payload.get("conversation_id", "")),
            "count": lambda: self.count_interactions(payload.get("user_id", "")),
        }
        if action in handlers:
            return handlers[action]()
        return {"ok": False, "status": 400, "message": f"Unknown action: {action}"}
