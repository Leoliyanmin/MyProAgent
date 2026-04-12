from fastapi import APIRouter, Depends, HTTPException
from typing import List
from presentation.schemas import ScheduleCreate, ScheduleUpdate, ScheduleResponse
from presentation.dependencies import get_current_user_id
from service.schedule_service import ScheduleService

router = APIRouter(prefix="/schedules", tags=["Schedules"])
schedule_service = ScheduleService()


@router.get("/", response_model=List[dict])
async def get_schedules(user_id: str = Depends(get_current_user_id)):
    result = schedule_service.get_schedules(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', 'Failed to get schedules'))
    return result.get('schedules', [])


@router.post("/")
async def create_schedule(schedule_data: ScheduleCreate, user_id: int = Depends(get_current_user_id)):
    result = schedule_service.create_schedule(user_id, schedule_data.dict())
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    return result


@router.put("/{schedule_id}")
async def update_schedule(schedule_id: int, schedule_data: ScheduleUpdate, user_id: str = Depends(get_current_user_id)):
    result = schedule_service.update_schedule(user_id, schedule_id, schedule_data.dict(exclude_unset=True))
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['message'])
    return result


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: int, user_id: str = Depends(get_current_user_id)):
    result = schedule_service.delete_schedule(user_id, schedule_id)
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['message'])
    return result
