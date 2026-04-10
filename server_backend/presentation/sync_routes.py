from fastapi import APIRouter, HTTPException, Header
from presentation.schemas import SyncRequest, SyncResponse, SyncToClientResponse
from service.sync_service import SyncService

router = APIRouter(prefix="/sync", tags=["Sync"])
sync_service = SyncService()


@router.post("/from-client", response_model=SyncResponse)
async def sync_from_client(sync_data: SyncRequest, x_user_id: str = Header(...)):
    try:
        user_id = int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    result = sync_service.sync_from_client(user_id, sync_data.data_type, sync_data.data)
    return SyncResponse(
        success=result['success'],
        message=result['message'],
        synced_count=result['synced_count']
    )


@router.get("/to-client", response_model=SyncToClientResponse)
async def sync_to_client(data_type: str, x_user_id: str = Header(...)):
    try:
        user_id = int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    result = sync_service.sync_to_client(user_id, data_type)
    return SyncToClientResponse(
        success=result['success'],
        message=result['message'],
        data=result['data'],
        synced_count=result['synced_count']
    )
