from fastapi import HTTPException
from sqlalchemy.orm import Session
from crud.ddl import get_ddl_by_sid, add_ddl_by_sid, delete_ddl_by_id
from model import schemas


def get_ddl(user_id: str, db: Session):
    """Get DDL list for a user"""
    ddls = get_ddl_by_sid(db, user_id)
    if not ddls:
        raise HTTPException(status_code=404, detail="DDL not found")
    return ddls


def add_ddl(user_id: str, db: Session, ddl_data: schemas.DDLCreate):
    """Create a new user DDL"""
    try:
        return add_ddl_by_sid(db, user_id, ddl_data)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


def delete_ddl(user_id: str, db: Session, ddl_id: int):
    """Delete a user DDL by id"""
    try:
        deleted = delete_ddl_by_id(db, user_id, ddl_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    if not deleted:
        raise HTTPException(status_code=404, detail="DDL not found")
