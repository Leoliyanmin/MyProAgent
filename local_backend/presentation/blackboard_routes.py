from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import asyncio
import traceback
import logging

from service.blackboard_service import BlackboardService
from presentation.dependencies import get_current_user_id
import json
import os
import logging

router = APIRouter(prefix="/api/v1/blackboard", tags=["blackboard"])
security = HTTPBearer()
logger = logging.getLogger(__name__)

blackboard_service = BlackboardService()
_executor = None

def _get_executor():
    global _executor
    if _executor is None:
        from concurrent.futures import ThreadPoolExecutor
        _executor = ThreadPoolExecutor(max_workers=4)
    return _executor


class BlackboardCookieRequest(BaseModel):
    """Blackboard Cookie请求体模型"""
    cookies: str
    ics_url: str | None = None


class BlackboardIcsRequest(BaseModel):
    """Blackboard ICS 绑定请求"""
    ics_url: str


def _parse_due(due_str: str):
    """Parse a due date string into (date, date, start_time, end_time).

    Accepts multiple formats: 'YYYY-MM-DD HH:MM', 'YYYY-MM-DD',
    'YYYY-MM-DDTHH:MM:SS', 'YYYY-MM-DD HH:MM:SS'.

    Returns (date, date, start_time, end_time) on success,
    or ('', '', '', '') if unparseable or empty.
    """
    if not due_str:
        return '', '', '', ''
    from datetime import datetime

    due = due_str.strip()
    formats = (
        ('%Y-%m-%d %H:%M', True),
        ('%Y-%m-%d', False),
        ('%Y-%m-%dT%H:%M:%S', True),
        ('%Y-%m-%d %H:%M:%S', True),
    )
    for fmt, has_time in formats:
        try:
            dt = datetime.strptime(due, fmt)
            date = dt.strftime('%Y-%m-%d')
            if has_time:
                end_time = dt.strftime('%H:%M')
                start_hour = dt.replace(minute=0).strftime('%H:%M')
                return date, date, start_hour, end_time
            return date, date, '23:00', '23:59'
        except ValueError:
            continue
    return '', '', '', ''


@router.get("/status")
async def get_bb_status(user_id: str = Depends(get_current_user_id)):
    """获取Blackboard绑定状态（从DB读取）"""
    from local_backend.database.code.command.database_command import list_events_by_user

    result = blackboard_service.get_blackboard_status(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '获取状态失败'))

    bb_courses = list_events_by_user(user_id, event_type="course", event_source="blackboard")
    assignments = list_events_by_user(user_id, event_type="assignment", event_source="blackboard")

    result['courses_count'] = len(bb_courses)
    result['assignments_count'] = len(assignments)
    result['course_names'] = [c.get('event_title', '') for c in bb_courses[:5]]
    return result

@router.post("/bind")
async def bind_with_cookie(request: BlackboardCookieRequest, user_id: str = Depends(get_current_user_id)):
    """使用Cookie绑定Blackboard账号
    
    通过Tauri等方式获取Blackboard的Cookie后，传递给后端完成绑定。
    
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
            blackboard_service.bind_with_cookie,
            user_id, cookies, request.ics_url
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message', '绑定失败'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"BB bind 崩溃: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}")

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


@router.post("/bind-ics")
async def bind_with_ics(request: BlackboardIcsRequest, user_id: str = Depends(get_current_user_id)):
    """使用 ICS 日历链接绑定 Blackboard，无需 CAS 登录"""
    if not request.ics_url:
        raise HTTPException(status_code=400, detail="ics_url 不能为空")
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            _get_executor(),
            blackboard_service.bind_with_ics,
            user_id, request.ics_url
        )
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message', '绑定失败'))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"BB ICS bind 崩溃: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {e}")


@router.get("/assignments")
async def get_bb_assignments(user_id: str = Depends(get_current_user_id)):
    """获取Blackboard作业列表（仅未来事件，去重）"""
    import json
    from datetime import datetime
    from local_backend.database.code.command.database_command import list_events_by_user

    assignment_events = list_events_by_user(user_id, event_type="assignment", event_source="blackboard")
    if not assignment_events:
        raise HTTPException(status_code=404, detail='Blackboard作业数据为空')

    today = datetime.now().strftime('%Y-%m-%d')
    events = []
    todos = []
    for item in assignment_events:
        item_name = item.get('event_title', '未命名')
        due_str = item.get('event_end_time', '')
        start, end, start_time, end_time = _parse_due(due_str)
        if not start:
            continue
        if start < today:
            continue

        course_name = "Blackboard"
        meta = {}
        if item.get("event_meta_json"):
            try:
                meta = json.loads(item["event_meta_json"])
            except (json.JSONDecodeError, TypeError):
                pass
        course_name = meta.get("course_name", course_name)

        events.append({
            'title': item_name,
            'start': start,
            'end': end,
            'startTime': start_time,
            'endTime': end_time,
            'priority': 0,
            'color': '#ff3b30',
            'description': f'课程: {course_name}',
            'source': 'blackboard',
            'isTodo': True,
        })

        todos.append({
            'title': item_name,
            'completed': False,
            'start': start,
            'end': end,
            'priority': 0,
            'color': '#ff3b30',
            'description': f'课程: {course_name}',
            'source': 'blackboard',
        })

    return {
        'success': True,
        'events': events,
        'todos': todos,
        'total_courses': 1,
        'total_events': len(events),
        'total_todos': len(todos),
    }
