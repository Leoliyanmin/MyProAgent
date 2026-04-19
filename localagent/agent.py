"""Core agent implementation - minimal version."""

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Awaitable

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
)
from .config import (
    LocalAgentConfig,
    load_config,
    save_config,
)
from .template import TemplateLoader



@dataclass
class AgentResult:
    """Result of an agent run."""
    content: str
    messages: list[dict[str, Any]]
    tools_used: list[str]
    iterations: int


class LocalAgent:
    """Minimal local file management agent.

    Usage:
        agent = LocalAgent(workspace=Path("."))
        result = await agent.run("List all Python files and find the main function")
        print(result.content)
    """

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

        # Load config if not provided
        self._config = config if config is not None else load_config()

        # Initialize template loader
        template_dir = Path(__file__).parent / "template"
        self._template_loader = TemplateLoader(template_dir)

        # Apply overrides from args
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
        self._register_tools()
        self.max_iterations = self._config.agent.max_iterations
        self.system_prompt = system_prompt or self._load_system_prompt()
        self.messages: list[dict[str, Any]] = []

    @property
    def config(self) -> LocalAgentConfig:
        """Current configuration."""
        return self._config

    @property
    def model(self) -> str:
        """Current model name."""
        return self.provider.model

    @property
    def api_base(self) -> str:
        """Current API base URL."""
        return self.provider.api_base

    @property
    def provider_name(self) -> str | None:
        """Current provider name."""
        return self._config.get_provider_name(self.model)

    def _register_tools(self) -> None:
        """Register all available tools."""
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

    def _load_system_prompt(self) -> str:
        """Load system prompt from template files."""
        return self._template_loader.load_template(
            "agent/system.md",
            workspace_path=str(self.workspace),
        )

    def update_model(self, model: str) -> None:
        """Update the model at runtime."""
        self.provider.update_config(model=model)
        self._config.agent.model = model
        save_config(self._config)

    def update_api_key(self, api_key: str) -> None:
        """Update the API key at runtime."""
        provider_name = self._config.get_provider_name(self.model)
        if provider_name:
            provider_config = getattr(self._config.providers, provider_name, None)
            if provider_config:
                provider_config.api_key = api_key
                self.provider.update_config(api_key=api_key)
                save_config(self._config)

    def update_api_base(self, api_base: str) -> None:
        """Update the API base URL at runtime."""
        provider_name = self._config.get_provider_name(self.model)
        if provider_name:
            provider_config = getattr(self._config.providers, provider_name, None)
            if provider_config:
                provider_config.api_base = api_base
                self.provider.update_config(api_base=api_base)
                save_config(self._config)

    def switch_provider(self, provider_name: str) -> None:
        """Switch to a different provider."""
        provider_config = getattr(self._config.providers, provider_name, None)
        if provider_config is None:
            raise ValueError(f"Unknown provider: {provider_name}")

        self._config.agent.provider = provider_name
        api_key = provider_config.api_key
        api_base = provider_config.api_base or self._config.get_api_base(self.model)

        if api_key or api_base:
            self.provider.update_config(api_key=api_key, api_base=api_base)
            save_config(self._config)

    def _build_messages(self, user_input: str) -> list[dict[str, Any]]:
        """Build message list for LLM request."""
        msgs = [{"role": "system", "content": self.system_prompt}]
        msgs.extend(self.messages)
        msgs.append({"role": "user", "content": user_input})
        return msgs

    async def _execute_tool(self, name: str, args: dict[str, Any]) -> str:
        """Execute a tool and return the result."""
        tool = self.tools.get(name)
        if not tool:
            return f"Error: Unknown tool '{name}'"
        try:
            return await tool.execute(**args)
        except Exception as e:
            return f"Error executing {name}: {e}"

    async def run(
        self,
        user_input: str,
        on_stream: Callable[[str], Awaitable[None]] | None = None,
        on_tool: Callable[[str, dict], Awaitable[None]] | None = None,
    ) -> AgentResult:
        """Run the agent with user input.

        Args:
            user_input: User's message
            on_stream: Optional callback for streaming content
            on_tool: Optional callback when tool is called

        Returns:
            AgentResult with final content and metadata
        """
        messages = self._build_messages(user_input)
        tools_used: list[str] = []
        iterations = 0
        final_content = ""

        for iteration in range(self.max_iterations):
            iterations = iteration + 1

            response = await self.provider.chat(
                messages=messages,
                tools=self.tools.get_schemas(),
            )

            if on_stream and response.content:
                await on_stream(response.content)

            if not response.tool_calls:
                final_content = response.content or ""
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

                result = await self._execute_tool(tc.name, tc.arguments)
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
        )

    def clear_history(self):
        """Clear conversation history."""
        self.messages.clear()

    async def close(self):
        """Close provider connection."""
        await self.provider.close()

    async def chat(
        self,
        user_input: str,
        on_stream: Callable[[str], Awaitable[None]] | None = None,
        on_tool: Callable[[str, dict], Awaitable[None]] | None = None,
    ) -> str:
        """Simple chat interface - returns just the content."""
        result = await self.run(user_input, on_stream=on_stream, on_tool=on_tool)
        return result.content
