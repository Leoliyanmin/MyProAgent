from local_backend.database.code.operations.database_api_key_operations import ApiKeyOperations, _mask_api_key


class ApiKeyHandle:

    def __init__(self):
        self.operations = ApiKeyOperations()

    def save_api_key(self, user_id: str, provider: str, api_key: str,
                     api_base: str, model: str = "", key_id: str = "",
                     last_test_success: bool = None) -> dict:
        if not user_id or not provider or not api_base:
            return {"ok": False, "status": 400, "message": "user_id, provider, api_base \u4e0d\u80fd\u4e3a\u7a7a"}
        try:
            if key_id:
                self.operations.update(
                    key_id, provider=provider, api_key_plain=api_key.strip() or None,
                    api_base=api_base, model=model,
                    last_test_success=1 if last_test_success else 0 if last_test_success is not None else None,
                )
                return {"ok": True, "status": 200, "data": {"key_id": key_id}}
            new_id = self.operations.create(user_id, provider, api_key, api_base, model)
            return {"ok": True, "status": 201, "data": {"key_id": new_id}}
        except Exception as e:
            return {"ok": False, "status": 500, "message": f"\u4fdd\u5b58\u5931\u8d25: {e}"}

    def list_api_keys(self, user_id: str) -> dict:
        if not user_id:
            return {"ok": False, "status": 400, "message": "user_id \u4e0d\u80fd\u4e3a\u7a7a"}
        try:
            rows = self.operations.list_for_user(user_id)
            result = []
            for r in rows:
                result.append({
                    "key_id": r.get("key_id", ""),
                    "provider": r.get("provider", ""),
                    "api_key_masked": _mask_api_key(
                        self.operations.get_full(r["key_id"]).get("api_key", "")
                        if self.operations.get_full(r["key_id"]) else ""
                    ),
                    "api_base": r.get("api_base", ""),
                    "model": r.get("model", ""),
                    "is_active": r.get("is_active", False),
                    "updated_at": r.get("updated_at", ""),
                    "last_test_success": r.get("last_test_success"),
                })
            result.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            return {"ok": True, "status": 200, "keys": result}
        except Exception as e:
            return {"ok": False, "status": 500, "message": f"\u83b7\u53d6\u5931\u8d25: {e}"}

    def delete_api_key(self, user_id: str, key_id: str) -> dict:
        if not key_id:
            return {"ok": False, "status": 400, "message": "key_id \u4e0d\u80fd\u4e3a\u7a7a"}
        try:
            existing = self.operations.get(key_id)
            if not existing or existing.get("user_id") != user_id:
                return {"ok": False, "status": 404, "message": "API Key \u4e0d\u5b58\u5728"}
            self.operations.delete(key_id)
            return {"ok": True, "status": 200, "message": "\u5220\u9664\u6210\u529f"}
        except Exception as e:
            return {"ok": False, "status": 500, "message": f"\u5220\u9664\u5931\u8d25: {e}"}

    def toggle_api_key(self, user_id: str, key_id: str) -> dict:
        if not key_id:
            return {"ok": False, "status": 400, "message": "key_id \u4e0d\u80fd\u4e3a\u7a7a"}
        try:
            existing = self.operations.get(key_id)
            if not existing or existing.get("user_id") != user_id:
                return {"ok": False, "status": 404, "message": "API Key \u4e0d\u5b58\u5728"}
            new_active = 0 if existing.get("is_active") else 1
            self.operations.update(key_id, is_active=new_active)
            return {"ok": True, "status": 200, "is_active": bool(new_active)}
        except Exception as e:
            return {"ok": False, "status": 500, "message": f"\u64cd\u4f5c\u5931\u8d25: {e}"}

    def test_api_key(self, provider: str, api_key: str, api_base: str, model: str = "") -> dict:
        return self.operations.test(provider, api_key, api_base, model)

    def handle(self, action: str, payload: dict = None) -> dict:
        if payload is None:
            payload = {}
        handlers = {
            "save": lambda: self.save_api_key(**payload),
            "list": lambda: self.list_api_keys(payload.get("user_id", "")),
            "delete": lambda: self.delete_api_key(payload.get("user_id", ""), payload.get("key_id", "")),
            "toggle": lambda: self.toggle_api_key(payload.get("user_id", ""), payload.get("key_id", "")),
            "test": lambda: self.test_api_key(**payload),
        }
        if action in handlers:
            return handlers[action]()
        return {"ok": False, "status": 400, "message": f"Unknown action: {action}"}
