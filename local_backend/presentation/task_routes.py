from fastapi import APIRouter, Depends, HTTPException
from typing import List
from presentation.schemas import TaskCreate, TaskUpdate, TaskResponse
from presentation.dependencies import get_current_user_id
from service.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])
task_service = TaskService()


@router.get("/", response_model=List[dict])
async def get_tasks(user_id: str = Depends(get_current_user_id)):
    result = task_service.get_tasks(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', 'Failed to get tasks'))
    return result.get('tasks', [])


@router.post("/")
async def create_task(task_data: TaskCreate, user_id: str = Depends(get_current_user_id)):
    result = task_service.create_task(user_id, task_data.dict())
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    return result


@router.put("/{task_id}")
async def update_task(task_id: int, task_data: TaskUpdate, user_id: str = Depends(get_current_user_id)):
    result = task_service.update_task(user_id, task_id, task_data.dict(exclude_unset=True))
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['message'])
    return result


@router.delete("/{task_id}")
async def delete_task(task_id: int, user_id: str = Depends(get_current_user_id)):
    result = task_service.delete_task(user_id, task_id)
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['message'])
    return result


@router.get("/study-plan")
async def get_study_plan(user_id: str = Depends(get_current_user_id)):
    return task_service.get_study_plan(user_id)
