from typing import List, Dict
from sqlalchemy.orm import Session
from model.entities import User, Deadline
from model import schemas

def save_ddl_to_db(db: Session, sid: str, schedule: List[Dict]):
    """
    将处理后的ddl数据保存到数据库
    """
    user = db.query(User).filter(User.user_id == sid).first()
    if not user:
        raise ValueError("用户不存在")
    for item in schedule:
        # 判断是否已存在相同ddl
        exists = db.query(Deadline).filter(
            Deadline.user_id == sid,
            Deadline.title == item.get('title'),
            Deadline.end_time == item.get('end')
        ).first()

        if exists:
            continue  # 已存在则跳过


        ddl_obj = Deadline(
            is_user_created = 0 if item.get('userCreated') is False else 1,
            calendar_name = item.get('calendarName'),
            end_time=item.get('end'),
            title=item.get('title'),
            event_type=item.get('eventType'),
            color=item.get('color'),
            user=user  # 建立一对多关系
        )

        db.add(ddl_obj)
    
    db.commit()

def get_ddl_by_sid(db: Session, sid: str) -> List[Deadline]:
    """
    根据学号获取用户的ddl
    """
    user = db.get(User, sid)
    if not user:
        return []
    return user.deadlines

def add_ddl_by_sid(db: Session, sid: str, ddl_data: schemas.DDLCreate) -> Deadline:
    """
    为指定用户添加一条自定义DDL
    """
    user = db.query(User).filter(User.user_id == sid).first()
    if not user:
        raise ValueError("用户不存在")

    existing = db.query(Deadline).filter(
        Deadline.user_id == sid,
        Deadline.title == ddl_data.title,
        Deadline.end_time == ddl_data.end_time
    ).first()

    if existing:
        return existing

    ddl_obj = Deadline(
        is_user_created=1,
        calendar_name=ddl_data.calendar_name,
        end_time=ddl_data.end_time,
        title=ddl_data.title,
        event_type=ddl_data.event_type,
        color=ddl_data.color,
        user=user
    )
    db.add(ddl_obj)
    db.commit()
    db.refresh(ddl_obj)
    return ddl_obj

def delete_ddl_by_id(db: Session, sid: str, ddl_id: int) -> bool:
    """
    删除指定用户的一条DDL
    """
    user = db.query(User).filter(User.user_id == sid).first()
    if not user:
        raise ValueError("用户不存在")

    ddl_obj = db.query(Deadline).filter(
        Deadline.id == ddl_id,
        Deadline.user_id == sid
    ).first()

    if not ddl_obj:
        return False

    db.delete(ddl_obj)
    db.commit()
    return True
