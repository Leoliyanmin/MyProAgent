from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Table, Text, LargeBinary, JSON, Boolean
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from sqlalchemy import Time

from core.database import Base

# 多对多关联表
user_schedule_association = Table(
    'user_schedule_association',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.user_id')),
    Column('schedule_id', Integer, ForeignKey('schedules.schedule_id'))
)


class User(Base):
    """学生用户实体"""
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    pinyin_name = Column(String(100))
    photo=Column(Text, nullable=True)  # 存储Base64编码的照片
    gender = Column(String(10))
    birth_date = Column(String(20))
    college = Column(String(100))
    dormitory = Column(String(100))
    phone=Column(String(20), unique = True)
    email = Column(String(100), unique = True, nullable=False)
    gpa = Column(Float)
    rank = Column(String(50))
    department = Column(String(100))
    interest = Column(Text, nullable=True)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


    # 一对一关系
    credits = relationship("Credits", back_populates="user", uselist=False)
    # 一对多关系
    deadlines = relationship("Deadline", back_populates="user")
    # 邮件账号与核心用户表解耦，不再通过外键绑定
    # operation_logs = relationship("OperationLog", back_populates="user")
    # 多对多关系
    schedules = relationship("Schedule", secondary=user_schedule_association, back_populates="users")

# class OperationLog(Base):
#     """用户操作日志实体"""
#     __tablename__ = 'operation_logs'

#     id = Column(Integer, primary_key=True)
#     messages = Column(String(500), nullable=False)
#     created_time = Column(DateTime, default=datetime.now)
#     user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)

#     # 多对一关系
#     user = relationship("User", back_populates="operation_logs")

class Schedule(Base):
    __tablename__ = "schedules"
    

    schedule_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    location = Column(String(100))
    start_time = Column(Time)
    end_time = Column(Time)
    teacher = Column(String(100))
    weekday = Column(Integer)  # 星期几，1-7表示周一到周日
    description = Column(String(500))
    schedule_type = Column(String(50)) # schedule类型，如课程、活动
    # 多对多关系    
    users = relationship("User", secondary=user_schedule_association, back_populates="schedules")


class Credits(Base):
    """学分信息表"""
    __tablename__ = 'credits'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False, unique=True)
    total_credit = Column(Float, default=0.0)
    category_credit = Column(JSON, nullable=True)  # 存储各类别学分的JSON数据
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 一对一关系
    user = relationship("User", back_populates="credits")


class Deadline(Base):
    __tablename__ = 'deadlines'

    id = Column(Integer, primary_key=True, autoincrement=True)
    is_user_created = Column(Integer, default=0)  # 0表示否，1表示是
    calendar_name = Column(String(200))
    end_time = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    event_type = Column(String(50))  # 事件类型，如作业、考试等
    color = Column(String(30))

    # 添加外键关联用户
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)

    # 关系定义
    user = relationship("User", back_populates="deadlines")


class EmailRaw(Base):
    """原始邮件 MIME 数据存储表"""

    __tablename__ = 'email_raw'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('email_accounts.user_id'), nullable=False)
    message_id = Column(Text, unique=True, nullable=True)
    mime_content = Column(LargeBinary, nullable=False)
    encoding = Column(String(50), nullable=True)
    stored_time = Column(DateTime, default=datetime.utcnow, nullable=False)

    account = relationship("EmailAccount", back_populates="raw_entries")
    parsed_entries = relationship("EmailParsed", back_populates="raw", cascade="all, delete-orphan")


class EmailParsed(Base):
    """解析后的邮件信息，用于查询展示"""

    __tablename__ = 'email_parsed'

    id = Column(Integer, primary_key=True, autoincrement=True)
    raw_id = Column(Integer, ForeignKey('email_raw.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('email_accounts.user_id'), nullable=False)

    subject = Column(Text, nullable=False)
    sender = Column(Text, nullable=False)
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    attachments = Column(Text, nullable=True)  # JSON 列表，包含 name/size/content_type
    summary = Column(Text, nullable=True)
    received_time = Column(DateTime, nullable=False)

    raw = relationship("EmailRaw", back_populates="parsed_entries")


class EmailAccount(Base):
    """IMAP 凭据存储表，负责自动同步配置。"""

    __tablename__ = 'email_accounts'

    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    email = Column(String(200), unique=True, nullable=False)
    password = Column(Text, nullable=False)
    host = Column(String(200), nullable=False)
    port = Column(Integer, nullable=False, default=993)
    use_ssl = Column(Boolean, nullable=False, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    raw_entries = relationship("EmailRaw", back_populates="account")
    user = relationship("User")


class BBFile(Base):
    """Blackboard课程文件信息表"""
    __tablename__ = 'bb_files'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    course = Column(String(200), nullable=False)
    content = Column(String(200))
    file_url = Column(Text, nullable=False)
    file_name = Column(String(500), nullable=False)
    create_time = Column(DateTime, default=datetime.now)

    # 关系
    # 注意：当前 User 未声明反向关系，查询时按 user_id 过滤即可

class BBGrade(Base):
    """Blackboard 成绩记录"""
    __tablename__ = 'bb_grades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    course_id = Column(String(200), nullable=False)
    course_name = Column(String(500), nullable=True)
    item_name = Column(String(500), nullable=False)
    full_grade = Column(String(100), nullable=False)
    synced_at = Column(DateTime, default=datetime.utcnow)

    # 不声明反向关系，按 user_id / course_id 过滤即可


class ImportantEmail(Base):
    """AI筛选的重要邮件"""
    __tablename__ = 'important_emails'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('email_accounts.user_id'), nullable=False)
    email_parsed_id = Column(Integer, ForeignKey('email_parsed.id'), nullable=False)
    reason = Column(Text, nullable=True) # AI筛选理由
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    email_parsed = relationship("EmailParsed")




