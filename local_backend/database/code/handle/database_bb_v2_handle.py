from local_backend.database.code.operations.database_bb_v2_operations import BbV2Operations


class BbV2Handle:
    def __init__(self):
        self.ops = BbV2Operations()

    def save_courses(self, user_id: str, courses: list) -> dict:
        try:
            result = self.ops.save_all(user_id, courses)
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "message": str(e)}
