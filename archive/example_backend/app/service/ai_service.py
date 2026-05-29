import openai
import os
import json
import re
from datetime import datetime, date, time as dtime
from sqlalchemy.orm import Session
from abc import ABC, abstractmethod # 用于抽象基类

from fastapi import UploadFile
# 假设您在 core.config 中定义了必要的配置
from core.config import OPENAI_API_KEY, BASE_URL, DATABASE_URL 

# --- LangChain 依赖 ---
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import Tool, StructuredTool # Added StructuredTool
from langchain_core.prompts import ChatPromptTemplate 
# ----------------------

from crud import schedule, user, ddl, email, credits, important_email # 假设存在这些 CRUD 模块
from model import schemas
# Added imports for email functionality
from core import email_crypto # 假设此模块用于加密解密
from service.email.email_send_service import SMTPMailService # 假设存在此邮件服务类
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, Field
from typing import Tuple
from collections import deque

# --- 会话级短期记忆：在单个对话框内保留最近若干轮消息 ---
# 设计目标：
# - 作用域：仅当前进程，非持久化；适合“对话框”的短期记忆。
# - 键：conversation_id（由前端或路由生成并传入）。
# - 值：deque，保存最近 MAX_TURNS 条消息记录。
# - TTL：可选的时间戳检查，简单版本不实现过期自动清理，提供手动 reset API。
_conversation_memories: dict[str, deque] = {}
MEMORY_MAX_TURNS = 8  # 每个会话最多保留最近 8 条消息（用户 + 助手混合）

def _memory_get(conversation_id: str) -> deque:
    if conversation_id not in _conversation_memories:
        _conversation_memories[conversation_id] = deque(maxlen=MEMORY_MAX_TURNS)
    return _conversation_memories[conversation_id]

def reset_conversation_memory(conversation_id: str) -> None:
    """清空指定会话的短期记忆。"""
    _conversation_memories.pop(conversation_id, None)

api_key = OPENAI_API_KEY
base_url = BASE_URL

if not api_key:
    raise ValueError("错误: 环境变量 OPENAI_API_KEY 未设置。")

client = openai.OpenAI(
    api_key = api_key,
    base_url = base_url
)

# 全局变量或缓存
_sql_agent_executors = {}  # 改为字典，key 是模型名，value 是对应的 agent
_sql_db = None

# --- 辅助函数：处理 JSON 中的日期时间序列化 ---
def _serialize_datetime(obj):
    """辅助函数：处理 JSON 中的日期时间序列化"""
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    return str(obj)

# ====================================================================
#              1. Model Context Protocol (MCP) 实现 (RAG 聊天)
# ====================================================================

## 1.1 MCP 抽象基类 (接口定义)
class MCPContextSource(ABC):
    """上下文源的抽象基类。用于 RAG 聊天上下文。"""
    @property
    @abstractmethod
    def source_key(self) -> str:
        """返回在最终 JSON 中使用的键名 (e.g., 'user_info')"""
        pass

    @abstractmethod
    def retrieve_context(self, db: Session, user_id: int) -> dict | list | None:
        """检索上下文数据。"""
        pass

## 1.2 现有 RAG 上下文源的实现

class UserContextSource(MCPContextSource):
    source_key = "user_info"
    def retrieve_context(self, db: Session, user_id: int) -> dict | None:
        users = user.get_user_by_sid(db, user_id)
        if users:
            return {
                "name": users.name,
                "gender": users.gender,
                "birth_date": users.birth_date,
                "college": users.college,
                "gpa": users.gpa,
                "rank": users.rank,
                "interest": users.interest,
                "department": users.department
            }
        return None

class ScheduleContextSource(MCPContextSource):
    source_key = "schedules"
    def retrieve_context(self, db: Session, user_id: int) -> list | None:
        schedules = schedule.get_schedule_by_sid(db, user_id)
        if schedules:
            return [
                {
                    "name": sch.name,
                    "location": sch.location,
                    "start_time": sch.start_time,
                    "end_time": sch.end_time,
                    "weekday": sch.weekday,
                    "type": sch.schedule_type,
                } for sch in schedules
            ]
        return None

class DeadlineContextSource(MCPContextSource):
    source_key = "deadlines"
    def retrieve_context(self, db: Session, user_id: int) -> list | None:
        ddls = ddl.get_ddl_by_sid(db, user_id)
        if ddls:
            return [
                {
                    "title": d.title,
                    "end_time": d.end_time,
                    "event_type": d.event_type,
                    "course": d.calendar_name,
                } for d in ddls
            ]
        return None
    
class CreditsContextSource(MCPContextSource):
    source_key = "credits_info"
    def retrieve_context(self, db: Session, user_id: int) -> dict | None:
        credit = credits.get_credits_by_user_id(db, user_id)
        if credit:
            return {
                "total_credit": credit.total_credit
            }
        return None
    
class EmailContextSource(MCPContextSource):
    source_key = "emails"
    def retrieve_context(self, db: Session, user_id: int) -> list | None:
        emails = email.get_email_by_sid(db, user_id)
        if emails:
            return [
                {
                    "subject": em.subject,
                    "sender": em.sender,
                    "body_text": em.body_text,
                    "received_time": em.received_time,
                } for em in emails
            ]
        return None


