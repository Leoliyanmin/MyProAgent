from fastapi import APIRouter, Depends
from core.database import get_db
from sqlalchemy.orm import Session
from service import schedule_service, user_service
from typing import List
from model import schemas

router = APIRouter(prefix="/schedule", tags=["Schedule"])

@router.get("/")
async def get_main_page_schedule_data(db: Session = Depends(get_db),
                             current_user: schemas.UserInDB = Depends(user_service.get_current_user)):
    """获取主页面数据: 课程表"""
    schedule = schedule_service.get_schedule(current_user.user_id, db)
    return {
        "sid": current_user.user_id,
        "name": current_user.name,
        "schedule": schedule}

@router.post("/")
async def add_main_page_schedule_data(schedule_data: schemas.ScheduleCreate,
                                      db: Session = Depends(get_db),
                                      current_user: schemas.UserInDB = Depends(user_service.get_current_user),
                                      ):
    schedule_service.add_schedule(db, current_user.user_id, schedule_data)
    return {"message": "日程添加成功"}

@router.delete("/{schedule_id}")
async def delete_main_page_schedule_data(db: Session = Depends(get_db),
                                         current_user: schemas.UserInDB = Depends(user_service.get_current_user),
                                         schedule_id: int = None):
    """删除指定的日程"""
    schedule_service.delete_schedule(db, current_user.user_id, schedule_id)
    return {"message": "日程删除成功"}