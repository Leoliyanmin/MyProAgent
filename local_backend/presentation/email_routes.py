from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from service.email_service import EmailService
from presentation.dependencies import get_current_user_id

router = APIRouter(prefix="/api/v1/email", tags=["email"])
security = HTTPBearer()

email_service = EmailService()


class EmailBindRequest(BaseModel):
    email_address: str
    app_password: str


class EmailSendRequest(BaseModel):
    title: str
    context: str
    receiver: str


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
    max_messages: int = Query(default=50, ge=1, le=200, description="最大同步邮件数"),
    user_id: str = Depends(get_current_user_id),
):
    result = email_service.sync_email_data(user_id, max_messages=max_messages)
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
