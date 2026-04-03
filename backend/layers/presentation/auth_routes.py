from fastapi import APIRouter, Depends, HTTPException
from layers.presentation.schemas import UserCreate, UserLogin, UserResponse, Token
from layers.presentation.dependencies import get_current_user_id
from layers.service.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])
user_service = UserService()


@router.post("/register", response_model=dict)
async def register(user_data: UserCreate):
    result = user_service.register_user(user_data.dict())
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['message'])
    return result


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    result = user_service.authenticate_user(user_data.email, user_data.password)
    if not result['success']:
        raise HTTPException(status_code=401, detail=result['message'])
    return Token(access_token=result['access_token'], token_type=result['token_type'])


@router.get("/me", response_model=UserResponse)
async def get_current_user(user_id: int = Depends(get_current_user_id)):
    user_profile = user_service.get_user_profile(user_id)
    if not user_profile:
        raise HTTPException(status_code=404, detail="User not found")
    return user_profile
