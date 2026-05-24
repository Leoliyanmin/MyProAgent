from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import asyncio
import traceback
import logging

from service.tis_service import TisService
from presentation.dependencies import get_current_user_id

router = APIRouter(prefix="/api/v1/tis", tags=["tis"])
security = HTTPBearer()
logger = logging.getLogger(__name__)

tis_service = TisService()
_executor = None

def _get_executor():
    global _executor
    if _executor is None:
        from concurrent.futures import ThreadPoolExecutor
        _executor = ThreadPoolExecutor(max_workers=4)
    return _executor


class TisCookieRequest(BaseModel):
    """TIS Cookie请求体模型"""
    cookies: str


@router.get("/status")
async def get_tis_status(user_id: str = Depends(get_current_user_id)):
    """获取TIS绑定状态（从DB读取）"""
    from local_backend.database.code.handle.database_tis_handle import TisHandle
    from local_backend.database.code.command.database_command import list_events_by_user

    tis_handle = TisHandle()
    db_status = tis_handle.handle_get_tis_status(user_id)
    if db_status.get('success') and db_status.get('is_bound'):
        courses = list_events_by_user(user_id, event_type="course", event_source="tis")
        return {
            'success': True,
            'is_bound': True,
            'student_id': db_status.get('student_id', ''),
            'bind_time': db_status.get('bind_time', ''),
            'last_sync_time': db_status.get('last_sync_time', ''),
            'total_courses': len(courses),
            'message': '已绑定TIS账号',
        }
    return {'success': True, 'is_bound': False, 'message': '未绑定TIS账号'}


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
    
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            _get_executor(),
            tis_service.bind_with_cookie,
            user_id, cookies
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message', '绑定失败'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TIS bind 崩溃: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}")


@router.get("/schedule")
async def get_tis_schedule(user_id: str = Depends(get_current_user_id)):
    """获取TIS课表数据"""
    import json
    from local_backend.database.code.command.database_command import list_events_by_user

    course_events = list_events_by_user(user_id, event_type="course", event_source="tis")
    if not course_events:
        raise HTTPException(status_code=404, detail='未找到TIS课表数据，请先绑定TIS账号')

    events = []
    for ev in course_events:
        meta = {}
        if ev.get("event_meta_json"):
            try:
                meta = json.loads(ev["event_meta_json"])
            except (json.JSONDecodeError, TypeError):
                pass

        teacher = meta.get("teacher", "")
        location = ev.get("event_location", meta.get("location", ""))
        weeks = meta.get("weeks", "")
        ps = meta.get("period_start", 0)
        pe = meta.get("period_end", 0)

        desc_parts = []
        if teacher:
            desc_parts.append(f'教师: {teacher}')
        if location:
            desc_parts.append(f'地点: {location}')
        if ps and pe:
            desc_parts.append(f'节次: {ps}-{pe}节')
        if weeks:
            desc_parts.append(f'周次: {weeks}')

        start_raw = ev.get("event_start_time", "")
        end_raw = ev.get("event_end_time", "")
        start_date = (start_raw or "").split("T")[0] if start_raw else ""
        end_date = (end_raw or "").split("T")[0] if end_raw else ""
        start_time = (start_raw or "").split("T")[1][:5] if start_raw and "T" in start_raw else ""
        end_time = (end_raw or "").split("T")[1][:5] if end_raw and "T" in end_raw else ""

        events.append({
            'title': ev.get("event_title", "未知课程"),
            'start': start_date,
            'end': end_date or start_date,
            'startTime': start_time,
            'endTime': end_time,
            'priority': 4,
            'color': '#8e8e93',
            'description': '\n'.join(desc_parts),
            'source': 'tis',
            'isTodo': False,
        })

    return {'success': True, 'events': events, 'total': len(events)}


@router.post("/unbind")
async def unbind_tis(user_id: str = Depends(get_current_user_id)):
    """解绑TIS账号"""
    result = tis_service.unbind_tis(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '解绑失败'))
    return result
