from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    student_id: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserRegisterWithCode(UserBase):
    password: str = Field(..., min_length=8, description="密码长度至少为8位")
    confirm_password: str = Field(..., min_length=8, description="确认密码")
    verification_code: str = Field(..., min_length=6, max_length=6, description="6位验证码")
    code_context: str = Field(..., description="从 /verification/send 返回的 code_context")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class VerificationCodeRequest(BaseModel):
    email: EmailStr
    purpose: str = Field(default="register", description="验证码用途：register或reset_password")


class VerificationCodeResponse(BaseModel):
    success: bool
    message: str
    code_context: Optional[str] = None
    test_code: Optional[str] = None
    expires_in: Optional[int] = None
    retry_after: Optional[int] = None


class SyncRequest(BaseModel):
    data_type: str  # 'schedules', 'tasks', 'chats'
    data: List[Dict[str, Any]]


class SyncResponse(BaseModel):
    success: bool
    message: str
    synced_count: int


class SyncToClientResponse(SyncResponse):
    data: List[Dict[str, Any]]
