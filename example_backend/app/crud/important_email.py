from sqlalchemy.orm import Session
from model.entities import ImportantEmail
from typing import List

def create_important_email(db: Session, user_id: int, email_parsed_id: int, reason: str) -> ImportantEmail:
    """创建一条重要邮件记录"""
    db_obj = ImportantEmail(
        user_id=user_id,
        email_parsed_id=email_parsed_id,
        reason=reason
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_important_emails(db: Session, user_id: int, limit: int = 3) -> List[ImportantEmail]:
    """获取用户的重要邮件列表，按创建时间倒序"""
    return db.query(ImportantEmail).filter(
        ImportantEmail.user_id == user_id
    ).order_by(ImportantEmail.created_at.desc()).limit(limit).all()

def clear_important_emails(db: Session, user_id: int, commit: bool = True) -> int:
    """清空用户的重要邮件记录并可选择是否立即提交。"""

    deleted = (
        db.query(ImportantEmail)
        .filter(ImportantEmail.user_id == user_id)
        .delete(synchronize_session=False)
    )
    if commit:
        db.commit()
    return deleted
