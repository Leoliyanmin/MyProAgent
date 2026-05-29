from fastapi import APIRouter, Depends, HTTPException
from model.schemas import LoginRequest
from service.sso_service import sso_login, list_services
from core.database import get_db
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm


# ✅ 引入调度器控制方法
from service.time_update import start_scheduler, stop_scheduler

router = APIRouter()

@router.post("/login")
async def login_endpoint(form_data: OAuth2PasswordRequestForm = Depends(),
                         db: Session = Depends(get_db)):
    # ✅ 登录成功后启动调度器，每分钟更新一次（测试用）
    start_scheduler(interval_minutes=60*24)  # BB+TIS
    return sso_login(form_data, db)



@router.get("/services")
async def list_services_endpoint():
    return list_services()

@router.post("/logout")
async def logout_endpoint():
    """
    用户登出：登出时自动停止调度器
    """
    try:
        stop_scheduler()
        return {"message": "已登出并停止后台任务。"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登出过程出现错误: {e}")