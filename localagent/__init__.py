"""Minimal local file management agent with session and memory support."""

from .agent import LocalAgent, AgentResult
from .tools.base import ToolRegistry
from .session import Session, SessionManager
from .memory import MemoryStore, Dream, ConsolidationResult
from .api import start_server, AgentServer

__all__ = [
    "LocalAgent",
    "AgentResult",
    "ToolRegistry",
    "Session",
    "SessionManager",
    "MemoryStore",
    "Dream",
    "ConsolidationResult",
    "start_server",
    "AgentServer",
]