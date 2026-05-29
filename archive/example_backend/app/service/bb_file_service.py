from typing import List
from sqlalchemy.orm import Session
from util.bb_download import download_all_courses
from crud.bb_file import (
    get_bb_files_by_user_id,
    get_bb_files_by_course,
    create_bb_files_from_json,
    delete_bb_files_by_user_id,
    delete_bb_files_by_course,
)

class BBFileService:
    @staticmethod
    def sync_bb_files(db: Session, user_id: int, sid: str = None, password: str = None, term_filter: str = "2025秋") -> dict:
        try:
            files_json = download_all_courses(sid=sid, password=password, term_filter=term_filter)
            if not files_json or files_json == "[]":
                return {"success": False, "count": 0, "message": "未获取到文件数据"}
            # 可选：删除旧记录
            delete_bb_files_by_user_id(db, user_id)
            count = create_bb_files_from_json(db, user_id, files_json)
            return {"success": True, "count": count, "message": f"成功同步 {count} 个文件"}
        except Exception as e:
            return {"success": False, "count": 0, "message": f"同步失败: {e}"}

    @staticmethod
    def list_user_files(db: Session, user_id: int) -> List:
        return get_bb_files_by_user_id(db, user_id)

    @staticmethod
    def list_course_files(db: Session, user_id: int, course: str) -> List:
        return get_bb_files_by_course(db, user_id, course)

    @staticmethod
    def delete_user_files(db: Session, user_id: int) -> int:
        return delete_bb_files_by_user_id(db, user_id)

    @staticmethod
    def delete_course_files(db: Session, user_id: int, course: str) -> int:
        return delete_bb_files_by_course(db, user_id, course)
