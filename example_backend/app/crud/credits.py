from typing import Optional
from sqlalchemy.orm import Session
from model.entities import Credits
from util.tis_credits import query_credits


def get_credits_by_user_id(db: Session, user_id: int) -> Optional[Credits]:
    """
    根据用户ID获取学分信息
    """
    return db.query(Credits).filter(Credits.user_id == user_id).first()


def create_credits(db: Session, user_id: int, sid: str = None, password: str = None) -> Optional[Credits]:
    """
    创建学分记录
    """
    # 检查是否已存在
    existing = get_credits_by_user_id(db, user_id)
    if existing:
        return existing
    
    # 获取学分数据
    credits_data = query_credits(sid=sid, password=password)
    if not credits_data:
        return None
    
    # 创建新记录
    credits = Credits(
        user_id=user_id,
        total_credit=credits_data.get("total_credit", 0.0),
        category_credit=credits_data.get("category_credit", {})
    )
    db.add(credits)
    db.commit()
    db.refresh(credits)
    return credits


def update_credits(db: Session, user_id: int, sid: str = None, password: str = None) -> Optional[Credits]:
    """
    更新学分记录
    """
    # 获取最新学分数据
    credits_data = query_credits(sid=sid, password=password)
    if not credits_data:
        return None
    
    # 查找现有记录
    credits = get_credits_by_user_id(db, user_id)
    if not credits:
        # 如果不存在则创建
        return create_credits(db, user_id, sid, password)
    
    # 更新数据
    credits.total_credit = credits_data.get("total_credit", 0.0)
    credits.category_credit = credits_data.get("category_credit", {})
    db.commit()
    db.refresh(credits)
    return credits


def delete_credits(db: Session, user_id: int) -> bool:
    """
    删除学分记录
    """
    credits = get_credits_by_user_id(db, user_id)
    if credits:
        db.delete(credits)
        db.commit()
        return True
    return False
