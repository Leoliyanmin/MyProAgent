from fastapi import APIRouter, Depends, HTTPException
from presentation.schemas import UserCreate, UserRegisterWithCode, UserLogin, UserResponse, VerificationCodeRequest, VerificationCodeResponse
from service.user_service import UserService
from business.auth_service import AuthService
from database.code.command import database_command as db
import logging

logger = logging.getLogger("server.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])
user_service = UserService()
auth_service = AuthService()


@router.get("/stats")
async def get_stats():
    """返回注册用户和同步统计信息"""
    users = db.list_users()
    sync_states = db.list_sync_states()

    user_list = []
    for u in users:
        uid = u["user_id"] if isinstance(u, dict) else u[0]
        email = u.get("user_email", "") if isinstance(u, dict) else u[2] if len(u) > 2 else ""
        created = u.get("user_created_at", "") if isinstance(u, dict) else u[4] if len(u) > 4 else ""

        sync_info = None
        for s in sync_states:
            sid = s["user_id"] if isinstance(s, dict) else s[0]
            if str(sid) == str(uid):
                sync_info = {
                    "last_synced_at": s.get("user_last_synced_at", "") if isinstance(s, dict) else s[2] if len(s) > 2 else "",
                    "version": s.get("user_version", 1) if isinstance(s, dict) else s[3] if len(s) > 3 else 1,
                }
                break

        # 检查加密数据
        personality = db.get_user_personality(uid)
        events = db.list_events_by_user(uid)

        encrypted_preview = None
        if personality and personality.get("encrypted_data"):
            ed = personality["encrypted_data"]
            encrypted_preview = ed[:80] + ("..." if len(ed) > 80 else "")

        user_list.append({
            "user_id": uid,
            "email": email,
            "created_at": created,
            "sync": sync_info,
            "encrypted": {
                "has_personality": personality is not None,
                "personality_preview": encrypted_preview,
                "event_count": len(events),
            },
        })

    activities = db.list_activities(limit=50)
    activity_list = []
    for a in activities:
        activity_list.append({
            "id": a["id"] if isinstance(a, dict) else a[0],
            "user_id": a["user_id"] if isinstance(a, dict) else a[1],
            "user_email": a["user_email"] if isinstance(a, dict) else a[2],
            "activity_type": a["activity_type"] if isinstance(a, dict) else a[3],
            "detail": a["detail"] if isinstance(a, dict) else a[4],
            "created_at": a["created_at"] if isinstance(a, dict) else a[5],
        })

    return {
        "total_users": len(users),
        "total_synced": len([u for u in user_list if u["sync"]]),
        "users": user_list,
        "recent_activities": activity_list,
    }


@router.post("/verification/send", response_model=VerificationCodeResponse)
async def send_verification_code(request: VerificationCodeRequest):
    result = await user_service.send_verification_code(request.email)
    return VerificationCodeResponse(
        success=result['success'],
        message=result['message'],
        code_context=result.get('code_context'),
        test_code=result.get('test_code'),
        expires_in=result.get('expires_in'),
        retry_after=result.get('retry_after')
    )


@router.post("/register")
async def register(user_data: UserRegisterWithCode):
    logger.info(f"用户注册: {user_data.email}")
    result = user_service.register_user(user_data.dict())
    if not result['success']:
        logger.warning(f"注册失败: {user_data.email} - {result['message']}")
        raise HTTPException(status_code=400, detail=result['message'])
    logger.info(f"注册成功: {user_data.email}")
    db.log_activity(user_data.email, user_data.email, "register",
                    f"用户注册: {user_data.email}")
    return result


@router.post("/login")
async def login(user_data: UserLogin):
    logger.info(f"用户登录: {user_data.email}")
    result = user_service.login_user(user_data.email, user_data.password)
    if not result['success']:
        logger.warning(f"登录失败: {user_data.email}")
        raise HTTPException(status_code=401, detail=result['message'])
    logger.info(f"登录成功: {user_data.email}")
    return result
