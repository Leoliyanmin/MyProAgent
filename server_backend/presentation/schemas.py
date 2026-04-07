from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    student_id: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SyncRequest(BaseModel):
    data_type: str  # 'schedules', 'tasks', 'chats'
    data: List[Dict[str, Any]]


class SyncResponse(BaseModel):
    success: bool
    message: str
    synced_count: int


class SyncToClientResponse(SyncResponse):
    data: List[Dict[str, Any]]
