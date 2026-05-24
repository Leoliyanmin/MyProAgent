from local_backend.database.code.operations.database_user_personality_operations import UserPersonalityOperations


class UserPersonalityHandle:

    def __init__(self):
        self.operations = UserPersonalityOperations()

    def upsert_profile(self, user_id: str, profile_data: dict) -> dict:
        if not user_id:
            return {"ok": False, "status": 400, "message": "user_id \u4e0d\u80fd\u4e3a\u7a7a"}
        try:
            self.operations.upsert_profile(user_id, profile_data)
            return {"ok": True, "status": 200, "message": "\u7528\u6237\u753b\u50cf\u4fdd\u5b58\u6210\u529f"}
        except Exception as e:
            return {"ok": False, "status": 500, "message": f"\u4fdd\u5b58\u5931\u8d25: {e}"}

    def get_profile(self, user_id: str) -> dict:
        if not user_id:
            return {"ok": False, "status": 400, "message": "user_id \u4e0d\u80fd\u4e3a\u7a7a"}
        try:
            profile = self.operations.get_profile(user_id)
            if not profile:
                return {"ok": False, "status": 404, "message": "\u7528\u6237\u753b\u50cf\u4e0d\u5b58\u5728"}
            return {"ok": True, "status": 200, "data": profile}
        except Exception as e:
            return {"ok": False, "status": 500, "message": f"\u83b7\u53d6\u5931\u8d25: {e}"}

    def delete_profile(self, user_id: str) -> dict:
        if not user_id:
            return {"ok": False, "status": 400, "message": "user_id \u4e0d\u80fd\u4e3a\u7a7a"}
        try:
            deleted = self.operations.delete_profile(user_id)
            if not deleted:
                return {"ok": False, "status": 404, "message": "\u7528\u6237\u753b\u50cf\u4e0d\u5b58\u5728"}
            return {"ok": True, "status": 200, "message": "\u5220\u9664\u6210\u529f"}
        except Exception as e:
            return {"ok": False, "status": 500, "message": f"\u5220\u9664\u5931\u8d25: {e}"}

    def update_mbti(self, user_id: str, mbti_result: dict) -> dict:
        if not user_id:
            return {"ok": False, "status": 400, "message": "user_id \u4e0d\u80fd\u4e3a\u7a7a"}
        try:
            self.operations.update_mbti(user_id, mbti_result)
            return {"ok": True, "status": 200, "message": "MBTI \u66f4\u65b0\u6210\u529f"}
        except Exception as e:
            return {"ok": False, "status": 500, "message": f"\u66f4\u65b0\u5931\u8d25: {e}"}

    def handle(self, action: str, payload: dict = None) -> dict:
        if payload is None:
            payload = {}
        handlers = {
            "upsert": lambda: self.upsert_profile(payload.get("user_id", ""), payload.get("profile_data", {})),
            "get": lambda: self.get_profile(payload.get("user_id", "")),
            "delete": lambda: self.delete_profile(payload.get("user_id", "")),
            "update_mbti": lambda: self.update_mbti(payload.get("user_id", ""), payload.get("mbti_result", {})),
        }
        if action in handlers:
            return handlers[action]()
        return {"ok": False, "status": 400, "message": f"Unknown action: {action}"}