## 1.3 RAG MCP 管理器
class MCPManager:
    """管理所有上下文源，并执行上下文检索。"""
    def __init__(self):
        # 注册所有可用的上下文源
        self._sources: list[MCPContextSource] = [
            UserContextSource(),
            ScheduleContextSource(),
            DeadlineContextSource(),
            CreditsContextSource(),
            EmailContextSource(),
        ]

    def retrieve_all_context(self, db: Session, user_id: int) -> str:
        """检索所有注册的上下文源，并将结果合并为一个 JSON 字符串。"""
        context_data = {}
        for source in self._sources:
            try:
                data = source.retrieve_context(db, user_id)
                if data is not None:
                    context_data[source.source_key] = data
            except Exception as e:
                print(f"警告: 检索上下文源 '{source.source_key}' 失败: {e}")
        
        return json.dumps(context_data, ensure_ascii=False, default=_serialize_datetime)

# 全局 RAG MCP 管理器实例
mcp_manager = MCPManager()

# ====================================================================
#              2. Agent Model Context Protocol (MCP) 实现 (SQL Agent)
# ====================================================================

## 2.1 Agent MCP 抽象基类
class MCPAgentToolSource(ABC):
    """Agent 工具源的抽象基类。"""
    @abstractmethod
    def get_tools(self, db_instance: SQLDatabase) -> list[Tool]:
        """返回 Agent 可用的 LangChain Tool 列表"""
        pass

    @abstractmethod
    def get_schema_context(self) -> str:
        """返回 Agent 在系统指令中需要知道的 Schema 或上下文描述"""
        pass

## 2.2 Agent SQL 工具源的实现
class SQLToolSource(MCPAgentToolSource):
    """提供标准的 SQL 查询和 Schema 获取工具。"""
    def get_tools(self, db_instance: SQLDatabase) -> list[Tool]:
        # --- 关键：自定义 DML 执行工具函数 ---
        def run_sql_query(sql_query: str) -> str:
            """执行任意 SQL 查询，包括 SELECT, INSERT, UPDATE, DELETE。"""
            return db_instance.run(sql_query)

        # --- 关键：自定义获取 Schema 工具函数 ---
        def get_sql_schema(table_names: str) -> str:
            """返回指定表的 SQL Schema 定义。"""
            return db_instance.get_table_info(table_names=table_names.split(","))

        dml_tool = Tool(
            name="sql_db_query", 
            description="用于执行 SQL 查询。此工具可以执行 SELECT, INSERT, UPDATE 和 DELETE 语句。 输入是完整的、可执行的 SQL 语句。",
            func=run_sql_query
        )
        schema_tool = Tool(
            name="sql_db_schema",
            description="用于获取数据库中表的 Schema 信息 (CREATE TABLE 语句)。输入是逗号分隔的表名列表。",
            func=get_sql_schema
        )
        return [dml_tool, schema_tool]

    def get_schema_context(self) -> str:
        # 硬编码了 Agent 所需的 Schema 描述
        return """
    **数据库 Schema 上下文 (Database Schema Context):**
    你被授权操作以下所有表。严格使用这些表名和字段名。

    ### 1. `users` (学生用户表)
    * 用途: 存储学生基本信息、联系方式和学业概况。
    * 关键字段: 
        * `user_id` (Integer, 主键): **必须**用于所有涉及用户数据的 WHERE 子句。
        * `name` (String, 姓名)
        * `gpa` (Float, 平均绩点)
        * `department` (String, 院系)
        * `phone` (String, 电话), `email` (String, 邮箱)

    ### 2. `schedules` (日程安排表)
    * 用途: 存储课程、训练、活动等安排。
    * 关键字段: 
        * `schedule_id` (Integer, 主键)
        * `name` (String, 活动名)
        * `location` (String, 地点)
        * `start_time` (Time), `end_time` (Time)
        * `weekday` (Integer, 1-7表示周一到周日)
        * `description` (String)
        * `schedule_type` (String, 只有四种类型: course, custom, study, sport.)
    * 关系: 与 `users` 是多对多关系 (`user_schedule_association` 关联)。

    ### 3. `user_schedule_association` (用户-日程关联表)
    * 用途: 关联用户和日程。
    * 关键字段: `user_id` (Foreign Key), `schedule_id` (Foreign Key)。

    ### 4. `deadlines` (截止日期表)
    * 用途: 存储截止日期事件。
    * 关键字段: 
        * `id` (Integer, 主键)
        * `user_id` (Foreign Key): **必须**用于数据隔离。
        * `title` (String, 标题)
        * `end_time` (String, 截止时间)
        * `event_type` (String, 如作业, 考试)
        * `is_user_created` (Integer, 0否/1是)

    ### 5. `credits` (学分信息表)
    * 用途: 存储用户的总学分及类别学分信息。
    * 关键字段:
        * `user_id` (Integer, Foreign Key): **必须**用于数据隔离。
        * `total_credit` (Float, 总学分)
        * `category_credit` (JSON, 存储各类别学分的JSON数据)

    ### 6. `email_parsed` (解析后邮件信息表)
    * 用途: 存储查询展示用的邮件信息。
    * 关键字段: 
        * `id` (Integer, 主键): 用于全文检索。
        * `user_id` (Foreign Key): **必须**用于数据隔离。
        * `subject` (Text, 主题), `sender` (Text, 发件人)
        * `body_text` (Text, 正文纯文本), `summary` (Text, 摘要)
        * `received_time` (DateTime, 接收时间)

    ### 7. `email_raw` (原始邮件数据表)
    * 用途: 存储原始 MIME 数据。
    * 关键字段: `id` (Integer, 主键), `user_id` (Foreign Key), `mime_content` (LargeBinary, 原始邮件内容)。

    ### 8. `bb_files` (Blackboard课程文件信息表)
    * 用途: 存储用户在 Blackboard 上同步的课程文件信息。
    * 关键字段:
        * `id` (Integer, 主键)
        * `user_id` (Foreign Key): **必须**用于数据隔离。
        * `course` (String, 课程名称)
        * `file_name` (String, 文件名)
        * `file_url` (Text, 文件下载链接)
"""

