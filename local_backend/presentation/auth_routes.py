from fastapi import APIRouter, Depends, HTTPException, Body
from presentation.schemas import UserCreate, UserRegisterWithCode, UserLogin, UserResponse, VerificationCodeRequest, VerificationCodeResponse
from presentation.dependencies import get_current_user_id
from service.user_service import UserService
from business.auth_service import AuthService
from database.code.handle.database_user_setting_handle import UserSettingHandle

router = APIRouter(prefix="/auth", tags=["Authentication"])
user_service = UserService()
auth_service = AuthService()
setting_handle = UserSettingHandle()


@router.post("/verification/send", response_model=VerificationCodeResponse)
async def send_verification_code(request: VerificationCodeRequest):
    result = await auth_service.send_verification_code(request.email, request.purpose)
    return VerificationCodeResponse(
        success=result['success'],
        message=result['message'],
        expires_in=result.get('expires_in'),
        retry_after=result.get('retry_after'),
        test_code=result.get('test_code')
    )


@router.post("/register")
async def register(user_data: UserRegisterWithCode):
    result = await user_service.register_user(user_data.dict())
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
    return {
        "id": user.get("user_id", user.get("id")),
        "email": user.get("user_email", user.get("email")),
        "full_name": user.get("username", user.get("full_name")),
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
    result = setting_handle.update_settings(user_id, fields)
    if not result["ok"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return {"success": True, "message": result["message"]}
