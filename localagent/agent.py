"""Core agent implementation with streaming and parallel tool execution."""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

from .provider import OpenAICompatProvider, LLMResponse
from .tools.base import BaseTool, ToolRegistry
from .tools import (
    ReadFileTool,
    WriteFileTool,
    EditFileTool,
    ListDirTool,
    CreateDirTool,
    SearchFilesTool,
    GrepTool,
    MoveFileTool,
    DeleteFileTool,
    CopyFileTool,
    ExecTool,
    CreateScheduleEventTool,
    UpdateScheduleEventTool,
    UpdateScheduleEventTimeTool,
    DeleteScheduleEventTool,
)
from .tools.email_tools import (
    CheckEmailStatusTool,
    GetEmailsTool,
    SendEmailTool,
    AnalyzeEmailsTool,
    GetStarredEmailsTool,
    StarEmailTool,
    UnstarEmailTool,
    SyncEmailsTool,
    DeleteEmailTool,
    GetTrashEmailsTool,
    RestoreEmailTool,
    PermanentDeleteEmailTool,
    EmptyTrashTool,
)
from .tools.profile_tools import (
    GetUserProfileTool,
)
from .tools.blackboard_tools import (
    GetBlackboardStatusTool,
    SyncBlackboardTool,
    GetBlackboardAssignmentsTool,
)
from .tools.tis_tools import (
    GetTisStatusTool,
    GetTisScheduleTool,
)
from .tools.course_tools import (
    ListCoursesTool,
)
from .tools.task_tools import (
    ListTasksTool,
    CreateTaskTool,
    UpdateTaskTool,
    DeleteTaskTool,
)
from .config import (
    LocalAgentConfig,
    load_config,
    save_config,
)
from .template import TemplateLoader

DEFAULT_MAX_HISTORY_MESSAGES = 40


# Patterns to detect file creation claims in agent responses
FILE_CREATION_CLAIM_PATTERNS = [
    # Chinese patterns
    re.compile(r'[我己已已将]?\s*(?:成功|已经|已)?\s*(?:创建|写入|生成|保存).*?(?:文件|故事|文档)',
               re.IGNORECASE | re.UNICODE),
    re.compile(r'(?:已经|已)?\s*(?:在.*)?\s*(?:创建|写入|生成|保存).*?(?:故事|文件)',
               re.IGNORECASE | re.UNICODE),
    re.compile(r'(?:文件|故事|文档)\s*(?:已经|已)?\s*(?:创建|写入|生成|保存)',
               re.IGNORECASE | re.UNICODE),
    # English patterns
    re.compile(r'(?:have\s+)?(?:successfully\s+)?(?:created|written|saved|generated)\s+(?:the\s+)?(?:file|story|stories|document)',
               re.IGNORECASE),
    re.compile(r'(?:file|story|stories|document)\s+(?:has\s+been\s+)?(?:created|written|saved|generated)',
               re.IGNORECASE),
]


@dataclass
class AgentResult:
    """Result of an agent run."""
    content: str
    messages: list[dict[str, Any]]
    tools_used: list[str]
    iterations: int
    hallucination_detected: bool = False


def _detect_file_creation_claims(content: str) -> bool:
    """Detect if the agent claims to have created files without actually calling tools.

    Args:
        content: The agent's response content

    Returns:
        True if file creation is claimed, False otherwise
    """
    if not content:
        return False
    return any(pattern.search(content) for pattern in FILE_CREATION_CLAIM_PATTERNS)


