import json
from typing import List, Optional
from sqlalchemy.orm import Session
from model.entities import BBFile


def get_bb_files_by_user_id(db: Session, user_id: int) -> List[BBFile]:
    return db.query(BBFile).filter(BBFile.user_id == user_id).order_by(BBFile.id.desc()).all()


def get_bb_files_by_course(db: Session, user_id: int, course: str) -> List[BBFile]:
    return db.query(BBFile).filter(BBFile.user_id == user_id, BBFile.course == course).order_by(BBFile.id.desc()).all()


def create_bb_files_from_json(db: Session, user_id: int, files_json: str) -> int:
    """从 bb_download 返回的 JSON 字符串批量导入."""
    try:
        items = json.loads(files_json)
    except json.JSONDecodeError:
        return 0
    if not isinstance(items, list) or not items:
        return 0

    count = 0
    for item in items:
        bb = BBFile(
            user_id=user_id,
            course=item.get("course", ""),
            content=item.get("content", ""),
            file_url=item.get("file_url", ""),
            file_name=item.get("file_name", "")
        )
        db.add(bb)
        count += 1
    db.commit()
    return count


def delete_bb_files_by_user_id(db: Session, user_id: int) -> int:
    q = db.query(BBFile).filter(BBFile.user_id == user_id)
    n = q.count()
    q.delete()
    db.commit()
    return n


def delete_bb_files_by_course(db: Session, user_id: int, course: str) -> int:
    q = db.query(BBFile).filter(BBFile.user_id == user_id, BBFile.course == course)
    n = q.count()
    q.delete()
    db.commit()
    return n
