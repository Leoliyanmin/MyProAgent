from typing import List, Dict
from sqlalchemy.orm import Session
from model.entities import Schedule, User
from model import schemas  # 1. 导入 schemas
from datetime import time

def save_schedule_to_db(db: Session, sid: str, schedule: List[Dict]) -> None:
    """
    将处理后的课程表数据保存到数据库（已存在则不重复存入）
    """
    user = db.query(User).filter(User.user_id == sid).first()
    if not user:
        raise ValueError("用户不存在")

    for item in schedule:
        weekday = _weekday_str_to_int(item.get('weekday'))
        start_hour, start_minute, end_hour, end_minute = _time_slot_to_hours(item.get('time_slots'))
        start_time = time(start_hour, start_minute) if start_hour is not None and start_minute is not None else None
        end_time = time(end_hour, end_minute) if end_hour is not None and end_minute is not None else None

        # 判断是否已存在相同课程
        exists = db.query(Schedule).filter(
            Schedule.name == item.get('course_name'),
            Schedule.teacher == item.get('teacher'),
            Schedule.location == item.get('location'),
            Schedule.weekday == weekday,
            Schedule.start_time == start_time,
            Schedule.end_time == end_time,
            Schedule.schedule_type == "course"
        ).first()
        
        if exists:
            if user not in exists.users:
                exists.users.append(user)  # 建立多对多关系
            continue  # 已存在则跳过

        schedule_obj = Schedule(
            name=item.get('course_name'),
            teacher=item.get('teacher'),
            location=item.get('location'),
            weekday=weekday,
            start_time=start_time,
            end_time=end_time,
            description=f"{item.get('weeks')}",
            schedule_type="course"
        )
        db.add(schedule_obj)
        user.schedules.append(schedule_obj)  # 建立多对多关系

    db.commit()

def add_schedule_by_sid(db: Session, sid: str, schedule_data: schemas.ScheduleCreate):
    """
    根据用户sid, 添加新的课程/日程
    """
    # 2. 查找用户
    user = db.query(User).filter(User.user_id == sid).first()
    if not user:
        print(f"错误：用户 {sid} 不存在")
        return
    exists = db.query(Schedule).filter(
        Schedule.name == schedule_data.name,
        Schedule.teacher == schedule_data.teacher,
        Schedule.location == schedule_data.location,
        Schedule.weekday == schedule_data.weekday,
        Schedule.start_time == schedule_data.start_time,
        Schedule.end_time == schedule_data.end_time,
        Schedule.schedule_type == schedule_data.schedule_type
    ).first()

    if exists:
        if user not in exists.users:
            exists.users.append(user)
    else:
        new_schedule = Schedule(
            name=schedule_data.name,
            location=schedule_data.location,
            start_time=schedule_data.start_time,
            end_time=schedule_data.end_time,
            teacher=schedule_data.teacher,
            weekday=schedule_data.weekday,
            description=schedule_data.description,
            schedule_type=schedule_data.schedule_type
        )
        db.add(new_schedule)
        user.schedules.append(new_schedule)
    db.commit()

def delete_schedule_by_id(db: Session, sid: str, schedule_id: int):
    """
    根据用户sid和课程/日程ID删除指定的课程/日程
    """
    user = db.query(User).filter(User.user_id == sid).first()
    if not user:
        print(f"错误：用户 {sid} 不存在")
        return

    schedule = db.query(Schedule).filter(Schedule.schedule_id == schedule_id).first()
    if not schedule:
        print(f"错误：课程/日程 ID {schedule_id} 不存在")
        return

    if user in schedule.users:
        schedule.users.remove(user)  # 移除多对多关系

    # 如果该课程/日程没有关联任何用户，则删除该课程/日程
    if not schedule.users:
        db.delete(schedule)

    db.commit()

def _weekday_str_to_int(weekday_str: str) -> int:
    """将'星期一'等字符串转为数字1-7"""
    mapping = {
        '星期一': 1,
        '星期二': 2,
        '星期三': 3,
        '星期四': 4,
        '星期五': 5,
        '星期六': 6,
        '星期日': 7,
        '星期天': 7
    }
    return mapping.get(weekday_str, 0)


def get_schedule_by_sid(db: Session, sid: int) -> list[Schedule]:
    """
    根据用户ID(sid)获取该用户的课程表
    :param db: SQLAlchemy 数据库会话
    :param sid: 用户ID
    :return: Schedule 对象列表（如果用户不存在则返回空列表）
    """
    # 方式一：通过 User 的关系属性直接访问
    user = db.get(User, sid)
    if not user:
        return []
    return user.schedules


def _time_slot_to_hours(time_slot: str) -> (int, int, int, int):
    """将时间段字符串转为开始和结束小时"""
    mapping = {
        "1-2节": (8, 0, 9, 50),
        "3-4节": (10, 20, 12, 10),
        "5-6节": (14, 0, 15, 50),
        "7-8节": (16, 20, 18, 10),
        "9-10节": (19, 0, 20, 50)
    }
    return mapping.get(time_slot, (0, 0, 0, 0))