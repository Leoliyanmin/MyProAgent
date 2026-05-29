from typing import List
from sqlalchemy.orm import Session
from model.entities import BBGrade


def replace_bb_grades(db: Session, user_id: int, items) -> int:
    # 容错：字符串尝试 JSON 解析；非列表直接丢弃
    if isinstance(items, str):
        try:
            import json
            items = json.loads(items)
        except Exception:
            items = []
    if not isinstance(items, list):
        items = []

    db.query(BBGrade).filter(BBGrade.user_id == user_id).delete()
    count = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        db.add(BBGrade(
            user_id=user_id,
            course_id=item.get("course_id", ""),
            course_name=item.get("course_name"),
            item_name=item.get("item_name", ""),
            full_grade=item.get("full_grade", ""),
        
        ))
        count += 1
    db.commit()
    return count



def list_bb_grades(db: Session, user_id: int, course_name: str | None = None) -> List[BBGrade]:
    q = db.query(BBGrade).filter(BBGrade.user_id == user_id).order_by(BBGrade.id.desc())
    if course_name:
        q = q.filter(BBGrade.course_name == course_name)
    return q.all()


def delete_bb_grades(db: Session, user_id: int, course_name: str | None = None) -> int:
    q = db.query(BBGrade).filter(BBGrade.user_id == user_id)
    if course_name:
        q = q.filter(BBGrade.course_name == course_name)
    n = q.count()
    q.delete()
    db.commit()
    return n