class LocalAgent:
    """Local file management agent with streaming and parallel tool execution."""

    def __init__(
        self,
        workspace: Path,
        provider: OpenAICompatProvider | None = None,
        api_key: str | None = None,
        api_base: str | None = None,
        model: str | None = None,
        max_iterations: int | None = None,
        system_prompt: str | None = None,
        config: LocalAgentConfig | None = None,
    ):
        self.workspace = Path(workspace).resolve()

        self._config = config if config is not None else load_config()

        template_dir = Path(__file__).parent / "template"
        self._template_loader = TemplateLoader(template_dir)

        if api_key is not None or api_base is not None or model is not None or max_iterations is not None:
            provider_name = self._config.get_provider_name(model)

            if provider_name:
                provider_config = getattr(self._config.providers, provider_name, None)
                if provider_config and api_key is not None:
                    provider_config.api_key = api_key
                if provider_config and api_base is not None:
                    provider_config.api_base = api_base

            if model is not None:
                self._config.agent.model = model
            if max_iterations is not None:
                self._config.agent.max_iterations = max_iterations

        self.provider = provider or OpenAICompatProvider(
            api_key=api_key,
            api_base=api_base,
            model=model or self._config.agent.model,
            temperature=self._config.agent.temperature,
            config=self._config,
        )
        self.tools = ToolRegistry()
        self._runtime_context: dict[str, Any] = {}
        self._register_tools()
        self.max_iterations = self._config.agent.max_iterations
        self.system_prompt = system_prompt or self._load_system_prompt()
        self.messages: list[dict[str, Any]] = []
        self._profile_store: Any = None

    @property
    def config(self) -> LocalAgentConfig:
        return self._config

    @property
    def model(self) -> str:
        return self.provider.model

    @property
    def api_base(self) -> str:
        return self.provider.api_base

    @property
    def provider_name(self) -> str | None:
        return self._config.get_provider_name(self.model)

    def _register_tools(self) -> None:
        self.tools.register(ReadFileTool(self.workspace))
        self.tools.register(WriteFileTool(self.workspace))
        self.tools.register(EditFileTool(self.workspace))
        self.tools.register(ListDirTool(self.workspace))
        self.tools.register(CreateDirTool(self.workspace))
        self.tools.register(SearchFilesTool(self.workspace))
        self.tools.register(GrepTool(self.workspace))
        self.tools.register(MoveFileTool(self.workspace))
        self.tools.register(DeleteFileTool(self.workspace))
        self.tools.register(CopyFileTool(self.workspace))
        self.tools.register(ExecTool(self.workspace))
        self.tools.register(CreateScheduleEventTool(lambda: self._runtime_context.get("user_id")))
        self.tools.register(UpdateScheduleEventTool(lambda: self._runtime_context.get("user_id")))
        self.tools.register(UpdateScheduleEventTimeTool(lambda: self._runtime_context.get("user_id")))
        self.tools.register(DeleteScheduleEventTool(lambda: self._runtime_context.get("user_id")))
        self.tools.register(CheckEmailStatusTool(
            lambda: self._runtime_context.get("user_id"),
        ))
        self.tools.register(GetEmailsTool(
            lambda: self._runtime_context.get("user_id"),
        ))
        self.tools.register(SendEmailTool(
            lambda: self._runtime_context.get("user_id"),
        ))
        self.tools.register(AnalyzeEmailsTool(
            lambda: self._runtime_context.get("user_id"),
            self.provider,
            profile_getter=lambda: self._get_user_profile(),
        ))
        self.tools.register(GetStarredEmailsTool(
            lambda: self._runtime_context.get("user_id"),
        ))
        self.tools.register(StarEmailTool(
            lambda: self._runtime_context.get("user_id"),
        ))
        self.tools.register(UnstarEmailTool(
            lambda: self._runtime_context.get("user_id"),
        ))
        self.tools.register(SyncEmailsTool(
            lambda: self._runtime_context.get("user_id"),
        ))
        self.tools.register(DeleteEmailTool(
            lambda: self._runtime_context.get("user_id"),
        ))
        self.tools.register(GetTrashEmailsTool(
            lambda: self._runtime_context.get("user_id"),
        ))
        self.tools.register(RestoreEmailTool(
            lambda: self._runtime_context.get("user_id"),
        ))
        self.tools.register(PermanentDeleteEmailTool(
            lambda: self._runtime_context.get("user_id"),
        ))
        self.tools.register(EmptyTrashTool(
            lambda: self._runtime_context.get("user_id"),
        ))
        self.tools.register(GetUserProfileTool(
            profile_getter=lambda: self._get_user_profile(),
        ))
        self.tools.register(GetBlackboardStatusTool(
            lambda: self._runtime_context.get("user_id"),
        ))
        self.tools.register(SyncBlackboardTool(
            lambda: self._runtime_context.get("user_id"),
        ))
        self.tools.register(GetBlackboardAssignmentsTool(
            lambda: self._runtime_context.get("user_id"),
        ))
        self.tools.register(GetTisStatusTool(
            lambda: self._runtime_context.get("user_id"),
        ))
        self.tools.register(GetTisScheduleTool(
            lambda: self._runtime_context.get("user_id"),
        ))
        self.tools.register(ListCoursesTool(
            lambda: self._runtime_context.get("user_id"),
        ))
        self.tools.register(ListTasksTool(lambda: self._runtime_context.get("user_id")))
        self.tools.register(CreateTaskTool(lambda: self._runtime_context.get("user_id")))
        self.tools.register(UpdateTaskTool(lambda: self._runtime_context.get("user_id")))
        self.tools.register(DeleteTaskTool(lambda: self._runtime_context.get("user_id")))

    def set_runtime_context(self, **context: Any) -> None:
        self._runtime_context.update(context)

    def _load_system_prompt(self) -> str:
        now = datetime.now()
        return self._template_loader.load_template(
            "agent/system.md",
            workspace_path=str(self.workspace),
            current_date=now.strftime("%Y-%m-%d"),
            current_time=now.strftime("%H:%M"),
            current_weekday=["周一","周二","周三","周四","周五","周六","周日"][now.weekday()],
        )

    def _get_user_profile(self) -> dict:
        user_id = self._runtime_context.get("user_id")
        if not user_id or not self._profile_store:
            return {}
        try:
            import sys
            from pathlib import Path as _Path
            _lb = _Path(__file__).resolve().parent.parent / "local_backend"
            if str(_lb) not in sys.path:
                sys.path.insert(0, str(_lb))
            from database.code.operations.database_user_personality_operations import UserPersonalityOperations
            db_profile = UserPersonalityOperations().get_profile(user_id)
            if db_profile:
                return db_profile
        except Exception:
            logger.warning("Profile lookup in DB failed", exc_info=True)
        try:
            return self._profile_store.get_profile(user_id)
        except Exception:
            logger.warning("Profile store lookup failed", exc_info=True)
            return {}

    def update_model(self, model: str) -> None:
        self.provider.update_config(model=model)
        self._config.agent.model = model
        save_config(self._config)

    def update_api_key(self, api_key: str) -> None:
        provider_name = self._config.get_provider_name(self.model)
        if provider_name:
            provider_config = getattr(self._config.providers, provider_name, None)
            if provider_config:
                provider_config.api_key = api_key
                self.provider.update_config(api_key=api_key)
                save_config(self._config)

    def update_api_base(self, api_base: str) -> None:
        provider_name = self._config.get_provider_name(self.model)
        if provider_name:
            provider_config = getattr(self._config.providers, provider_name, None)
            if provider_config:
                provider_config.api_base = api_base
                self.provider.update_config(api_base=api_base)
                save_config(self._config)

    def switch_provider(self, provider_name: str) -> None:
        provider_config = getattr(self._config.providers, provider_name, None)
        if provider_config is None:
            raise ValueError(f"Unknown provider: {provider_name}")

        self._config.agent.provider = provider_name
        api_key = provider_config.api_key
        api_base = provider_config.api_base or self._config.get_api_base(self.model)

        if api_key or api_base:
            self.provider.update_config(api_key=api_key, api_base=api_base)
            save_config(self._config)

    def _trim_history(self) -> None:
        """Trim conversation history to prevent token bloat."""
        max_msgs = DEFAULT_MAX_HISTORY_MESSAGES
        if len(self.messages) <= max_msgs:
            return

        keep = self.messages[-max_msgs:]

        if keep and keep[0].get("role") != "user":
            for i, msg in enumerate(keep):
                if msg.get("role") == "user":
                    keep = keep[i:]
                    break

        self.messages = keep

    def _build_messages(self, user_input: str) -> list[dict[str, Any]]:
        self._trim_history()
        msgs = [{"role": "system", "content": self.system_prompt}]
        msgs.extend(self.messages)
        msgs.append({"role": "user", "content": user_input})
        return msgs

    async def _execute_tool(self, name: str, args: dict[str, Any]) -> str:
        tool = self.tools.get(name)
        if not tool:
            return f"Error: Unknown tool '{name}'"
        try:
            print(f"[AgentTool] calling {name} with args: {json.dumps(args, ensure_ascii=False, default=str)[:200]}")
            result = await tool.execute(**args)
            print(f"[AgentTool] {name} result: {result[:200]}")
            return result
        except Exception as e:
            return f"Error executing {name}: {e}"

    async def _execute_tools_parallel(self, tool_calls: list) -> list[str]:
        """Execute independent tool calls in parallel."""
        if len(tool_calls) <= 1:
            if not tool_calls:
                return []
            tc = tool_calls[0]
            return [await self._execute_tool(tc.name, tc.arguments)]

        tasks = [
            self._execute_tool(tc.name, tc.arguments)
            for tc in tool_calls
        ]
        return await asyncio.gather(*tasks)

    async def run(
        self,
        user_input: str,
        on_stream: Callable[[str], Awaitable[None]] | None = None,
        on_tool: Callable[[str, dict], Awaitable[None]] | None = None,
        enforce_tool_calls: bool = True,
    ) -> AgentResult:
        """Run the agent with user input. Uses streaming when on_stream is provided.

        Args:
            user_input: The user's input message
            on_stream: Optional callback for streaming responses
            on_tool: Optional callback when tools are called
            enforce_tool_calls: If True, verifies that file creation claims match actual tool calls
        """
        messages = self._build_messages(user_input)
        tools_used: list[str] = []
        iterations = 0
        final_content = ""
        hallucination_detected = False

        use_streaming = on_stream is not None

        for iteration in range(self.max_iterations):
            iterations = iteration + 1

            if use_streaming:
                collected_chunks: list[str] = []

                async def _collect_chunk(chunk: str):
                    collected_chunks.append(chunk)
                    if on_stream:
                        await on_stream(chunk)

                response = await self.provider.chat_stream(
                    messages=messages,
                    tools=self.tools.get_schemas(),
                    on_chunk=_collect_chunk,
                )
            else:
                response = await self.provider.chat(
                    messages=messages,
                    tools=self.tools.get_schemas(),
                )

            if not response.tool_calls:
                final_content = response.content or ""

                # Check for hallucination: agent claims to create files but didn't call write_file
                if enforce_tool_calls and _detect_file_creation_claims(final_content):
                    write_file_called = "write_file" in tools_used
                    if not write_file_called:
                        hallucination_detected = True
                        # Add a corrective system message to force actual tool usage
                        correction_msg = {
                            "role": "system",
                            "content": (
                                "检测到您声称创建了文件，但没有调用 write_file 工具。"
                                "根据系统规则，您必须实际调用 write_file 工具才能创建文件。"
                                "请不要只在回复中说已创建文件，必须使用工具调用。"
                                "请现在调用 write_file 工具来完成文件创建任务。"
                            )
                        }
                        messages.append(correction_msg)
                        # Continue to next iteration to force tool call
                        continue

                self.messages.append({"role": "user", "content": user_input})
                self.messages.append({"role": "assistant", "content": final_content})
                break

            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": response.content,
            }
            if response.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                        },
                    }
                    for tc in response.tool_calls
                ]
            messages.append(assistant_msg)

            for tc in response.tool_calls:
                if on_tool:
                    await on_tool(tc.name, tc.arguments)

            results = await self._execute_tools_parallel(response.tool_calls)
            for tc, result in zip(response.tool_calls, results):
                tools_used.append(tc.name)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
        else:
            final_content = "Max iterations reached. Task may not be complete."

        return AgentResult(
            content=final_content,
            messages=messages,
            tools_used=tools_used,
            iterations=iterations,
            hallucination_detected=hallucination_detected,
        )

    def clear_history(self):
        self.messages.clear()

    async def close(self):
        await self.provider.close()

    async def chat(
        self,
        user_input: str,
        on_stream: Callable[[str], Awaitable[None]] | None = None,
        on_tool: Callable[[str, dict], Awaitable[None]] | None = None,
    ) -> str:
        result = await self.run(user_input, on_stream=on_stream, on_tool=on_tool)
        return result.content