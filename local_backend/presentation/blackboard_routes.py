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


@router.get("/status")
async def get_bb_status(user_id: str = Depends(get_current_user_id)):
    """获取Blackboard绑定状态"""
    import json
    import os
    result = blackboard_service.get_blackboard_status(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '获取状态失败'))

    json_path = os.path.join(os.path.expanduser('~'), '.proagent', 'bind_data', f'{user_id}_blackboard_courses.json')
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        result['bind_time'] = data.get('bind_time', '')
        result['courses_count'] = len(data.get('courses', []))
        course_names = [c.get('name', '') for c in data.get('courses', [])]
        result['course_names'] = course_names[:5]
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
            user_id, cookies
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


@router.get("/assignments")
async def get_bb_assignments(user_id: str = Depends(get_current_user_id)):
    """获取Blackboard作业列表，转换为日历事件+待办格式返回"""
    save_dir = os.path.join(os.path.expanduser('~'), '.proagent', 'bind_data')
    json_path = os.path.join(save_dir, f'{user_id}_blackboard_courses.json')

    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail='未找到Blackboard数据，请先绑定Blackboard账号')

    with open(json_path, 'r', encoding='utf-8') as f:
        bb_data = json.load(f)

    courses = bb_data.get('courses', [])
    if not courses:
        raise HTTPException(status_code=404, detail='Blackboard课程数据为空')

    events = []
    todos = []
    for course in courses:
        course_name = course.get('name', '未知课程')
        all_items = []
        for item in course.get('upload_assignments', []):
            all_items.append(('作业', item))
        for item in course.get('announcements', []):
            all_items.append(('公告', item))
        for item in course.get('course_materials', []):
            all_items.append(('资料', item))

        if not all_items:
            events.append({
                'title': course_name,
                'start': '', 'end': '', 'startTime': '', 'endTime': '',
                'priority': 1, 'color': '#ff9500',
                'description': f'课程: {course_name}', 'source': 'blackboard',
                'isTodo': False,
            })
            continue

        for item_type, item in all_items:
            item_name = item.get('label', item.get('title', item.get('name', '未命名')))
            title = f"[{course_name}] {item_name}"

            description_parts = [f'课程: {course_name}', f'类型: {item_type}']
            content_blocks = item.get('content_blocks', [])
            for block in content_blocks[:3]:
                if isinstance(block, dict):
                    text = block.get('text', '')
                    if text and len(text) < 200:
                        description_parts.append(text)
            description = '\n'.join(description_parts)

            due_date = item.get('due_date', '') or item.get('deadline', '')

            events.append({
                'title': title,
                'start': due_date or '',
                'end': due_date or '',
                'startTime': '', 'endTime': '',
                'priority': 1 if item_type == '作业' else 2,
                'color': '#ff9500',
                'description': description,
                'source': 'blackboard',
                'isTodo': item_type == '作业',
                'dueDate': due_date,
            })

            if item_type == '作业':
                todos.append({
                    'title': title,
                    'completed': False,
                    'start': due_date or '',
                    'end': due_date or '',
                    'priority': 1,
                    'color': '#ff9500',
                    'description': description,
                    'source': 'blackboard',
                })

    return {
        'success': True,
        'events': events,
        'todos': todos,
        'total_courses': len(courses),
        'total_events': len(events),
        'total_todos': len(todos),
    }