## 2.3 Agent Email 工具源的实现 (新增)
class EmailToolSource(MCPAgentToolSource):
    """提供邮件发送功能的工具源。"""
    
    # 定义工具的输入参数结构
    class SendEmailInput(BaseModel):
        to: str = Field(description="收件人邮箱地址")
        subject: str = Field(description="邮件主题")
        body: str = Field(description="邮件正文内容")
    
    def get_tools(self, db_instance: SQLDatabase) -> list[Tool]:
        
        def _resolve_smtp(host: str, port: int, use_ssl: bool) -> Tuple[str, int, bool]:
            """简化的 SMTP 配置解析逻辑"""
            host = (host or "").strip()
            normalized = host.lower()
            
            # 常见邮箱服务商映射
            overrides = {
                "imap.qq.com": ("smtp.qq.com", 465, True),
                "imap.exmail.qq.com": ("smtp.exmail.qq.com", 465, True),
                "imap.gmail.com": ("smtp.gmail.com", 465, True),
                "imap.163.com": ("smtp.163.com", 465, True),
                "imap.126.com": ("smtp.126.com", 465, True),
                "imap-mail.outlook.com": ("smtp-mail.outlook.com", 587, True),
                "outlook.office365.com": ("smtp.office365.com", 587, False),
            }
            
            if normalized in overrides:
                return overrides[normalized]
                
            if normalized.startswith("imap."):
                return ("smtp." + host[5:], 465 if use_ssl else 587, use_ssl)
                
            return (host, port, use_ssl)

        # 这里的 user_id 应该由 process_agent_query 在调用 Agent 时隐式处理，
        # 但 StructuredTool 要求所有参数在 Schema 中。
        # 因此，我们在 Agent 的系统指令中明确要求 LLM 总是传入当前的 user_id。
        def send_email_func(user_id: int, to: str, subject: str, body: str) -> str:
            """发送邮件的具体实现"""
            # 创建临时 Session
            SessionLocal = sessionmaker(bind=db_instance._engine)
            session = SessionLocal()
            try:
                # 1. 获取账户
                account = email.get_email_account(session, user_id)
                if not account:
                    return "发送失败: 未找到您的邮箱账户信息，请先在系统中登录邮箱。"
                
                # 2. 解密密码
                try:
                    # 注意：这里假设 email_crypto.decrypt_stored_password 存在并有效
                    password = email_crypto.decrypt_stored_password(account.password)
                except Exception:
                    return "发送失败: 密码解析错误，请检查存储的密码是否正确加密。"
                
                # 3. 解析 SMTP 设置
                smtp_host, smtp_port, smtp_use_ssl = _resolve_smtp(account.host, account.port, account.use_ssl)
                
                # 4. 发送
                service = SMTPMailService(
                    host=smtp_host,
                    username=account.email,
                    password=password,
                    port=smtp_port,
                    use_ssl=smtp_use_ssl
                )
                
                service.send_email(
                    subject=subject,
                    sender=account.email,
                    to=[to],
                    body_text=body
                )
                return f"邮件已成功发送给 {to}。请告知用户已完成。"
            except Exception as e:
                return f"邮件发送失败，请检查邮箱账户设置或收件人地址。错误详情: {str(e)}"
            finally:
                session.close()

        # 定义工具的输入参数结构 (包含 user_id)
        class FullSendEmailInput(BaseModel):
            user_id: int = Field(description="当前操作用户的ID，必须从调用函数的上下文 (process_agent_query) 中获取并传入。")
            to: str = Field(description="收件人邮箱地址")
            subject: str = Field(description="邮件主题")
            body: str = Field(description="邮件正文内容")

        email_tool = StructuredTool.from_function(
            func=send_email_func,
            name="send_email",
            description="用于向指定收件人发送邮件。必须提供用户ID、收件人、主题和正文。请务必核实收件人地址。",
            args_schema=FullSendEmailInput
        )
        
        return [email_tool]

    def get_schema_context(self) -> str:
        return """
    **工具能力上下文 (Tool Capabilities):**
    除了数据库操作，你还可以使用 `send_email` 工具。
    * **何时使用:** 当用户明确要求“发邮件给...”或“通知...”时使用。
    * **参数要求:** 必须从用户请求中准确提取 `to` (收件人), `subject` (主题), `body` (正文)。
    * **安全要求:** 必须将当前用户的 `user_id` 嵌入到 `send_email` 工具的 `user_id` 参数中。
    """

