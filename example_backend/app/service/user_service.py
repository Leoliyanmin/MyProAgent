from fastapi import HTTPException, Depends
from core import security, database
from sqlalchemy.orm import Session
from fastapi_cache.decorator import cache
from model.schemas import UserInDB
from crud.user import get_user_by_sid, create_user, update_user_interest



async def get_current_user(db: Session = Depends(database.get_db),
                           token: str = Depends(security.oauth2_scheme)) -> UserInDB:
    """通过JWT Token获取当前用户"""
    print(token)
    sid = security.extract_sid(token)
    
    if not sid:
        raise HTTPException(status_code=401, detail="无效的认证凭据")
    user = get_user_by_sid(db, sid)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserInDB.model_validate(user)

def get_user(db: Session, sid: str):
    """通过学号获取用户"""
    user = get_user_by_sid(db, sid)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserInDB.model_validate(user)

def get_photo_base64(db: Session, sid: str):
    """通过学号获取用户照片的base64编码"""
    user = get_user_by_sid(db, sid)
    if not user or not user.photo:
        raise HTTPException(status_code=404, detail="用户照片不存在")
    return user.photo


def set_user_interest(db: Session, sid: int, interest: str) -> UserInDB:
    """更新兴趣爱好"""
    user = update_user_interest(db, sid, interest)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserInDB.model_validate(user)
