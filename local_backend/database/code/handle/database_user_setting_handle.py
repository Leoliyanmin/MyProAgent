from local_backend.database.code.operations.database_user_setting_operations import UserSettingOperations


class UserSettingHandle:
    def __init__(self):
        self.operations = UserSettingOperations()

    def get_settings(self, user_id: str) -> dict:
        try:
            data = self.operations.get(user_id)
            return {"ok": True, "status": 200, "data": data or {}}
        except Exception as e:
            return {"ok": False, "status": 500, "message": str(e)}

    def update_settings(self, user_id: str, fields: dict) -> dict:
        if not user_id:
            return {"ok": False, "status": 400, "message": "user_id 不能为空"}
        try:
            self.operations.save(user_id, **fields)
            return {"ok": True, "status": 200, "message": "保存成功"}
        except Exception as e:
            return {"ok": False, "status": 500, "message": str(e)}