## 2.4 Agent MCP 管理器
class AgentMCPManager:
    """管理所有 Agent 工具和上下文源。"""
    def __init__(self):
        # 注册 Agent 所需的工具源
        self._tool_sources: list[MCPAgentToolSource] = [
            SQLToolSource(),
            EmailToolSource(), # 注册邮件工具
        ]

    def get_all_tools(self, db_instance: SQLDatabase) -> list[Tool]:
        """收集所有注册源提供的工具"""
        all_tools = []
        for source in self._tool_sources:
            all_tools.extend(source.get_tools(db_instance))
        return all_tools

    def get_all_schema_context(self) -> str:
        """收集所有注册源提供的 Schema 上下文"""
        context_parts = []
        for source in self._tool_sources:
            context_parts.append(source.get_schema_context())
        return "\n".join(context_parts)

# 全局 Agent MCP 管理器实例
agent_mcp_manager = AgentMCPManager()

# ====================================================================
#              3. 基础服务函数 (ASR, TTS, LLM)
# ====================================================================
# ... (transcribe_audio, text_to_speech, get_completion 保持不变) ...

# ====================================================================
#              4. 核心业务函数 (RAG, Agent)
# ====================================================================

def process_user_query(llm:str, db: Session, user_id: int, query: str, conversation_id: str | None = None) -> str:
    """
    使用 RAG MCP Manager 检索上下文，并调用 LLM。
    """
    # 检索用户上下文
    context_str = mcp_manager.retrieve_all_context(db, user_id)
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    system_prompt = f"""
    你是一个名为 SUSTech Agent 的校园私人助手。
    当前时间是: {current_time}

    以下是当前用户的相关数据 (JSON格式):
    {context_str}

    请按照如下要求回答用户的问题：
    - 如果询问涉及用户相关数据的问题，请基于上述数据进行回答。
    - 如果用户数据中没有相关信息，请礼貌地告知用户你无法回答该问题，而不是编造信息。
    - 请确保回答简洁明了，避免冗长
    - 如果询问无关用户数据的相关内容，请直接回答。
    """
    # 读取并拼接短期记忆（仅限当前对话框）
    history_msgs: list[dict] = []
    if conversation_id:
        mem = _memory_get(conversation_id)
        history_msgs = list(mem)  # 已是 role/content 结构

    messages = (
        [{"role": "system", "content": system_prompt}] +
        history_msgs +
        [{"role": "user", "content": query}]
    )
    response = get_completion(messages, model=llm)

    # 将当前轮次写入短期记忆
    if conversation_id:
        mem = _memory_get(conversation_id)
        mem.append({"role": "user", "content": query})
        mem.append({"role": "assistant", "content": response})
    return response

def create_sql_agent_executor(llm_model: str, system_instruction: str):
    """
    初始化并返回 LangChain SQL Agent Executor。
    使用 AgentMCPManager 动态加载工具和 Schema 上下文。
    根据模型名缓存不同的 Agent 实例。
    """
    global _sql_agent_executors, _sql_db

    # 检查是否已经为该模型创建了 Agent
    if llm_model in _sql_agent_executors:
        return _sql_agent_executors[llm_model]
    
    try:
        # 1. 初始化 SQLDatabase (只初始化一次)
        if _sql_db is None:
            _sql_db = SQLDatabase.from_uri(
                DATABASE_URL, 
                include_tables=["users", "deadlines", "schedules", "user_schedule_association", "email_parsed", "email_raw"] 
            )
        
        # 2. 初始化 LLM
        llm = ChatOpenAI(
            model=llm_model, 
            temperature=0, 
            openai_api_key=api_key,
            openai_api_base=base_url
        )

        # 3. 使用 AgentMCPManager 获取所有工具
        final_tools = agent_mcp_manager.get_all_tools(_sql_db)
        
        # 4. 合并基础指令和动态 Schema 上下文
        full_system_prompt = system_instruction + agent_mcp_manager.get_all_schema_context()

        # 5. 创建 Agent
        agent = create_agent(
            model=llm,
            tools=final_tools,
            system_prompt=full_system_prompt
        )
        
        # 缓存该模型的 Agent 实例
        _sql_agent_executors[llm_model] = agent
        return agent

    except Exception as e:
        print(f"初始化 SQL Agent 时出错: {e}. 请检查 DATABASE_URL 和数据库连接。")
        return None

