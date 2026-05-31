from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from presentation.dependencies import get_current_user_id
from local_backend.database.code.handle.database_activity_log_handle import ActivityLogHandle

router = APIRouter(prefix="/activity", tags=["activity"])

_handle = ActivityLogHandle()


class ActivityLogBatch(BaseModel):
    logs: list[dict]


@router.get("/log")
async def get_activity_logs(
    user_id: str = Depends(get_current_user_id),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
):
    result = _handle.list(user_id, from_date, to_date)
    if not result["ok"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=result["status"], detail=result["message"])
    return result["data"]


@router.post("/log")
async def record_activity_logs(
    body: ActivityLogBatch,
    user_id: str = Depends(get_current_user_id),
):
    result = _handle.record_batch(user_id, body.logs)
    if not result["ok"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=result["status"], detail=result["message"])
    return result


@router.get("/heatmap")
async def get_activity_heatmap(
    user_id: str = Depends(get_current_user_id),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
):
    result = _handle.heatmap(user_id, from_date, to_date)
    if not result["ok"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=result["status"], detail=result["message"])
    return result["data"]
