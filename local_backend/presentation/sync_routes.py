from fastapi import APIRouter, Depends, HTTPException
import requests
from config import settings
from presentation.schemas import SyncRequest, SyncResponse
from presentation.dependencies import get_current_user_id

router = APIRouter(prefix="/sync", tags=["Sync"])


@router.post("/to-server", response_model=SyncResponse)
async def sync_to_server(sync_data: SyncRequest, user_id: int = Depends(get_current_user_id)):
    try:
        response = requests.post(
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


@router.get("/from-server", response_model=SyncResponse)
async def sync_from_server(data_type: str, user_id: int = Depends(get_current_user_id)):
    try:
        response = requests.get(
            f"{settings.SERVER_BACKEND_URL}/sync/to-client",
            params={"data_type": data_type},
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
