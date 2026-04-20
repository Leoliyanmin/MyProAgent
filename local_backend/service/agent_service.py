from business.agent_logic import AgentLogic
from database.code.database_chat_handle import ChatHandle
import asyncio
import json
import re
import re
from typing import Any, Awaitable, Callable, Optional
import websockets
from pathlib import Path
from datetime import datetime
import sys

localagent_path = Path(__file__).parent.parent.parent / "localagent"
if str(localagent_path) not in sys.path:
    sys.path.insert(0, str(localagent_path))

from localagent.agent import LocalAgent
from localagent.session import SessionManager
from localagent.memory import MemoryStore


class AgentService:
    CALENDAR_MUTATION_TOOLS = {
        "create_schedule_event",
        "update_schedule_event",
        "update_schedule_event_time",
        "delete_schedule_event",
    }

    _CALENDAR_OBJECT_KEYWORDS = (
        "日程", "行程", "事件", "会议", "提醒", "calendar", "schedule", "event",
    )
    _CALENDAR_MUTATION_KEYWORDS = (
        "新建", "创建", "添加", "安排", "修改", "更新", "调整", "改成", "改到", "变更",
        "删除", "取消", "移除", "推迟", "提前", "rename", "reschedule", "update", "create", "delete", "cancel",
    )

    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init(*args, **kwargs)
        return cls._instance
    
    def _init(self, nanobot_ws_url: str = "ws://127.0.0.1:8765/"):
        self.agent_logic = AgentLogic()
        self.chat_handle = ChatHandle()
        self.nanobot_ws_url = nanobot_ws_url

        self.workspace = Path(__file__).parent.parent.parent
        self.session_manager = SessionManager(self.workspace)
        self.memory_store = MemoryStore(self.workspace)
        
        print("[AgentService] Initializing LocalAgent...")
        import time
        start = time.time()
        self.agent = LocalAgent(workspace=self.workspace)
        print(f"[AgentService] LocalAgent initialized in {time.time() - start:.2f}s")

    def process_query(self, user_id: str, message: str, session_id: str = None):
        # 如果没有 session_id，创建一个新会话
        if not session_id:
            session_result = self.chat_handle.create_session(user_id)
            if not session_result['ok']:
                return {'response': '创建会话失败', 'thought_trace': [], 'tool_calls': []}
            session_id = session_result['data']['session_id']
        
        # 创建用户消息
        user_msg_result = self.chat_handle.create_chat_message(session_id, 'user', message)
        if not user_msg_result['ok']:
            print(f"Failed to create user message: {user_msg_result['message']}")
        
        # 处理查询
        result = self.agent_logic.process_query(user_id, message, str(session_id))
        
        # 创建助手消息
        assistant_msg_result = self.chat_handle.create_chat_message(
            session_id,
            'assistant',
            result['response'],
            thought_trace=str(result.get('thought_trace', [])),
            tool_calls=str(result.get('tool_calls', [])),
        )
        if not assistant_msg_result['ok']:
            print(f"Failed to create assistant message: {assistant_msg_result['message']}")
        
        return result

    def get_chat_history(self, user_id: str, session_id: str):
        try:
            session_id_int = int(session_id)
        except ValueError:
            return {'success': False, 'message': 'Invalid session ID'}
        
        result = self.chat_handle.get_chat_history(session_id_int)
        if not result['ok']:
            return {'success': False, 'message': result['message']}
        
        return {
            'success': True,
            'history': result['data']
        }

    async def chat_with_nanobot(self, message: str, client_id: str = "local_backend") -> dict:
        SYSTEM_PROMPT = "你现在是 sustech_productivity 助手，一个专为南科大学生打造的 productivity 助手。你的所有回答都必须以 sustech_productivity 助手的身份进行回复。"

        try:
            async with websockets.connect(f"{self.nanobot_ws_url}?client_id={client_id}") as ws:
                ready = await ws.recv()
                if isinstance(ready, bytes):
                    ready = ready.decode("utf-8")
                full_message = f"{SYSTEM_PROMPT}\n\n用户问题：{message}"
                await ws.send(json.dumps({"content": full_message}, ensure_ascii=False))
                response_text = ""
                while True:
                    raw = await ws.recv()
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8")
                    msg = json.loads(raw)
                    event = msg.get("event")
                    if event == "message":
                        response_text = msg.get("text", "")
                        break
                    elif event == "delta":
                        response_text += msg.get("text", "")
                    elif event == "stream_end":
                        break
                return {
                    'success': True,
                    'response': response_text,
                    'client_id': client_id
                }
        except Exception as e:
            return {
                'success': False,
                'response': f'连接nanobot失败: {str(e)}',
                'error': str(e)
            }

    def chat_with_nanobot_sync(self, message: str, client_id: str = "local_backend") -> dict:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.chat_with_nanobot(message, client_id))
            loop.close()
            return result
        except Exception as e:
            return {
                'success': False,
                'response': f'连接nanobot失败: {str(e)}',
                'error': str(e)
            }

    # ==================== LocalAgent 集成方法 ====================

    def _resolve_working_directory(self, raw_path: str) -> Path:
        """Resolve and validate a working directory provided by client."""
        candidate = Path(raw_path).expanduser()
        if not candidate.is_absolute():
            candidate = (self.workspace / candidate).resolve()
        else:
            candidate = candidate.resolve()

        if not candidate.exists():
            raise ValueError(f"工作目录不存在: {candidate}")
        if not candidate.is_dir():
            raise ValueError(f"工作目录不是文件夹: {candidate}")
        return candidate

    @staticmethod
    def _build_file_manager_message(user_message: str, working_directory: Path) -> str:
        return (
            "你正在执行文件管理任务。\n"
            f"当前工作目录: {working_directory}\n"
            "规则:\n"
            "1) 除非用户明确指定其他绝对路径，否则所有相对路径都基于当前工作目录。\n"
            "2) 处理文件时优先使用工具：list_dir/read_file/write_file/edit_file/delete_file/move_file/copy_file/create_dir。\n"
            "3) 对于删除或覆盖操作，先说明将执行的目标路径，再执行。\n\n"
            f"用户请求:\n{user_message}"
        )

    @staticmethod
    def _build_calendar_guard_message(user_message: str) -> str:
        return (
            "你正在处理日程操作请求。\n"
            "重要规则：必须调用日程工具（create_schedule_event / update_schedule_event / "
            "update_schedule_event_time / delete_schedule_event）来完成操作。\n"
            "禁止仅用文字回复'创建成功/更新成功/删除成功'而不调用工具。\n"
            "如果信息不足，明确向用户追问缺失字段（标题、开始时间、结束时间等）。\n\n"
            f"用户请求:\n{user_message}"
        )

    async def process_with_local_agent(
        self,
        user_id: str,
        message: str,
        session_id: str = "default",
        working_directory: Optional[str] = None,
        on_stream: Callable[[str], Awaitable[None]] | None = None,
    ):
        session = self.session_manager.get_or_create(session_id)

        effective_working_dir: Optional[Path] = None
        if working_directory and working_directory.strip():
            effective_working_dir = self._resolve_working_directory(working_directory.strip())
            session.metadata["working_directory"] = str(effective_working_dir)
        elif session.metadata.get("working_directory"):
            effective_working_dir = self._resolve_working_directory(session.metadata["working_directory"])

        agent_message = message
        if self._needs_calendar_mutation_tool(message):
            agent_message = self._build_calendar_guard_message(message)
        elif effective_working_dir is not None:
            agent_message = self._build_file_manager_message(message, effective_working_dir)

        self.agent.set_runtime_context(user_id=user_id)

        result = await self.agent.run(agent_message, on_stream=on_stream)

        session.add_message("user", message)
        if result.content:
            session.add_message("assistant", result.content)
        await asyncio.gather(
            asyncio.to_thread(self.session_manager.save, session),
            asyncio.to_thread(self.memory_store.add_entry, message),
        )

        pending_deletions = self._extract_pending_deletions(result.content)

        return {
            'response': result.content,
            'thought_trace': [],
            'tool_calls': result.tools_used,
            'iterations': result.iterations,
            'requires_confirmation': len(pending_deletions) > 0,
            'pending_deletions': pending_deletions,
        }

    _DELETE_CONFIRMATION_PREFIX = "[DELETE_CONFIRMATION]"

    @classmethod
    def _extract_pending_deletions(cls, result_content: str) -> list[dict]:
        deletions = []
        for line in result_content.split("\n"):
            line = line.strip()
            if line.startswith(cls._DELETE_CONFIRMATION_PREFIX):
                json_str = line[len(cls._DELETE_CONFIRMATION_PREFIX):]
                try:
                    detail = json.loads(json_str)
                    deletions.append(detail)
                except (json.JSONDecodeError, ValueError):
                    pass
        return deletions

    @classmethod
    def _has_calendar_mutation_tool(cls, tools_used: list[str] | None) -> bool:
        if not tools_used:
            return False
        return any(tool in cls.CALENDAR_MUTATION_TOOLS for tool in tools_used)

    @classmethod
    def _needs_calendar_mutation_tool(cls, message: str) -> bool:
        text = str(message or "").strip().lower()
        if not text:
            return False

        has_object = any(keyword in text for keyword in cls._CALENDAR_OBJECT_KEYWORDS)
        if not has_object:
            return False

        has_mutation = any(keyword in text for keyword in cls._CALENDAR_MUTATION_KEYWORDS)
        if has_mutation:
            return True

        # 兜底：检测常见“改时间”语义
        return bool(re.search(r"(改|调).*(时间|日期)", text))

    def list_working_directory(self, working_directory: str, relative_path: str = ""):
        """List contents under a validated working directory for Finder-style browsing."""
        root = self._resolve_working_directory(working_directory)

        sub_path = Path(relative_path.strip() or ".")
        target = (root / sub_path).resolve()

        try:
            target.relative_to(root)
        except ValueError as exc:
            raise ValueError("子路径超出工作目录范围") from exc

        if not target.exists():
            raise ValueError(f"目录不存在: {target}")
        if not target.is_dir():
            raise ValueError(f"目标不是目录: {target}")

        entries = []
        for item in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            stat = item.stat()
            entries.append({
                "name": item.name,
                "relative_path": str(item.relative_to(root)),
                "is_directory": item.is_dir(),
                "size": None if item.is_dir() else stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })

        relative = "" if target == root else str(target.relative_to(root))
        parent_relative = None
        if target != root:
            parent_relative = "" if target.parent == root else str(target.parent.relative_to(root))

        return {
            "working_directory": str(root),
            "current_directory": str(target),
            "relative_path": relative,
            "parent_relative_path": parent_relative,
            "entries": entries,
        }

    @staticmethod
    def _validate_filename(filename: str) -> str:
        name = filename.strip()
        if not name:
            raise ValueError("文件名不能为空")
        if "/" in name or "\\" in name:
            raise ValueError("仅支持文件名，不支持路径")
        if name in {".", ".."}:
            raise ValueError("非法文件名")
        return name

    def _resolve_target_directory(self, working_directory: str, relative_path: str = "") -> tuple[Path, Path, str]:
        root = self._resolve_working_directory(working_directory)
        sub_path = Path((relative_path or "").strip() or ".")
        target = (root / sub_path).resolve()

        try:
            target.relative_to(root)
        except ValueError as exc:
            raise ValueError("子路径超出工作目录范围") from exc

        if not target.exists():
            raise ValueError(f"目录不存在: {target}")
        if not target.is_dir():
            raise ValueError(f"目标不是目录: {target}")

        relative = "" if target == root else str(target.relative_to(root))
        return root, target, relative

    def create_file_name(self, working_directory: str, filename: str, relative_path: str = ""):
        root, target_dir, relative = self._resolve_target_directory(working_directory, relative_path)
        name = self._validate_filename(filename)
        file_path = target_dir / name

        if file_path.exists():
            raise ValueError(f"文件已存在: {name}")

        file_path.touch()
        return {
            "success": True,
            "message": f"创建成功: {name}",
            "working_directory": str(root),
            "relative_path": relative,
            "filename": name,
        }

    def update_file_name(self, working_directory: str, filename: str, content: str, relative_path: str = ""):
        root, target_dir, relative = self._resolve_target_directory(working_directory, relative_path)
        name = self._validate_filename(filename)
        file_path = target_dir / name

        if not file_path.exists():
            raise ValueError(f"文件不存在: {name}")
        if not file_path.is_file():
            raise ValueError(f"不是文件: {name}")

        file_path.write_text(content, encoding="utf-8")

        return {
            "success": True,
            "message": f"更新成功: {name}",
            "working_directory": str(root),
            "relative_path": relative,
            "filename": name,
        }

    def rename_file_name(self, working_directory: str, old_filename: str, new_filename: str, relative_path: str = ""):
        root, target_dir, relative = self._resolve_target_directory(working_directory, relative_path)
        old_name = self._validate_filename(old_filename)
        new_name = self._validate_filename(new_filename)

        old_path = target_dir / old_name
        new_path = target_dir / new_name

        if not old_path.exists() or not old_path.is_file():
            raise ValueError(f"文件不存在: {old_name}")
        if new_path.exists():
            raise ValueError(f"目标文件名已存在: {new_name}")

        old_path.rename(new_path)
        return {
            "success": True,
            "message": f"重命名成功: {old_name} -> {new_name}",
            "working_directory": str(root),
            "relative_path": relative,
            "filename": old_name,
            "new_filename": new_name,
        }

    def read_file_name(self, working_directory: str, filename: str, relative_path: str = ""):
        root, target_dir, relative = self._resolve_target_directory(working_directory, relative_path)
        name = self._validate_filename(filename)
        file_path = target_dir / name

        if not file_path.exists():
            raise ValueError(f"文件不存在: {name}")
        if not file_path.is_file():
            raise ValueError(f"不是文件: {name}")

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            raise ValueError(f"读取文件失败: {exc}") from exc

        return {
            "working_directory": str(root),
            "relative_path": relative,
            "filename": name,
            "content": content,
        }

    def delete_file_name(self, working_directory: str, filename: str, relative_path: str = ""):
        root, target_dir, relative = self._resolve_target_directory(working_directory, relative_path)
        name = self._validate_filename(filename)
        file_path = target_dir / name

        if not file_path.exists() or not file_path.is_file():
            raise ValueError(f"文件不存在: {name}")

        file_path.unlink()
        return {
            "success": True,
            "message": f"删除成功: {name}",
            "working_directory": str(root),
            "relative_path": relative,
            "filename": name,
        }

    def get_local_agent_session(self, session_id: str = "default"):
        """获取 LocalAgent 会话消息"""
        session = self.session_manager.get_or_create(session_id)
        history = session.get_history()
        return {
            'success': True,
            'session_id': session_id,
            'messages': [
                {'role': msg['role'], 'content': msg.get('content', '')}
                for msg in history
            ]
        }

    def clear_local_agent_session(self, session_id: str = "default"):
        """清除 LocalAgent 会话"""
        session = self.session_manager.get_or_create(session_id)
        session.clear()
        self.session_manager.save(session)
        return {'success': True, 'message': f'Session {session_id} cleared'}

    def get_memory_content(self):
        """获取当前记忆内容"""
        return {
            'success': True,
            'content': self.memory_store.get_memory()
        }

    async def consolidate_memory(self):
        """运行记忆整合"""
        from localagent.memory import Dream
        dream = Dream(
            store=self.memory_store,
            provider=self.agent.provider,
            tool_registry=self.agent.tools,
        )
        result = await dream.run()
        return {
            'success': result.success,
            'entries_processed': result.entries_processed,
            'summary': result.summary
        }