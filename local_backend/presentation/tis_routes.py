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
async def get_tis_schedule(user_id: str = Depends(get_current_user_id), current_week: int = 1):
    """获取TIS课表数据，转换为日历事件格式返回（从event表读取）"""
    import json
    from datetime import datetime, timedelta
    from local_backend.database.code.command.database_command import list_events_by_user

    course_events = list_events_by_user(user_id, event_type="course", event_source="tis")
    if not course_events:
        raise HTTPException(status_code=404, detail='未找到TIS课表数据，请先绑定TIS账号')

    all_schedule_events = []
    for ev in course_events:
        meta = {}
        if ev.get("event_meta_json"):
            try:
                meta = json.loads(ev["event_meta_json"])
            except (json.JSONDecodeError, TypeError):
                pass
        for se in meta.get("schedule_events", []):
            se["course_name"] = ev.get("event_title", "")
            se["teacher"] = meta.get("teacher", "")
            se["location"] = ev.get("event_location", meta.get("location", ""))
            se["weeks"] = meta.get("weeks", "")
            all_schedule_events.append(se)

    if not all_schedule_events:
        raise HTTPException(status_code=404, detail='TIS课表数据为空')

    if current_week == 1:
        today = datetime.now()
        estimated_week = max(1, today.isocalendar()[1] - 8)
        all_weeks = [e.get("week_num", 1) for e in all_schedule_events]
        current_week = min(all_weeks, key=lambda w: abs(w - estimated_week)) if all_weeks else 1

    today = datetime.now()
    semester_monday = today - timedelta(days=today.weekday() + (current_week - 1) * 7)

    events = []
    for ev in all_schedule_events:
        week_num = ev.get("week_num", 1)
        dow = ev.get("day_of_week", 0)
        offset_days = (week_num - 1) * 7 + dow
        event_date = semester_monday + timedelta(days=offset_days)

        teacher = ev.get("teacher", "")
        location = ev.get("location", "")
        weeks = ev.get("weeks", "")
        ps = ev.get("period_start", 0)
        pe = ev.get("period_end", 0)

        desc_parts = []
        if teacher:
            desc_parts.append(f'教师: {teacher}')
        if location:
            desc_parts.append(f'地点: {location}')
        if ps and pe:
            desc_parts.append(f'节次: {ps}-{pe}节')
        if weeks:
            desc_parts.append(f'周次: {weeks}')
        description = '\n'.join(desc_parts)

        events.append({
            'title': ev.get("course_name", "未知课程"),
            'start': event_date.strftime('%Y-%m-%d'),
            'end': event_date.strftime('%Y-%m-%d'),
            'startTime': ev.get('start_time', ''),
            'endTime': ev.get('end_time', ''),
            'priority': 0,
            'color': '#ff3b30',
            'description': description,
            'source': 'tis',
            'isTodo': False,
            'weekNum': week_num,
        })

    return {'success': True, 'events': events, 'total': len(events)}


@router.post("/unbind")
async def unbind_tis(user_id: str = Depends(get_current_user_id)):
    """解绑TIS账号"""
    result = tis_service.unbind_tis(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '解绑失败'))
    return result
