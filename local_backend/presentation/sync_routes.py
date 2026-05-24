from fastapi import APIRouter, Depends, HTTPException
import httpx
from config import settings
from presentation.schemas import SyncRequest, SyncResponse
from presentation.dependencies import get_current_user_id

router = APIRouter(prefix="/sync", tags=["Sync"])

_client: httpx.AsyncClient | None = None


async def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


@router.post("/to-server", response_model=SyncResponse)
async def sync_to_server(sync_data: SyncRequest, user_id: str = Depends(get_current_user_id)):
    try:
        client = await _get_client()
        response = await client.post(
            f"{settings.SERVER_BACKEND_URL}/sync/from-client",
            json=sync_data.dict(),
            headers={"X-User-ID": str(user_id)}
        )
        response.raise_for_status()
        result = response.json()
        return SyncResponse(
            success=result['success'],
            message=result['message'],
            synced_count=result['synced_count']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/from-server")
async def sync_from_server(sync_data: SyncRequest, user_id: str = Depends(get_current_user_id)):
    try:
        client = await _get_client()
        response = await client.get(
            f"{settings.SERVER_BACKEND_URL}/sync/to-client",
            params={"data_type": sync_data.data_type},
            headers={"X-User-ID": user_id}
        )
        response.raise_for_status()
        result = response.json()
        return {
            'success': result['success'],
            'message': result['message'],
            'data': result.get('data', []),
            'synced_count': result['synced_count']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/tasks")
async def sync_tasks(user_id: str = Depends(get_current_user_id)):
    """拉取 Agent 创建的任务，返回给前端"""
    try:
        from service.task_service import TaskService
        task_service = TaskService()
        result = task_service.get_tasks(user_id)
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('message', '获取任务失败'))
        return {
            'success': True,
            'tasks': result.get('tasks', [])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"任务同步失败: {str(e)}")