from typing import List
from sqlalchemy.orm import Session
from util.bb_grade import get_grades_from_html
from crud.bb_grade import replace_bb_grades, list_bb_grades, delete_bb_grades


class BBGradeService:
    @staticmethod
    def sync_bb_grades(
        db: Session,
        user_id: int,
        sid: str | None = None,
        password: str | None = None,
        semester: str | None = None,
        cookies_file: str = "util/data/cookies.json",
    ) -> dict:
        try:
            grades = get_grades_from_html(
                sid=sid or "",
                password=password or "",
                semester=semester,
                cookies_file=cookies_file,
            )
            if not grades:
                return {"success": False, "count": 0, "message": "未获取到成绩数据"}
            count = replace_bb_grades(db, user_id, grades)
            return {"success": True, "count": count, "message": f"成功同步 {count} 条成绩记录"}
        except Exception as e:
            return {"success": False, "count": 0, "message": f"同步失败: {e}"}

    @staticmethod
    def list_grades(db: Session, user_id: int, course_name: str | None = None) -> List:
        return list_bb_grades(db, user_id, course_name)

    @staticmethod
    def delete_grades(db: Session, user_id: int, course_name: str | None = None) -> int:
        return delete_bb_grades(db, user_id, course_name)
