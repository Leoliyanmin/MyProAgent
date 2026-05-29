from fastapi import APIRouter, Depends
from core.database import get_db
from sqlalchemy.orm import Session
from service import user_service, schedule_service, ddl_service
from model import schemas


router = APIRouter()

@router.get("/mainpage")
async def get_main_page_data(db: Session = Depends(get_db),
                             current_user: schemas.UserInDB = Depends(user_service.get_current_user)):
    """获取主页面数据"""
    schedule = schedule_service.get_schedule(current_user.user_id, db)
    photo_base64 = user_service.get_photo_base64(db, current_user.user_id)
    ddls=ddl_service.get_ddl(current_user.user_id,db)
    return {
        "sid": current_user.user_id,
        "name": current_user.name,
        "photo": photo_base64,
        "schedule": schedule,
        "ddls": ddls}




@router.get("/mainpage/ddls")
async def get_main_page_data(db: Session = Depends(get_db),
                             current_user: schemas.UserInDB = Depends(user_service.get_current_user)):
    """获取主页面数据: 待办事项"""
    ddls=ddl_service.get_ddl(current_user.user_id,db)
    return {
        "sid": current_user.user_id,
        "name": current_user.name,
        "ddls": ddls}




@router.post("/mainpage/ddls")
async def add_main_page_ddl(payload: schemas.DDLCreate,
                            db: Session = Depends(get_db),
                            current_user: schemas.UserInDB = Depends(user_service.get_current_user)):
    """添加一条DDL"""
    ddl_service.add_ddl(current_user.user_id, db, payload)
    return {"message": "DDL添加成功"}

@router.delete("/mainpage/ddls/{ddl_id}")
async def delete_main_page_ddl(ddl_id: int,
                               db: Session = Depends(get_db),
                               current_user: schemas.UserInDB = Depends(user_service.get_current_user)):
    """删除指定的DDL"""
    ddl_service.delete_ddl(current_user.user_id, db, ddl_id)
    return {"message": "DDL删除成功"}

@router.get("/mainpage/personal_info")
async def get_personal_info(db: Session = Depends(get_db),
                            current_user: schemas.UserInDB = Depends(user_service.get_current_user)):
    """获取个人信息"""
    return current_user

@router.put("/mainpage/personal_info/interest")
async def update_interest(
    payload: schemas.InterestUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.UserInDB = Depends(user_service.get_current_user),
):
    """更新当前登录用户的兴趣爱好"""
    updated_user = user_service.set_user_interest(db, current_user.user_id, payload.interest)
    return updated_user
