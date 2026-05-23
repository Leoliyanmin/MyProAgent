from fastapi import APIRouter, Depends, HTTPException

from presentation.dependencies import get_current_user_id

router = APIRouter(prefix="/api/v1", tags=["courses"])


@router.get("/courses")
async def get_courses(user_id: str = Depends(get_current_user_id)):
    """获取已同步的TIS课程列表（从DB读取）"""
    from local_backend.database.code.command.database_command import list_tis_courses_by_user, list_tis_events_by_user

    courses_raw = list_tis_courses_by_user(user_id)
    events = list_tis_events_by_user(user_id)

    events_by_course = {}
    for ev in events:
        cid = ev.get('course_id')
        if cid not in events_by_course:
            events_by_course[cid] = []
        events_by_course[cid].append(ev)

    courses = []
    for c in courses_raw:
        cid = c.get('course_id')
        c_events = events_by_course.get(cid, [])

        if c_events:
            ps = min(e.get('period_start', 0) for e in c_events)
            pe = max(e.get('period_end', 0) for e in c_events)
            starts = [e.get('start_time', '') for e in c_events if e.get('start_time')]
            ends = [e.get('end_time', '') for e in c_events if e.get('end_time')]
            periods = f"{ps}-{pe}节" if ps and pe else ''
            start = min(starts) if starts else ''
            end = max(ends) if ends else ''
        else:
            periods = start = end = ''

        courses.append({
            'category_title': c.get('course_name', ''),
            'teacher': c.get('teacher', ''),
            'weeks': c.get('weeks', ''),
            'location': c.get('location', ''),
            'periods': periods,
            'start': start,
            'end': end,
            'category_term': c.get('term', ''),
        })

    return {'success': True, 'courses': courses}
