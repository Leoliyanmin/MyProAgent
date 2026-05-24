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
    test_code: Optional[str] = None


class ScheduleBase(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    event_type: Optional[str] = "personal"
    priority: Optional[str] = Field(default="p2", pattern=r"^p[0-4]$")


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    event_type: Optional[str] = None
    priority: Optional[str] = Field(default=None, pattern=r"^p[0-4]$")


class ScheduleResponse(ScheduleBase):
    id: int
    user_id: str
    source: str
    
    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = "medium"
    status: Optional[str] = "pending"
    linked_schedule_id: Optional[int] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    linked_schedule_id: Optional[int] = None


class TaskResponse(TaskBase):
    id: int
    user_id: str
    
    class Config:
        from_attributes = True


class AgentChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None


class AgentFileManagerMessage(BaseModel):
    message: str
    working_directory: str = Field(..., min_length=1, description="用户输入的文件工作目录")
    session_id: Optional[str] = None


class AgentFileManagerListRequest(BaseModel):
    working_directory: str = Field(..., min_length=1, description="用户输入的文件工作目录")
    relative_path: Optional[str] = Field(default="", description="相对于工作目录的子路径")


class AgentFileManagerEntry(BaseModel):
    name: str
    relative_path: str
    is_directory: bool
    size: Optional[int] = None
    modified_at: Optional[str] = None


class AgentFileManagerListResponse(BaseModel):
    working_directory: str
    current_directory: str
    relative_path: str
    parent_relative_path: Optional[str] = None
    entries: List[AgentFileManagerEntry]


class AgentFileManagerFileCreateRequest(BaseModel):
    working_directory: str = Field(..., min_length=1, description="用户输入的文件工作目录")
    relative_path: Optional[str] = Field(default="", description="相对于工作目录的子目录")
    filename: str = Field(..., min_length=1, description="仅文件名，不含路径")


class AgentFileManagerDirectoryCreateRequest(BaseModel):
    working_directory: str = Field(..., min_length=1, description="用户输入的文件工作目录")
    relative_path: Optional[str] = Field(default="", description="相对于工作目录的子目录")
    dirname: str = Field(..., min_length=1, description="仅目录名，不含路径")


class AgentFileManagerFileRenameRequest(BaseModel):
    working_directory: str = Field(..., min_length=1, description="用户输入的文件工作目录")
    relative_path: Optional[str] = Field(default="", description="相对于工作目录的子目录")
    old_filename: str = Field(..., min_length=1, description="旧文件名")
    new_filename: str = Field(..., min_length=1, description="新文件名")


class AgentFileManagerFileReadRequest(BaseModel):
    working_directory: str = Field(..., min_length=1, description="用户输入的文件工作目录")
    relative_path: Optional[str] = Field(default="", description="相对于工作目录的子目录")
    filename: str = Field(..., min_length=1, description="仅文件名，不含路径")


class AgentFileManagerFileDeleteRequest(BaseModel):
    working_directory: str = Field(..., min_length=1, description="用户输入的文件工作目录")
    relative_path: Optional[str] = Field(default="", description="相对于工作目录的子目录")
    filename: str = Field(..., min_length=1, description="仅文件名，不含路径")


class AgentFileManagerPathDeleteRequest(BaseModel):
    path: str = Field(..., min_length=1, description="要删除的文件的绝对路径或相对于工作目录的路径")
    working_directory: Optional[str] = Field(default=None, description="工作目录（path 为相对路径时必须提供）")


class AgentFileManagerOperationResponse(BaseModel):
    success: bool
    message: str
    working_directory: str
    relative_path: str
    filename: Optional[str] = None
    new_filename: Optional[str] = None


class AgentFileManagerFileReadResponse(BaseModel):
    working_directory: str
    relative_path: str
    filename: str
    content: str


class AgentFileManagerFileUpdateRequest(BaseModel):
    working_directory: str = Field(..., min_length=1, description="用户输入的文件工作目录")
    relative_path: Optional[str] = Field(default="", description="相对于工作目录的子目录")
    filename: str = Field(..., min_length=1, description="仅文件名，不含路径")
    content: str = Field(..., min_length=0, description="文件新内容")


class AgentResponse(BaseModel):
    response: str
    thought_trace: List[Dict[str, str]]
    tool_calls: List[Any]
    requires_confirmation: bool = False
    pending_deletions: List[Dict[str, str]] = []


class ChatHistoryItem(BaseModel):
    id: int
    message: str
    role: str
    tool_calls: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AgentConfigUpdateRequest(BaseModel):
    """Agent 配置更新请求"""
    provider: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None


class AgentConfigUpdateResponse(BaseModel):
    """Agent 配置更新响应"""
    success: bool
    message: str
    provider: Optional[str] = None
    model: Optional[str] = None
    api_base: Optional[str] = None


class AgentTestConnectionResponse(BaseModel):
    """Agent 测试连接响应"""
    success: bool
    status: Optional[int] = None
    message: str
    error: Optional[str] = None
    type: Optional[str] = None


class SyncRequest(BaseModel):
    data_type: str  # 'schedules', 'tasks', 'chats'
    data: List[Dict[str, Any]]


class SyncResponse(BaseModel):
    success: bool
    message: str
    synced_count: int
