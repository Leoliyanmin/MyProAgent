from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from service.email_service import EmailService
from service.email_priority_service import EmailPriorityService
from presentation.dependencies import get_current_user_id

router = APIRouter(prefix="/api/v1/email", tags=["email"])
security = HTTPBearer()

email_service = EmailService()
email_priority_service = EmailPriorityService()


class EmailBindRequest(BaseModel):
    email_address: str
    app_password: str


class EmailSendRequest(BaseModel):
    title: str
    context: str
    receiver: str


class StarEmailRequest(BaseModel):
    reason: str | None = None


@router.get("/status")
async def get_email_status(user_id: str = Depends(get_current_user_id)):
    result = email_service.get_email_status(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '获取状态失败'))
    return result


@router.post("/bind")
async def bind_email(request: EmailBindRequest, user_id: str = Depends(get_current_user_id)):
    if not request.email_address or not request.app_password:
        raise HTTPException(status_code=400, detail="邮箱地址和客户端专用密码不能为空")

    result = email_service.bind_with_app_password(
        user_id=user_id,
        email_address=request.email_address,
        app_password=request.app_password,
    )
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '绑定失败'))
    return result


@router.post("/sync")
async def sync_email_data(
    max_messages: int = Query(default=None, ge=1, le=200, description="最大同步邮件数"),
    full_sync: bool = Query(default=False, description="是否全量同步(忽略增量记录)"),
    user_id: str = Depends(get_current_user_id),
):
    if max_messages is None:
        from config import settings
        max_messages = settings.EMAIL_SYNC_MAX_MESSAGES
    result = email_service.sync_email_data(user_id, max_messages=max_messages, full_sync=full_sync)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '同步失败'))
    return result


@router.post("/unbind")
async def unbind_email(user_id: str = Depends(get_current_user_id)):
    result = email_service.unbind_email(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '解绑失败'))
    return result


@router.get("/messages")
async def get_email_messages(user_id: str = Depends(get_current_user_id)):
    """获取已同步的邮件列表"""
    result = email_service.get_email_messages(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '获取失败'))
    return result


@router.post("/send")
async def send_email(request: EmailSendRequest, user_id: str = Depends(get_current_user_id)):
    """发送邮件"""
    if not request.title.strip():
        raise HTTPException(status_code=400, detail="邮件标题不能为空")
    if not request.context.strip():
        raise HTTPException(status_code=400, detail="邮件内容不能为空")
    if not request.receiver.strip():
        raise HTTPException(status_code=400, detail="收件人地址不能为空")

    result = email_service.send_email(
        user_id=user_id,
        title=request.title,
        context=request.context,
        receiver=request.receiver,
    )
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '发送失败'))
    return result


@router.delete("/messages/{message_id}")
async def delete_email_message(message_id: int, user_id: str = Depends(get_current_user_id)):
    result = email_service.delete_email_message(user_id, message_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '删除失败'))
    return result


@router.get("/trash")
async def get_trash(user_id: str = Depends(get_current_user_id)):
    result = email_service.get_trash_messages(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '获取失败'))
    return result


@router.post("/messages/{message_id}/restore")
async def restore_message(message_id: int, user_id: str = Depends(get_current_user_id)):
    result = email_service.restore_email_message(user_id, message_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '恢复失败'))
    return result


@router.delete("/messages/{message_id}/permanent")
async def permanent_delete_message(message_id: int, user_id: str = Depends(get_current_user_id)):
    result = email_service.permanent_delete_email(user_id, message_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '删除失败'))
    return result


@router.delete("/trash")
async def empty_trash(user_id: str = Depends(get_current_user_id)):
    result = email_service.empty_trash(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '清空失败'))
    return result


@router.post("/prioritize")
async def prioritize_emails(user_id: str = Depends(get_current_user_id)):
    """结合用户画像和日程，AI 分析邮件重要性，返回 top5 置顶"""
    result = await email_priority_service.prioritize(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '分析失败'))
    return result


@router.post("/messages/{message_id}/star")
async def star_email_message(message_id: int, request: StarEmailRequest | None = None, user_id: str = Depends(get_current_user_id)):
    """手动星标一封邮件"""
    reason = request.reason if request else None
    result = email_service.star_email(user_id, message_id, reason or '手动标注')
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '星标失败'))
    return result


@router.delete("/messages/{message_id}/star")
async def unstar_email_message(message_id: int, user_id: str = Depends(get_current_user_id)):
    """取消星标"""
    result = email_service.unstar_email(user_id, message_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '取消星标失败'))
    return result


@router.get("/starred")
async def get_starred_emails(user_id: str = Depends(get_current_user_id)):
    """获取所有星标邮件（含完整内容 + 原因 + 来源）"""
    result = email_service.get_starred_emails(user_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', '获取失败'))
    return result