def process_agent_query(llm: str, query: str, user_id: int, conversation_id: str | None = None) -> str:
    """
    专门调用 LangChain SQL Agent 处理数据库查询、修改和邮件发送等操作。
    """
    # 基础 Agent 的系统指令（不包含 Schema/Tool 上下文，那部分由 AgentMCPManager 提供）
    BASE_AGENT_INSTRUCTION = f"""
    你是 SUSTech Agent 的 **专家级 AI 智能执行体**。
    你的任务是精确地将用户的中文自然语言请求，通过调用提供的工具来完成。

    ### 核心原则
    1.  **用户身份:** 当前操作的用户ID是 **{user_id}**。在所有涉及用户身份的工具调用（如 `sql_db_query` 或 `send_email`）中，**必须**将这个 `user_id` 嵌入到参数中。
    2.  **工具选择:** * **SQL (数据操作):** 仅在用户请求查询、增加、修改或删除日程/DDL等数据库记录时使用 `sql_db_query`。
        * **Email (通信):** 仅在用户请求发送邮件或通知他人时使用 `send_email`。
        * **推理步骤 (ReAct/Tool Calling):** 必须先思考 (Thought)，再行动 (Action)，然后观察 (Observation)，最后回答 (Answer)。

    ### SQL 操作安全规范 (严格遵守)
    1.  **SQL 构造要求:** 在所有涉及到用户身份的 SQL 语句中 (SELECT, INSERT, UPDATE, DELETE)，你必须直接将这个 `user_id` 的数值嵌入到 SQL 字符串中（例如: `... WHERE user_id = {user_id};`）。
    2.  **权限限制:** 严禁执行任何破坏数据库结构的命令 (如 DROP, TRUNCATE, ALTER)。
    3.  **WHERE 子句:** 在任何 UPDATE 或 DELETE 语句中，必须包含一个明确的 WHERE 子句来限制操作范围，并且**必须包含当前用户的 `user_id = {user_id}` 条件**。

    ### 邮件操作规范
    1.  **参数提取:** 仔细从用户请求中提取 `to`, `subject`, `body` 参数。
    2.  **用户ID传递:** 必须将当前 `user_id` 传递给 `send_email` 工具的 `user_id` 参数。

    ---
    **Schema 上下文和工具描述将紧接在下方提供。**
    """
    
    agent_executor = create_sql_agent_executor(llm_model=llm, system_instruction=BASE_AGENT_INSTRUCTION)

    if agent_executor is None:
        return "代理服务初始化失败，无法执行操作。"
    
    try:
        # 注入短期记忆到 Agent 的 messages 输入（不包含系统指令，LangChain 会处理）
        history_msgs: list[dict] = []
        if conversation_id:
            mem = _memory_get(conversation_id)
            history_msgs = list(mem)

        inputs = {"messages": history_msgs + [{"role": "user", "content": query}]}
        response = agent_executor.invoke(inputs)
        
        # Agent 的响应通常包含最终消息
        final = response.get("messages", "Agent 未返回有效响应。")

        # 写入短期记忆（尽量归一化为一条 assistant 文本）
        if conversation_id:
            mem = _memory_get(conversation_id)
            mem.append({"role": "user", "content": query})
            # 如果返回的是字符串，直接写入；如果是列表/对象，尽量提取最终 assistant 内容
            assistant_text = ""
            try:
                if isinstance(final, str):
                    assistant_text = final
                elif isinstance(final, list):
                    # 寻找最后一个 assistant role
                    for m in reversed(final):
                        if isinstance(m, dict) and m.get("role") == "assistant":
                            assistant_text = str(m.get("content", ""))
                            break
                    assistant_text = assistant_text or str(final[-1])
                elif isinstance(final, dict):
                    assistant_text = str(final.get("content") or final)
                else:
                    assistant_text = str(final)
            except Exception:
                assistant_text = str(final)
            mem.append({"role": "assistant", "content": assistant_text})

        return final

    except Exception as e:
        print(f"Agent 执行失败: {e}")
        return f"Agent 在尝试处理您的请求时出错。请尝试更清晰或具体的查询。错误详情: {e}"

# 重新定义 ASR, TTS, LLM 函数以确保完整性，尽管主体不变

def transcribe_audio(file_obj: UploadFile) -> str:
    """使用 OpenAI Whisper 模型将语音文件转换为文本。"""
    try:
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=(file_obj.filename, file_obj.file, file_obj.content_type)
        )
        return transcription.text
    except Exception as e:
        print(f"语音转录失败: {e}")
        raise e
    
def text_to_speech(text: str) -> bytes:
    """使用 OpenAI TTS 模型将文本转换为 MP3 音频二进制数据。"""
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        return response.content
    except Exception as e:
        print(f"文本转语音失败: {e}")
        return b""

