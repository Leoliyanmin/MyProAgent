from fastapi import APIRouter, Depends, HTTPException

from presentation.dependencies import get_current_user_id

router = APIRouter(prefix="/api/v1", tags=["courses"])


@router.get("/courses")
async def get_courses(user_id: str = Depends(get_current_user_id)):
    """获取已同步的TIS课程列表（从DB读取）"""
    import json
    from local_backend.database.code.command.database_command import list_events_by_user

    events = list_events_by_user(user_id, event_type="course", event_source="tis")

    courses = []
    for ev in events:
        meta = {}
        if ev.get("event_meta_json"):
            try:
                meta = json.loads(ev["event_meta_json"])
            except (json.JSONDecodeError, TypeError):
                pass

        schedule_events = meta.get("schedule_events", [])
        if schedule_events:
            ps = min(e.get("period_start", 0) for e in schedule_events)
            pe = max(e.get("period_end", 0) for e in schedule_events)
            starts = [e.get("start_time", "") for e in schedule_events if e.get("start_time")]
            ends = [e.get("end_time", "") for e in schedule_events if e.get("end_time")]
            periods = f"{ps}-{pe}节" if ps and pe else ""
            start = min(starts) if starts else ""
            end = max(ends) if ends else ""
        else:
            periods = start = end = ""

        courses.append({
            "category_title": ev.get("event_title", ""),
            "teacher": meta.get("teacher", ""),
            "weeks": meta.get("weeks", ""),
            "location": ev.get("event_location", meta.get("location", "")),
            "periods": periods,
            "start": start,
            "end": end,
            "category_term": meta.get("term", ""),
        })

    return {"success": True, "courses": courses}
