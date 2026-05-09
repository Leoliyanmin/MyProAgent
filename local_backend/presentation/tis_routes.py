from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from service.tis_service import TisService
from presentation.dependencies import get_current_user_id

router = APIRouter(prefix="/api/v1/tis", tags=["tis"])
security = HTTPBearer()

tis_service = TisService()


class TisCookieRequest(BaseModel):
    """TIS Cookie请求体模型"""
    cookies: str


@router.get("/status")
async def get_tis_status(user_id: str = Depends(get_current_user_id)):
    """获取TIS绑定状态"""
    result = tis_service.get_tis_status(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '获取状态失败'))
    return result


@router.post("/bind")
async def bind_with_cookie(request: TisCookieRequest, user_id: str = Depends(get_current_user_id)):
    """使用Cookie绑定TIS账号
    
    通过Tauri等方式获取TIS的Cookie后，传递给后端完成绑定。
    
    Args:
        request: 包含cookies的请求体
    
    Returns:
        绑定结果
    """
    cookies = request.cookies
    if not cookies:
        raise HTTPException(status_code=400, detail="cookies不能为空")
    
    result = tis_service.bind_with_cookie(user_id, cookies)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '绑定失败'))
    return result


@router.post("/sync")
async def sync_tis_data(user_id: str = Depends(get_current_user_id)):
    """同步TIS课表数据"""
    result = tis_service.sync_tis_data(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '同步失败'))
    return result


@router.post("/unbind")
async def unbind_tis(user_id: str = Depends(get_current_user_id)):
    """解绑TIS账号"""
    result = tis_service.unbind_tis(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '解绑失败'))
    return result
