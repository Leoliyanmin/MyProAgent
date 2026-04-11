from fastapi import APIRouter, Depends, HTTPException
from presentation.schemas import UserCreate, UserRegisterWithCode, UserLogin, UserResponse, VerificationCodeRequest, VerificationCodeResponse
from service.user_service import UserService
from business.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
user_service = UserService()
auth_service = AuthService()


@router.post("/verification/send", response_model=VerificationCodeResponse)
async def send_verification_code(request: VerificationCodeRequest):
    result = auth_service.send_verification_code(request.email, request.purpose)
    return VerificationCodeResponse(
        success=result['success'],
        message=result['message'],
        expires_in=result.get('expires_in'),
        retry_after=result.get('retry_after')
    )


@router.post("/register")
async def register(user_data: UserRegisterWithCode):
    result = user_service.register_user(user_data.dict())
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    return result


@router.post("/login")
async def login(user_data: UserLogin):
    result = user_service.login_user(user_data.email, user_data.password)
    if not result['success']:
        raise HTTPException(status_code=401, detail=result['message'])
    return result
