from fastapi import APIRouter, HTTPException, Header
from presentation.schemas import SyncRequest, SyncResponse, SyncToClientResponse
from service.sync_service import SyncService
import logging

logger = logging.getLogger("server.sync")

router = APIRouter(prefix="/sync", tags=["Sync"])
sync_service = SyncService()


@router.post("/from-client", response_model=SyncResponse)
async def sync_from_client(sync_data: SyncRequest, x_user_id: str = Header(...)):
    logger.info(f"接收客户端同步: user={x_user_id}, type={sync_data.data_type}, count={len(sync_data.data) if sync_data.data else 0}")
    user_id = x_user_id
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    result = sync_service.sync_from_client(user_id, sync_data.data_type, sync_data.data)
    logger.info(f"同步完成: user={x_user_id}, type={sync_data.data_type}, synced={result['synced_count']}")
    return SyncResponse(
        success=result['success'],
        message=result['message'],
        synced_count=result['synced_count']
    )


@router.get("/to-client", response_model=SyncToClientResponse)
async def sync_to_client(data_type: str, x_user_id: str = Header(...)):
    logger.info(f"客户端拉取数据: user={x_user_id}, type={data_type}")
    user_id = x_user_id
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    result = sync_service.sync_to_client(user_id, data_type)
    logger.info(f"数据推送完成: user={x_user_id}, type={data_type}, count={result['synced_count']}")
    return SyncToClientResponse(
        success=result['success'],
        message=result['message'],
        data=result['data'],
        synced_count=result['synced_count']
    )
