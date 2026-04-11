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


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: str
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
    expires_in: Optional[int] = None
    retry_after: Optional[int] = None


class ScheduleBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    event_type: Optional[str] = "personal"


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    event_type: Optional[str] = None


class ScheduleResponse(ScheduleBase):
    id: int
    user_id: int
    source: str
    
    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = "medium"
    status: Optional[str] = "pending"


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class TaskResponse(TaskBase):
    id: int
    user_id: int
    
    class Config:
        from_attributes = True


class AgentChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None


class AgentResponse(BaseModel):
    response: str
    thought_trace: List[Dict[str, str]]
    tool_calls: List[Any]
    requires_confirmation: bool


class ChatHistoryItem(BaseModel):
    id: int
    message: str
    role: str
    tool_calls: Optional[str] = None
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
