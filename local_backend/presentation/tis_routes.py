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
    """获取TIS绑定状态"""
    import json
    import os
    result = tis_service.get_tis_status(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '获取状态失败'))

    json_path = os.path.join(os.path.expanduser('~'), '.proagent', 'bind_data', f'{user_id}_tis_schedule.json')
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        result['bind_time'] = data.get('bind_time', '')
        result['student_id'] = data.get('student_id', '')
        result['student_name'] = data.get('student_name', '')
        result['total_courses'] = data.get('total_courses', 0)
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


@router.post("/sync")
async def sync_tis_data(user_id: str = Depends(get_current_user_id)):
    """同步TIS课表数据"""
    result = tis_service.sync_tis_data(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '同步失败'))
    return result


@router.get("/schedule")
async def get_tis_schedule(user_id: str = Depends(get_current_user_id)):
    """获取TIS课表数据，转换为日历事件格式返回（整学期展开）"""
    import json
    import os
    import re
    from datetime import datetime, timedelta

    save_dir = os.path.join(os.path.expanduser('~'), '.proagent', 'bind_data')
    json_path = os.path.join(save_dir, f'{user_id}_tis_schedule.json')

    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail='未找到TIS课表数据，请先绑定TIS账号')

    with open(json_path, 'r', encoding='utf-8') as f:
        tis_data = json.load(f)

    schedule = tis_data.get('schedule', {})
    if not schedule:
        raise HTTPException(status_code=404, detail='TIS课表数据为空')

    weekday_map = {
        '星期一': 0, '星期二': 1, '星期三': 2,
        '星期四': 3, '星期五': 4, '星期六': 5, '星期日': 6,
    }

    current_week = int(tis_data.get('week', '1') or '1')
    today = datetime.now()
    semester_monday = today - timedelta(days=today.weekday() + (current_week - 1) * 7)

    def parse_weeks(weeks_str):
        result = set()
        if not weeks_str:
            return result
        for part in weeks_str.replace('，', ',').split(','):
            part = part.strip()
            m = re.match(r'(\d+)-(\d+)(双|单)?周', part)
            if m:
                start, end = int(m.group(1)), int(m.group(2))
                parity = m.group(3)
                for w in range(start, end + 1):
                    if parity == '双' and w % 2 != 0:
                        continue
                    if parity == '单' and w % 2 != 1:
                        continue
                    result.add(w)
            else:
                m2 = re.match(r'(\d+)周', part)
                if m2:
                    result.add(int(m2.group(1)))
        return result

    events = []
    for day_name, courses in schedule.items():
        dow = weekday_map.get(day_name)
        if dow is None:
            continue

        for course in courses:
            title = course.get('title', '未知课程')
            location = course.get('location', '')
            teacher = course.get('teacher', '')
            start_time = course.get('start', '')
            end_time = course.get('end', '')
            periods = course.get('periods', '')
            weeks_str = course.get('weeks', '')

            active_weeks = parse_weeks(weeks_str)
            if not active_weeks:
                active_weeks = {current_week}

            description_parts = []
            if teacher:
                description_parts.append(f'教师: {teacher}')
            if location:
                description_parts.append(f'地点: {location}')
            if periods:
                description_parts.append(f'节次: {periods}')
            if weeks_str:
                description_parts.append(f'周次: {weeks_str}')
            description = '\n'.join(description_parts)

            for week_num in sorted(active_weeks):
                offset_days = (week_num - 1) * 7 + dow
                event_date = semester_monday + timedelta(days=offset_days)
                date_str = event_date.strftime('%Y-%m-%d')

                events.append({
                    'title': title,
                    'start': date_str,
                    'end': date_str,
                    'startTime': start_time,
                    'endTime': end_time,
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
