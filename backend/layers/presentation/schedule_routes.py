from fastapi import APIRouter, Depends, HTTPException
from layers.presentation.schemas import ScheduleCreate, ScheduleUpdate, ScheduleResponse
from layers.presentation.dependencies import get_current_user_id
from layers.service.schedule_service import ScheduleService

router = APIRouter(prefix="/schedules", tags=["Schedules"])
schedule_service = ScheduleService()


@router.post("/", response_model=dict)
async def create_schedule(
    schedule_data: ScheduleCreate,
    user_id: int = Depends(get_current_user_id)
):
    result = schedule_service.create_schedule(user_id, schedule_data.dict())
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    return result


@router.get("/", response_model=list)
async def get_schedules(user_id: int = Depends(get_current_user_id)):
    return schedule_service.get_user_schedules(user_id)


@router.put("/{schedule_id}", response_model=dict)
async def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    user_id: int = Depends(get_current_user_id)
):
    update_dict = {k: v for k, v in schedule_data.dict().items() if v is not None}
    result = schedule_service.update_schedule(schedule_id, update_dict)
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['message'])
    return result


@router.delete("/{schedule_id}", response_model=dict)
async def delete_schedule(
    schedule_id: int,
    user_id: int = Depends(get_current_user_id)
):
    result = schedule_service.delete_schedule(schedule_id)
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['message'])
    return result
