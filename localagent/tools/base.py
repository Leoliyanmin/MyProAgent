"""Base classes for LocalAgent tools."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class BaseTool(ABC):
    """Base class for all tools."""

    name: str = ""
    description: str = ""
    parameters: dict[str, Any] = {}

    def to_schema(self) -> dict[str, Any]:
        """Convert tool to OpenAI function schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """Execute the tool with given parameters."""
        pass


@dataclass
class ToolCall:
    """A tool call request from the LLM."""
    id: str
    name: str
    arguments: dict[str, Any]


class ToolRegistry:
    """Registry for managing tools."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._schemas_cache: list[dict[str, Any]] | None = None

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool
        self._schemas_cache = None

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)
        self._schemas_cache = None

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def get_schemas(self) -> list[dict[str, Any]]:
        if self._schemas_cache is None:
            self._schemas_cache = [tool.to_schema() for tool in self._tools.values()]
        return self._schemas_cache

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())

    def __len__(self):
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
