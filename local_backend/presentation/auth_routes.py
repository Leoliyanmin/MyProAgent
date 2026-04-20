from fastapi import APIRouter, Depends, HTTPException
from presentation.schemas import UserCreate, UserRegisterWithCode, UserLogin, UserResponse, VerificationCodeRequest, VerificationCodeResponse
from presentation.dependencies import get_current_user_id
from service.user_service import UserService
from business.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
user_service = UserService()
auth_service = AuthService()


@router.post("/verification/send", response_model=VerificationCodeResponse)
async def send_verification_code(request: VerificationCodeRequest):
    result = await auth_service.send_verification_code(request.email, request.purpose)
    return VerificationCodeResponse(
        success=result['success'],
        message=result['message'],
        expires_in=result.get('expires_in'),
        retry_after=result.get('retry_after')
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


@router.get("/me", response_model=UserResponse)
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # user is already a dict from the database
    return {
        "id": user.get("user_id", user.get("id")),
        "email": user.get("user_email", user.get("email")),
        "full_name": user.get("username", user.get("full_name")),
        "is_active": user.get("user_is_active", user.get("is_active")),
        "created_at": user.get("user_created_at", user.get("created_at"))
    }
