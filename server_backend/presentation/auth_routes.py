from fastapi import APIRouter, Depends, HTTPException
from presentation.schemas import UserCreate, UserLogin, UserResponse
from service.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])
user_service = UserService()


@router.post("/register")
async def register(user_data: UserCreate):
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
