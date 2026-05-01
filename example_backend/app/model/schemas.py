from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import time, datetime
from typing import Literal

class LoginRequest(BaseModel):
    sid: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class CreditsInfo(BaseModel):
    id: int
    user_id: int
    total_credit: float
    category_credit: Optional[Dict[str, float]] = None
    update_time: datetime

    class Config:
        from_attributes = True


class UserInDB(BaseModel):
    user_id: int
    name: str
    pinyin_name: str
    photo: str | None = None  # Base64编码的照片
    gender: str
    birth_date: str
    college: str
    dormitory: str
    phone: str
    email: str
    gpa: float | None = None
    rank: str | None = None
    department: str
    interest: str | None = None
    credits: Optional[CreditsInfo] = None  # 关联的学分信息

    class Config:
        from_attributes = True

class ScheduleCreate(BaseModel):
    name: str
    location: Optional[str] = None
    start_time: time
    end_time: time
    teacher: Optional[str] = None
    weekday: int
    description: str
    schedule_type: str

class Schedule(ScheduleCreate):
    schedule_id: int

    class Config:
        from_attributes = True

class DDLCreate(BaseModel):
    title: str
    end_time: str = Field(..., alias="end")
    calendar_name: Optional[str] = None
    event_type: Optional[str] = None
    color: Optional[str] = None

    class Config:
        populate_by_name = True


class EmailAttachmentMeta(BaseModel):
    name: str
    size: int = 0
    content_type: Optional[str] = None


class EmailListItem(BaseModel):
    id: int
    raw_id: Optional[int] = None
    subject: str
    sender: str
    received_time: datetime
    snippet: str
    summary: Optional[str] = None
    has_attachments: bool


class EmailListResponse(BaseModel):
    total: int
    items: List[EmailListItem]


class EmailDetail(BaseModel):
    id: int
    raw_id: Optional[int] = None
    subject: str
    sender: str
    received_time: datetime
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    attachments: List[EmailAttachmentMeta] = Field(default_factory=list)
    summary: Optional[str] = None
    message_id: Optional[str] = None
    encoding: Optional[str] = None
    stored_time: Optional[datetime] = None
    mime_content: Optional[str] = None

    class Config:
        from_attributes = True


class EmailLoginRequest(BaseModel):
    user_id: int
    host: str
    port: int = 993
    email: str
    encrypted_password: Optional[str] = None
    password: Optional[str] = None
    use_ssl: bool = True


class EmailLoginResponse(BaseModel):
    success: bool
    message: str


class EmailSyncResponse(BaseModel):
    fetched: int
    stored: int
    skipped: int


class EmailAttachmentPayload(BaseModel):
    filename: str
    content: str
    content_type: str = "application/octet-stream"


class EmailSendRequest(BaseModel):
    subject: str
    to: List[str]
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[EmailAttachmentPayload]] = None


class EmailSendResponse(BaseModel):
    success: bool
    message: str


class EmailAttachmentUploadResponse(BaseModel):
    filename: str
    content_type: str
    size: int
    content: str


class EmailLogoutResponse(BaseModel):
    success: bool
    deleted_parsed: int
    deleted_raw: int
    deleted_accounts: int
    deleted_important: int = 0
    message: str


class InterestUpdate(BaseModel):
    interest: str

# 1. 定义单条消息结构
class Message(BaseModel):
    role: str  # 'user', 'assistant', or 'system'
    content: str
    
# 2. 定义请求体结构 (符合 Vercel 标准)
class ChatRequest(BaseModel):
    messages: List[Message]
    # llm 模型名称可以作为 body 的可选参数，这样更灵活
    llm: Optional[str] = "gpt-4o"


class BBFileInfo(BaseModel):
    id: int
    user_id: int
    course: str
    content: Optional[str] = None
    file_url: str
    file_name: str
    create_time: datetime

    class Config:
        from_attributes = True

class BBFileSyncResponse(BaseModel):
    success: bool
    count: int
    message: str

class ImportantEmailResponse(BaseModel):
    id: int
    email_id: int
    subject: str
    sender: str
    summary: Optional[str] = None
    reason: Optional[str] = None
    received_time: datetime

    class Config:
        from_attributes = True


# 活动推荐类型与结构
ActivityType = Literal["course", "sport", "study", "custom"]

class ActivityRecommendation(BaseModel):
    name: str
    time: Optional[str] = None  # 统一用字符串表达时间或时间范围，格式由AI生成
    location: Optional[str] = None
    type: ActivityType

class ActivityRecommendationsResponse(BaseModel):
    items: List[ActivityRecommendation]


class BBGradeInfo(BaseModel):
    id: int
    user_id: int
    course_id: str
    course_name: str | None = None
    item_name: str
    full_grade: str
    synced_at: datetime | None = None

    class Config:
        from_attributes = True


class BBGradeSyncResponse(BaseModel):
    success: bool
    count: int
    message: str
