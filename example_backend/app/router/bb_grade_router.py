from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from service import user_service
from service.bb_grade_service import BBGradeService
from model.schemas import BBGradeInfo, BBGradeSyncResponse

router = APIRouter(prefix="/bb/grades", tags=["bb-grades"])


@router.post("/sync", response_model=BBGradeSyncResponse)
def sync_bb_grades(
    semester: str | None = Query(default="2025秋", description="学期筛选，例如 2025春"),
    sid: str | None = Query(default=None, description="学号，如留空则尝试使用 cookies_file"),
    password: str | None = Query(default=None, description="密码，如留空则尝试使用 cookies_file"),
    cookies_file: str = Query(default="util/data/cookies.json", description="可选：cookie 文件路径"),
    db: Session = Depends(get_db),
    current_user = Depends(user_service.get_current_user),
):
    return BBGradeService.sync_bb_grades(
        db,
        user_id=current_user.user_id,
        sid=sid,
        password=password,
        semester=semester,
        cookies_file=cookies_file,
    )


@router.get("/", response_model=List[BBGradeInfo])
def list_bb_grades(
    course_name: str | None = Query(default=None, description="Filter by course_name"),
    db: Session = Depends(get_db),
    current_user = Depends(user_service.get_current_user),
):
    return BBGradeService.list_grades(db, current_user.user_id, course_name)


@router.delete("/")
def delete_bb_grades(
    course_name: str | None = Query(default=None, description="Delete by course_name; empty deletes all for user"),
    db: Session = Depends(get_db),
    current_user = Depends(user_service.get_current_user),
):
    deleted = BBGradeService.delete_grades(db, current_user.user_id, course_name)
    scope = f"course_name={course_name}" if course_name else "all courses"
    return {"success": True, "count": deleted, "message": f"Deleted {deleted} grade records for {scope}"}