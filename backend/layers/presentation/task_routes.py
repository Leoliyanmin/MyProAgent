from fastapi import APIRouter, Depends, HTTPException
from layers.presentation.schemas import TaskCreate, TaskUpdate, TaskResponse
from layers.presentation.dependencies import get_current_user_id
from layers.service.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])
task_service = TaskService()


@router.post("/", response_model=dict)
async def create_task(
    task_data: TaskCreate,
    user_id: int = Depends(get_current_user_id)
):
    result = task_service.create_task(user_id, task_data.dict())
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    return result


@router.get("/", response_model=list)
async def get_tasks(user_id: int = Depends(get_current_user_id)):
    return task_service.get_user_tasks(user_id)


@router.put("/{task_id}", response_model=dict)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    user_id: int = Depends(get_current_user_id)
):
    update_dict = {k: v for k, v in task_data.dict().items() if v is not None}
    result = task_service.update_task(task_id, update_dict)
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['message'])
    return result


@router.delete("/{task_id}", response_model=dict)
async def delete_task(
    task_id: int,
    user_id: int = Depends(get_current_user_id)
):
    result = task_service.delete_task(task_id)
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['message'])
    return result


@router.get("/study-plan", response_model=dict)
async def get_study_plan(user_id: int = Depends(get_current_user_id)):
    return task_service.get_study_plan(user_id)
