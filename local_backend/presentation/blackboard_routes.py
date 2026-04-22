from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from service.blackboard_service import BlackboardService
from presentation.dependencies import get_current_user_id

router = APIRouter(prefix="/api/v1/blackboard", tags=["blackboard"])
security = HTTPBearer()

blackboard_service = BlackboardService()

@router.get("/status")
async def get_bb_status(user_id: str = Depends(get_current_user_id)):
    """获取Blackboard绑定状态"""
    result = blackboard_service.get_blackboard_status(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '获取状态失败'))
    return result

@router.post("/bind")
async def bind_with_cookie(cookies: str, user_id: str = Depends(get_current_user_id)):
    """使用Cookie绑定Blackboard账号
    
    通过Tauri等方式获取Blackboard的Cookie后，传递给后端完成绑定。
    
    Args:
        cookies: Blackboard的Cookie字符串（JSON格式）
    
    Returns:
        绑定结果
    """
    if not cookies:
        raise HTTPException(status_code=400, detail="cookies不能为空")
    
    result = blackboard_service.bind_with_cookie(user_id, cookies)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '绑定失败'))
    return result

@router.post("/sync")
async def sync_bb_data(user_id: str = Depends(get_current_user_id)):
    """同步Blackboard数据"""
    result = blackboard_service.sync_blackboard_data(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '同步失败'))
    return result

@router.post("/unbind")
async def unbind_bb(user_id: str = Depends(get_current_user_id)):
    """解绑Blackboard账号"""
    result = blackboard_service.unbind_blackboard(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '解绑失败'))
    return result

@router.post("/test-cookie")
async def test_cookie(cookies: str):
    """测试Cookie有效性（不绑定）
    
    用于调试目的，验证Cookie是否可以成功访问Blackboard。
    
    Args:
        cookies: Blackboard的Cookie字符串（JSON格式）
    
    Returns:
        Cookie测试结果
    """
    if not cookies:
        raise HTTPException(status_code=400, detail="cookies不能为空")
    
    result = blackboard_service.test_cookie_validity(cookies)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '测试失败'))
    return result