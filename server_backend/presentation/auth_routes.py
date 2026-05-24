from fastapi import APIRouter, Depends, HTTPException
from presentation.schemas import UserCreate, UserRegisterWithCode, UserLogin, UserResponse, VerificationCodeRequest, VerificationCodeResponse
from service.user_service import UserService
from business.auth_service import AuthService
import logging

logger = logging.getLogger("server.auth")

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
    logger.info(f"用户注册: {user_data.email}")
    result = user_service.register_user(user_data.dict())
    if not result['success']:
        logger.warning(f"注册失败: {user_data.email} - {result['message']}")
        raise HTTPException(status_code=400, detail=result['message'])
    logger.info(f"注册成功: {user_data.email}")
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
