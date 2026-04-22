from fastapi import HTTPException, Depends
from core.database import get_db
from sqlalchemy.orm import Session
from crud.schedule import get_schedule_by_sid, add_schedule_by_sid, delete_schedule_by_id
from typing import List
from model import schemas

def get_schedule(user_id: str, db: Session):
    """获取用户的课表数据"""
    schedules = get_schedule_by_sid(db, user_id)
    if not schedules:
        raise HTTPException(status_code=404, detail="课表未找到")
    return schedules

def add_schedule(db: Session, user_id: str, schedule_data: schemas.ScheduleCreate):
    add_schedule_by_sid(db, user_id, schedule_data)

def delete_schedule(db: Session, user_id: str, schedule_id: int):
    """删除指定的课程/日程"""
    delete_schedule_by_id(db, user_id, schedule_id)
