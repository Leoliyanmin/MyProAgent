from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from service import user_service
from service.bb_file_service import BBFileService
from model.schemas import BBFileInfo, BBFileSyncResponse

router = APIRouter(prefix="/bb/files", tags=["bb-files"])

@router.post("/sync", response_model=BBFileSyncResponse)
def sync_bb_files(
    term_filter: str = Query(default="2025秋", description="学期筛选，如 2025秋"),
    db: Session = Depends(get_db),
    current_user = Depends(user_service.get_current_user)
):
    result = BBFileService.sync_bb_files(db, current_user.user_id, term_filter=term_filter)
    return result

@router.get("/", response_model=List[BBFileInfo])
def list_bb_files(
    course: str | None = Query(default=None, description="课程名称筛选"),
    db: Session = Depends(get_db),
    current_user = Depends(user_service.get_current_user)
):
    if course:
        return BBFileService.list_course_files(db, current_user.user_id, course)
    return BBFileService.list_user_files(db, current_user.user_id)

@router.delete("/")
def delete_bb_files(
    course: str | None = Query(default=None, description="课程名称，不填则删除全部"),
    db: Session = Depends(get_db),
    current_user = Depends(user_service.get_current_user)
):
    if course:
        count = BBFileService.delete_course_files(db, current_user.user_id, course)
        return {"success": True, "count": count, "message": f"已删除课程 {course} 的 {count} 条记录"}
    count = BBFileService.delete_user_files(db, current_user.user_id)
    return {"success": True, "count": count, "message": f"已删除全部 {count} 条记录"}
