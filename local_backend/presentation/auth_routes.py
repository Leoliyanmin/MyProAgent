from fastapi import APIRouter, Depends, HTTPException, Body
from presentation.schemas import UserCreate, UserRegisterWithCode, UserLogin, UserResponse, VerificationCodeRequest, VerificationCodeResponse
from presentation.dependencies import get_current_user_id
from service.user_service import UserService
from business.auth_service import AuthService
from database.code.handle.database_user_setting_handle import UserSettingHandle
from database.code.handle.database_quote_history_handle import QuoteHistoryHandle

router = APIRouter(prefix="/auth", tags=["Authentication"])
user_service = UserService()
auth_service = AuthService()
setting_handle = UserSettingHandle()
quote_history_handle = QuoteHistoryHandle()


@router.post("/verification/send", response_model=VerificationCodeResponse)
async def send_verification_code(request: VerificationCodeRequest):
    result = await auth_service.send_verification_code(request.email, request.purpose)
    return VerificationCodeResponse(
        success=result['success'],
        message=result['message'],
        expires_in=result.get('expires_in'),
        retry_after=result.get('retry_after'),
        code_context=result.get('code_context'),
        test_code=result.get('test_code')
    )


@router.post("/register")
async def register(user_data: UserRegisterWithCode):
    result = await user_service.register_user(user_data.model_dump(by_alias=False))
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    return result


@router.post("/login")
async def login(user_data: UserLogin):
    result = await user_service.login_user(user_data.email, user_data.password)
    if not result['success']:
        raise HTTPException(status_code=401, detail=result['message'])
    return result


@router.get("/me")
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    user = user_service.get_user_by_id(user_id)
    if not user:
        user = user_service.get_user_by_email(user_id)
    if not user:
        from config import settings
        if settings.TEST_MODE:
            email = user_id if '@' in user_id else f'{user_id}@test.local'
            return {
                "id": user_id,
                "email": email,
                "full_name": user_id.split('@')[0] if '@' in user_id else user_id,
                "is_active": True,
                "created_at": "2026-01-01T00:00:00"
            }
        raise HTTPException(status_code=404, detail="User not found")
    full_name = user.get("username", user.get("full_name"))
    if not full_name or "@" in str(full_name):
        settings_data = setting_handle.get_settings(user_id)
        if settings_data.get("ok"):
            data = settings_data.get("data", {}) or {}
            alt = data.get("full_name") or data.get("display_name")
            if alt:
                full_name = alt
    return {
        "id": user.get("user_id", user.get("id")),
        "email": user.get("user_email", user.get("email")),
        "full_name": full_name,
        "is_active": bool(user.get("user_is_active", user.get("is_active", True))),
        "created_at": user.get("user_created_at", user.get("created_at", ""))
    }


@router.get("/settings")
async def get_settings(user_id: str = Depends(get_current_user_id)):
    result = setting_handle.get_settings(user_id)
    if not result["ok"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result["data"]


@router.put("/settings")
async def update_settings(fields: dict = Body(...), user_id: str = Depends(get_current_user_id)):
    full_name = fields.pop("full_name", None)
    username = fields.pop("username", None)
    name_value = full_name or username
    if name_value is not None:
        from local_backend.database.code.command.database_command import upsert_user, upsert_user_setting
        existing = user_service.get_user_by_id(user_id)
        if existing:
            upsert_user(
                user_id=user_id,
                username=name_value,
                user_email=existing.get("user_email", user_id),
                user_is_active=existing.get("user_is_active", 1),
                user_created_at=existing.get("user_created_at", ""),
                user_last_login=existing.get("user_last_login"),
                user_source_device_id=existing.get("user_source_device_id"),
            )
        upsert_user_setting(user_id, full_name=name_value)
    if fields:
        result = setting_handle.update_settings(user_id, fields)
        if not result["ok"]:
            raise HTTPException(status_code=400, detail=result["message"])
        daily_quote = fields.get("daily_quote")
        if daily_quote:
            source = fields.get("daily_quote_source", "custom")
            quote_author = fields.get("daily_quote_author", "")
            quote_from = fields.get("daily_quote_from", "")
            quote_history_handle.add(user_id, daily_quote, source, quote_author, quote_from)
    return {"success": True, "message": "保存成功"}


@router.get("/settings/daily-quote/history")
async def get_daily_quote_history(user_id: str = Depends(get_current_user_id)):
    result = quote_history_handle.get_today(user_id)
    if not result["ok"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result["data"]


# ==================== API Key Management ====================


@router.get("/settings/api-keys")
async def get_api_keys(user_id: str = Depends(get_current_user_id)):
    """List all API keys for the current user (masked)."""
    from database.code.operations.api_key_storage import list_api_keys
    keys = list_api_keys(user_id)
    return {"providers": keys}


@router.put("/settings/api-keys")
async def save_api_key(
    body: dict = Body(...),
    user_id: str = Depends(get_current_user_id),
):
    """Save or update an API key. Pass key_id to edit existing."""
    from database.code.operations.api_key_storage import save_api_key as storage_save
    key_id = storage_save(
        user_id,
        body["provider"],
        body.get("api_key", ""),
        body.get("api_base", ""),
        model=body.get("model", ""),
        key_id=body.get("key_id"),
    )
    return {"success": True, "key_id": key_id}


@router.delete("/settings/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Delete an API key by key_id."""
    from database.code.operations.api_key_storage import delete_api_key
    delete_api_key(user_id, key_id)
    return {"success": True}


@router.post("/settings/api-keys/test")
async def test_api_key_connection(
    body: dict = Body(...),
    user_id: str = Depends(get_current_user_id),
):
    """Test an API key connection."""
    from database.code.operations.api_key_storage import test_api_key, save_api_key as storage_save
    provider = body.get("provider", "")
    api_key = body.get("api_key", "")
    api_base = body.get("api_base", "")
    model = body.get("model", "")
    key_id = body.get("key_id")
    result = test_api_key(provider, api_key, api_base, model=model)
    saved_id = storage_save(user_id, provider, api_key, api_base, model=model,
                 key_id=key_id, last_test_success=result["success"])
    result["key_id"] = saved_id
    return result


@router.post("/settings/api-keys/{key_id}/toggle")
async def toggle_api_key(
    key_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Toggle API key active state by key_id."""
    from database.code.operations.api_key_storage import toggle_api_key
    result = toggle_api_key(user_id, key_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail="API key not found")
    return result