def get_completion(messages: list, model: str) -> str:
    """调用基础 LLM API 获取回复。"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"调用 LLM API 时出错: {e}")
        return "抱歉，LLM 服务调用失败，请检查 API 密钥和网络连接。"

def select_important_emails(user_id: int, db: Session) -> list:
    """
    从用户的最近邮件中筛选出3条重要邮件并保存。
    """
    # 1. 获取最近的邮件 (例如最近50封)
    emails, _ = email.list_emails(db, user_id, limit=50)
    
    if not emails:
        return []

    # 2. 构造 Prompt
    email_data = []
    for e in emails:
        email_data.append({
            "id": e.id,
            "subject": e.subject,
            "sender": e.sender,
            "body_text": e.body_text[:200] if e.body_text else "", # 截断以节省token
            "received_time": str(e.received_time)
        })
    
    prompt = f"""
    请从以下邮件列表中筛选出最重要的3封邮件。
    重要性判断标准：
    1. 来自学校教务处、老师或重要通知。
    2. 包含截止日期（DDL）、考试安排、成绩发布等关键信息。
    3. 近期收到的邮件优先。

    邮件列表数据 (JSON):
    {json.dumps(email_data, ensure_ascii=False)}

    请返回一个 JSON 数组，包含3个对象，每个对象有以下字段：
    - "id": 邮件的ID (对应输入中的id)
    - "reason": 筛选理由 (简短说明为什么重要)

    仅返回 JSON 数组，不要包含其他文字。
    """

    messages = [
        {"role": "system", "content": "你是一个智能邮件助手，负责筛选重要邮件。"},
        {"role": "user", "content": prompt}
    ]

    # 3. 调用 LLM
    # 使用 gpt-4o 或其他高性能模型以获得更好的推理能力
    response_text = get_completion(messages, model="gpt-4o") 

    # 4. 解析结果并保存
    try:
        # 清理可能的 markdown 标记
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        selected_emails = json.loads(response_text)
        
        # 先清空旧的重要邮件 (根据需求，这里假设每次重新生成)
        important_email.clear_important_emails(db, user_id)
        
        results = []
        for item in selected_emails:
            email_id = item.get("id")
            reason = item.get("reason")
            if email_id:
                # 验证 email_id 是否存在于原始列表中 (安全起见)
                if any(e.id == email_id for e in emails):
                    new_record = important_email.create_important_email(db, user_id, email_id, reason)
                    results.append(new_record)
        
        return results

    except Exception as e:
        print(f"筛选邮件失败: {e}")
        return []


def blackboard_email_summaries(db: Session, user_id: int, max_emails: int = 50, llm: str = "gpt-4o") -> list[str]:
    """使用 AI 判断哪些邮件来自 Blackboard，并返回这些邮件的总结内容列表。

    不使用 SQL 层面的筛选逻辑，统一先取最近若干封邮件，然后交由 LLM 判断和汇总。
    返回值为中文总结字符串列表。
    """
    # 1) 取最近 max_emails 封用于判别的数据（不在 SQL 中做 Blackboard 过滤）
    emails, _ = email.list_emails(db, user_id, limit=max_emails)

    if not emails:
        return []

    # 2) 构造简要输入，尽量控制 token；优先使用已有 summary，缺失时提供正文片段
    email_brief = [
        {
            "id": em.id,
            "subject": em.subject or "",
            "sender": em.sender or "",
            "summary": (em.summary or "")[:400],
            "body_text": ((em.body_text or "").strip())[:800],
            "received_time": em.received_time.strftime('%Y-%m-%d %H:%M') if em.received_time else "",
        }
        for em in emails
    ]

    system_prompt = (
        "你是一个严格的邮件分类与总结助手。目标：在提供的邮件数组中，仅筛选出由 Blackboard 发送的通知类邮件并输出英文总结。\n"
        "判定规则（满足任一即可视为 Blackboard 邮件）：\n"
        "1) sender 精确等于 blackboard@sustech.edu.cn；或包含 'blackboard' 且域名含 sustech.edu.cn。\n"
        "2) subject 或正文出现关键短语：'Blackboard', 'Course Announcement', 'Assignment', 'Test', 'Exam', 'Grade', 'Submission', 'Deadline'.\n"
        "排除：纯欢迎语、重复提醒（内容高度相似）、无实质信息的空通知。\n\n"
        "输入：JSON 数组，每个元素含字段 id, subject, sender, summary(可能为空), body_text(截断), received_time。\n"
        "任务：\n"
        "1. 只对判定为 Blackboard 的邮件生成英文总结；其他邮件忽略。\n"
        "2. 每封邮件输出 1 条英文总结（不超过 40 词），包含：\n"
        "   - 课程/来源 (若可解析出课程代码或名称，用方括号如 [CS101])；\n"
        "   - 关键信息（公告类型、作业/考试/成绩/资源更新等）；\n"
        "   - 动作与截止时间（若存在，统一规范为 YYYY-MM-DD HH:MM；只有日期则用 YYYY-MM-DD）。\n"
        "3. 不要翻译日期文本，如果正文含 '11:59pm' 统一规范为 23:59。\n"
        "4. 若正文与 summary 同时存在，优先基于 summary，必要时补充正文缺失的截止时间或动作。\n"
        "5. 如果没有 Blackboard 邮件，返回空数组 []。\n\n"
        "输出格式：严格仅返回一个 JSON 数组，数组元素为英文字符串，每个元素对应一封 Blackboard 邮件的总结。\n"
        "禁止：输出对象、额外说明、前后缀文字、Markdown 代码块、中文内容。\n"
        "示例输出：\n"
        '["[CS101] Assignment 2 released. Action: submit via Blackboard. Deadline: 2025-12-08 23:59",'
        ' "[MATH203] Quiz 3 grade published. Review feedback promptly"]\n'
        "现在开始。"
    )

    user_prompt = (
        "以下是最近的邮件列表（JSON）：\n" + json.dumps(email_brief, ensure_ascii=False)
    )

    raw = get_completion([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ], model=llm)

    cleaned = (raw or "").strip()
    try:
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
        elif cleaned.startswith("```") and cleaned.endswith("```"):
            cleaned = cleaned.strip("`")
    except Exception:
        pass

    # 3) 尝试解析 LLM 输出
    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            # 仅保留字符串，并去空
            results = [str(x).strip() for x in data if isinstance(x, (str, int, float))]
            return [r for r in results if r]
    except Exception:
        pass

    # 4) 兜底：若 LLM 输出解析失败，使用简单启发式仅用于保底
    fallback = []
    for em in emails:
        text = f"{(em.subject or '').lower()} {(em.sender or '').lower()} {(em.body_text or '').lower()}"
        if "blackboard" in text:
            if em.summary:
                fallback.append(em.summary)
            else:
                fallback.append((em.subject or "Blackboard 通知")[:80])
    return fallback


def recommend_activities(llm: str, db: Session, user_id: int, count: int = 3) -> list[schemas.ActivityRecommendation]:
    """
    根据用户最近邮件内容与兴趣生成活动推荐。
    输出 2-3 条，包含: name, time, location, type (course|sport|study|custom)。
    """
    # 限制返回数量在 2-3 范围
    target_n = max(2, min(3, int(count or 3)))

    # 获取上下文（包括用户兴趣、课程/日程、DDL、邮件等）
    context_str = mcp_manager.retrieve_all_context(db, user_id)

    # 获取最近若干封邮件，构造简要列表以减少token
    emails_list, _ = email.list_emails(db, user_id, limit=30)
    email_brief = [
        {
            "id": em.id,
            "subject": em.subject,
            "sender": em.sender,
            "received_time": em.received_time.strftime('%Y-%m-%d %H:%M'),
            "body_text": (em.body_text or "")[:500],
            "summary": em.summary or ""
        }
        for em in emails_list
    ]

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    system_prompt = f"""
你是 SUSTech Agent 的活动推荐助手，当前时间: {current_time}。

