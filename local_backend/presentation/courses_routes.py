from fastapi import APIRouter, Depends, HTTPException

from service.tis_service import TisService
from presentation.dependencies import get_current_user_id

router = APIRouter(prefix="/api/v1", tags=["courses"])

tis_service = TisService()


@router.get("/courses")
async def get_courses(user_id: str = Depends(get_current_user_id)):
    """获取已同步的TIS课程列表"""
    result = tis_service.get_tis_schedule(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '获取失败'))
    return result