以下是当前用户相关数据(JSON)：
{context_str}

你需要根据用户的邮件内容和兴趣，推荐接下来值得参加的活动，严格遵守：
- 仅返回 JSON 数组，无任何额外文字或注释。
- 每个对象必须包含字段："name"(字符串), "time"(字符串或可为空), "location"(可为空), "type"(必须是以下之一: course, sport, study, custom)。
- 推荐 2-3 个活动，优先选择与用户兴趣匹配或邮件中明确的通知/安排。
- "time" 字段尽量提供具体日期时间或范围，如 "2025-12-01 19:00" 或 "每周三 14:00-16:00"；若无法确定可留空字符串。
- 依据邮件来源，避免重复或过期活动。
- 必须避免与用户现有日程冲突；如存在冲突请更换时间或不予推荐。
- 推荐事件必须在当前时间之后发生，不可以是已发生事件。
"""

    user_prompt = (
        "请阅读这些邮件的简要信息(JSON)并给出推荐活动：\n" +
        json.dumps(email_brief, ensure_ascii=False)
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    raw = get_completion(messages, model=llm)

    # 清理代码块包裹
    cleaned = raw.strip()
    try:
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
        elif cleaned.startswith("```") and cleaned.endswith("```"):
            cleaned = cleaned.strip("`")
    except Exception:
        pass

    # 解析 JSON
    try:
        items = json.loads(cleaned)
        if not isinstance(items, list):
            items = []
    except Exception:
        items = []

    # 规范化 type 字段
    def normalize_type(t: str) -> str:
        t_norm = (t or "").strip().lower()
        if t_norm in {"course", "sport", "study", "custom"}:
            return t_norm
        # 常见同义词映射
        synonyms = {
            "class": "course", "lecture": "course", "课程": "course",
            "运动": "sport", "体育": "sport", "sports": "sport",
            "学习": "study", "自习": "study", "workshop": "study",
        }
        return synonyms.get(t_norm, "custom")

    # ---------- 与现有日程冲突检测工具函数 ----------
    # 将现有课表转换为按 weekday -> [(start_min, end_min)] 的索引
    user_schedules = schedule.get_schedule_by_sid(db, user_id) or []

    def time_to_minutes(t: dtime) -> int:
        return t.hour * 60 + t.minute

    schedule_index: dict[int, list[tuple[int, int]]] = {}
    for sch in user_schedules:
        try:
            wd = int(getattr(sch, "weekday", 0) or 0)
            st = getattr(sch, "start_time", None)
            et = getattr(sch, "end_time", None)
            if wd and st and et:
                schedule_index.setdefault(wd, []).append((time_to_minutes(st), time_to_minutes(et)))
        except Exception:
            continue

    # 解析“周几 + 时间段”的字符串，例如："每周三 14:00-16:00"、"周一 09:00-11:00"、"Wed 14:00-16:00"
    CN_WEEK_MAP = {"一":1, "二":2, "三":3, "四":4, "五":5, "六":6, "日":7, "天":7}
    EN_WEEK_MAP = {
        "mon":1, "monday":1,
        "tue":2, "tues":2, "tuesday":2,
        "wed":3, "wednesday":3,
        "thu":4, "thur":4, "thurs":4, "thursday":4,
        "fri":5, "friday":5,
        "sat":6, "saturday":6,
        "sun":7, "sunday":7,
    }

    def parse_weekday_token(token: str) -> int | None:
        token = (token or "").strip().lower()
        if not token:
            return None
        # 中文：周一/星期一
        m = re.search(r"[周星期]{1,2}([一二三四五六日天])", token)
        if m:
            return CN_WEEK_MAP.get(m.group(1))
        # 英文：Mon/Wed/Friday
        tok = re.sub(r"[^a-z]", "", token)
        if tok in EN_WEEK_MAP:
            return EN_WEEK_MAP[tok]
        return None

    def parse_hhmm(s: str) -> int | None:
        m = re.search(r"(\d{1,2}):(\d{2})", s)
        if not m:
            return None
        h, mm = int(m.group(1)), int(m.group(2))
        if 0 <= h < 24 and 0 <= mm < 60:
            return h * 60 + mm
        return None

    def extract_weekly_range(text: str) -> tuple[int, int, int] | None:
        """返回 (weekday, start_min, end_min) 或 None"""
        if not text:
            return None
        # 尝试匹配：(<每周/周/星期/英文星期>) + 时间段
        # 示例：每周三 14:00-16:00 / 周四 09:00-10:30 / Wed 14:00-16:00
        # 先找星期
        wd = parse_weekday_token(text)
        if not wd:
            return None
        # 找时间范围
        time_match = re.search(r"(\d{1,2}:\d{2})\s*[-~到toTO]{1,3}\s*(\d{1,2}:\d{2})", text)
        if not time_match:
            return None
        st = parse_hhmm(time_match.group(1))
        et = parse_hhmm(time_match.group(2))
        if st is None or et is None or st >= et:
            return None
        return (wd, st, et)

    def extract_date_range(text: str) -> tuple[int, int, int] | None:
        """解析形如 'YYYY-MM-DD HH:MM' 或 'YYYY-MM-DD HH:MM- HH:MM'，返回 (weekday, start_min, end_min) 或 None"""
        if not text:
            return None
        m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})(?:\s+(\d{1,2}:\d{2})(?:\s*[-~到toTO]{1,3}\s*(\d{1,2}:\d{2}))?)?", text)
        if not m:
            return None
        try:
            y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            dt = date(y, mo, d)
            wd = (dt.isoweekday())  # 1-7
            if m.group(4):
                st = parse_hhmm(m.group(4)) or 0
                et = parse_hhmm(m.group(5) or "") or (st + 60)  # 若无结束时间，默认+60分钟
                if st < et:
                    return (wd, st, et)
        except Exception:
            return None
        return None

    def has_conflict(time_str: str) -> bool:
        """与现有日程是否冲突；无法解析时间则视为未知，不判冲突。"""
        if not time_str:
            return False  # 无时间信息，无法判定冲突，视为不冲突
        parsed = extract_weekly_range(time_str) or extract_date_range(time_str)
        if not parsed:
            return False
        wd, st, et = parsed
        slots = schedule_index.get(wd, [])
        for s_st, s_et in slots:
            # 区间重叠判断
            if st < s_et and s_st < et:
                return True
        return False

    normalized = []
    for it in items:
        try:
            rec = schemas.ActivityRecommendation(
                name=str(it.get("name", "")).strip(),
                time=(it.get("time") or "").strip() or None,
                location=(it.get("location") or "").strip() or None,
                type=normalize_type(it.get("type", "custom"))  # type: ignore
            )
            # 跳过空名称
            if rec.name:
                normalized.append(rec)
        except Exception:
            continue

    # 过滤与现有日程冲突的推荐；优先保留可解析且不冲突的，其次保留时间未知的
    non_conflicting: list[schemas.ActivityRecommendation] = []
    unknown_time: list[schemas.ActivityRecommendation] = []

    for rec in normalized:
        if rec.time:
            if not has_conflict(rec.time):
                non_conflicting.append(rec)
        else:
            unknown_time.append(rec)

    # 合并，先放不冲突的，再补未知时间的
    merged: list[schemas.ActivityRecommendation] = non_conflicting + unknown_time

    # 若数量仍不足 2，则用邮件主题占位补齐（time 为空，自然不冲突）
    if len(merged) < 2:
        for em in emails_list:
            if len(merged) >= 2:
                break
            try:
                merged.append(
                    schemas.ActivityRecommendation(
                        name=(em.subject or "活动"),
                        time=None,
                        location=None,
                        type="custom"  # type: ignore
                    )
                )
            except Exception:
                continue

    # 最终裁剪到 2-3 条
    normalized = merged[:target_n]

    return normalized

    # 2. 构造 Prompt
    email_data = []
    for e in emails:
        email_data.append({
            "id": e.id,
            "subject": e.subject,
            "sender": e.sender,
            "body_text": e.body_text[:200] if e.body_text else "", # 截断以节省token
            "received_time": str(e.received_time)
        })
    
    prompt = f"""
    请从以下邮件列表中筛选出最重要的3封邮件。
    重要性判断标准：
    1. 来自学校教务处、老师或重要通知。
    2. 包含截止日期（DDL）、考试安排、成绩发布等关键信息。
    3. 近期收到的邮件优先。

    邮件列表数据 (JSON):
    {json.dumps(email_data, ensure_ascii=False)}

    请返回一个 JSON 数组，包含3个对象，每个对象有以下字段：
    - "id": 邮件的ID (对应输入中的id)
    - "reason": 筛选理由 (简短说明为什么重要)

    仅返回 JSON 数组，不要包含其他文字。
    """

    messages = [
        {"role": "system", "content": "你是一个智能邮件助手，负责筛选重要邮件。"},
        {"role": "user", "content": prompt}
    ]

    # 3. 调用 LLM
    # 使用 gpt-4o 或其他高性能模型以获得更好的推理能力
    response_text = get_completion(messages, model="gpt-4o") 

    # 4. 解析结果并保存
    try:
        # 清理可能的 markdown 标记
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        selected_emails = json.loads(response_text)
        
        # 先清空旧的重要邮件 (根据需求，这里假设每次重新生成)
        important_email.clear_important_emails(db, user_id)
        
        results = []
        for item in selected_emails:
            email_id = item.get("id")
            reason = item.get("reason")
            if email_id:
                # 验证 email_id 是否存在于原始列表中 (安全起见)
                if any(e.id == email_id for e in emails):
                    new_record = important_email.create_important_email(db, user_id, email_id, reason)
                    results.append(new_record)
        
        return results

    except Exception as e:
        print(f"筛选邮件失败: {e}")
        return []