"""FastAPI server for local agent."""

import asyncio
import httpx
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .agent import LocalAgent, AgentResult
from .config import load_config
from .memory import MemoryStore, Dream
from .session import SessionManager


app = FastAPI(title="Local Agent API")


class ChatRequest(BaseModel):
    message: str
    session_key: str = "default"


class ChatResponse(BaseModel):
    content: str
    tools_used: list[str]
    iterations: int


class SessionInfo(BaseModel):
    key: str
    created_at: str
    updated_at: str
    message_count: int


class ConsolidationResponse(BaseModel):
    success: bool
    entries_processed: int
    summary: str | None


class AgentServer:
    """Agent server with session and memory management."""

    def __init__(self, workspace: Path):
        self.workspace = Path(workspace).resolve()
        self.config = load_config()
        self.session_manager = SessionManager(self.workspace)
        self.memory_store = MemoryStore(self.workspace)
        self._agent: LocalAgent | None = None

    @property
    def agent(self) -> LocalAgent:
        """Get or create agent instance."""
        if self._agent is None:
            self._agent = LocalAgent(workspace=self.workspace, config=self.config)
        return self._agent

    async def chat(self, message: str, session_key: str = "default") -> AgentResult:
        """Process a chat message."""
        session = self.session_manager.get_or_create(session_key)

        result = await self.agent.run(message)

        # Save to session
        session.add_message("user", message)
        if result.content:
            session.add_message("assistant", result.content)
        self.session_manager.save(session)

        # Add to memory for consolidation
        self.memory_store.add_entry(message)

        return result

    async def consolidate_memory(self) -> ConsolidationResponse:
        """Run memory consolidation."""
        dream = Dream(
            store=self.memory_store,
            provider=self.agent.provider,
            workspace=self.workspace,
        )
        result = await dream.run()
        return ConsolidationResponse(
            success=result.success,
            entries_processed=result.entries_processed,
            summary=result.summary,
        )

    def get_memory(self) -> str:
        """Get current memory."""
        return self.memory_store.get_memory()

    def list_sessions(self) -> list[SessionInfo]:
        """List all sessions."""
        sessions = self.session_manager.list_sessions()
        return [
            SessionInfo(
                key=s["key"],
                created_at=s["created_at"],
                updated_at=s["updated_at"],
                message_count=s["message_count"],
            )
            for s in sessions
        ]

    def delete_session(self, key: str) -> bool:
        """Delete a session."""
        return self.session_manager.delete(key)

    def clear_session(self, key: str) -> bool:
        """Clear a session's messages."""
        session = self.session_manager.get_or_create(key)
        session.clear()
        self.session_manager.save(session)
        return True


# Global server instance
_server: AgentServer | None = None


def get_server() -> AgentServer:
    """Get the global server instance."""
    global _server
    if _server is None:
        _server = AgentServer(workspace=Path.cwd())
    return _server


# API Routes


@app.get("/")
async def root() -> HTMLResponse:
    """Serve the web UI."""
    html_path = Path(__file__).parent / "templates" / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Local Agent</h1><p>请检查templates/index.html文件是否存在</p>")


@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """Send a chat message."""
    server = get_server()
    result = await server.chat(request.message, request.session_key)
    return ChatResponse(
        content=result.content,
        tools_used=result.tools_used,
        iterations=result.iterations,
    )


@app.get("/api/sessions")
async def list_sessions() -> list[SessionInfo]:
    """List all sessions."""
    return get_server().list_sessions()


@app.get("/api/sessions/{session_key}/messages")
async def get_session_messages(session_key: str) -> list[dict[str, Any]]:
    """Get messages for a session."""
    server = get_server()
    session = server.session_manager.get_or_create(session_key)
    return [
        {"role": msg["role"], "content": msg.get("content", "")}
        for msg in session.messages
    ]


@app.delete("/api/sessions/{session_key}")
async def delete_session(session_key: str) -> dict[str, bool]:
    """Delete a session."""
    success = get_server().delete_session(session_key)
    return {"success": success}


@app.post("/api/sessions/{session_key}/clear")
async def clear_session(session_key: str) -> dict[str, bool]:
    """Clear a session's messages."""
    success = get_server().clear_session(session_key)
    return {"success": success}


@app.get("/api/memory")
async def get_memory() -> dict[str, str]:
    """Get current memory."""
    return {"content": get_server().get_memory()}


@app.post("/api/memory/consolidate")
async def consolidate_memory() -> ConsolidationResponse:
    """Run memory consolidation."""
    return await get_server().consolidate_memory()


@app.get("/api/status")
async def get_status() -> dict[str, Any]:
    """Get agent status."""
    server = get_server()
    return {
        "provider": server.agent.provider_name,
        "model": server.agent.model,
        "api_base": server.agent.api_base,
        "api_key": f"{server.agent.provider.api_key[:10]}..." if server.agent.provider.api_key else "None",
    }


@app.get("/api/test")
async def test_connection() -> dict[str, Any]:
    """Test API connection."""
    server = get_server()
    agent = server.agent

    try:
        client = httpx.AsyncClient(
            base_url=agent.api_base,
            headers={
                "Authorization": f"Bearer {agent.provider.api_key}",
                "Content-Type": "application/json",
            },
            timeout=10.0,
        )

        payload = {
            "model": agent.model,
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 10,
        }

        resp = await client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        return {
            "success": True,
            "status": resp.status_code,
            "message": "Connection successful",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "type": type(e).__name__,
        }


@app.get("/api/files")
async def list_files(path: str = "") -> dict[str, Any]:
    """List files in workspace."""
    server = get_server()

    try:
        target_path = server.workspace / path if path else server.workspace

        if not target_path.exists():
            return {"error": "路径不存在", "items": []}

        if not target_path.is_dir():
            return {"error": "不是目录", "items": []}

        items = []
        for item in sorted(target_path.iterdir()):
            try:
                rel_path = item.relative_to(server.workspace)
                items.append({
                    "name": item.name,
                    "path": str(rel_path),
                    "type": "dir" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0,
                })
            except Exception:
                continue

        return {"current_path": path, "items": items}
    except Exception as e:
        return {"error": str(e), "items": []}


@app.get("/api/files/read")
async def read_file(path: str) -> dict[str, Any]:
    """Read file content."""
    server = get_server()

    try:
        file_path = server.workspace / path

        if not file_path.exists():
            return {"error": "文件不存在"}

        if not file_path.is_file():
            return {"error": "不是文件"}

        content = file_path.read_text(encoding="utf-8", errors="replace")

        # Truncate large files
        if len(content) > 50000:
            content = content[:50000] + "\n\n... (文件过大，已截断)"

        return {"path": path, "content": content}
    except Exception as e:
        return {"error": str(e)}


@app.websocket("/ws/{session_key}")
async def websocket_endpoint(websocket: WebSocket, session_key: str):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    server = get_server()
    session = server.session_manager.get_or_create(session_key)

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "chat":
                message = data.get("message", "")

                # Send user message back
                await websocket.send_json({
                    "type": "message",
                    "role": "user",
                    "content": message
                })

                try:
                    # Process message with streaming
                    result = await server.agent.run(message, on_stream=None)

                    if result.content:
                        await websocket.send_json({
                            "type": "message",
                            "role": "assistant",
                            "content": result.content
                        })

                    # Save to session and memory
                    session.add_message("user", message)
                    if result.content:
                        session.add_message("assistant", result.content)
                    server.session_manager.save(session)
                    server.memory_store.add_entry(message)

                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "content": f"错误: {str(e)}\n\n请检查:\n1. API密钥是否正确\n2. 网络连接是否正常\n3. 点击左侧'测试连接'按钮"
                    })
                finally:
                    await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")


def start_server(host: str = "127.0.0.1", port: int = 8000, workspace: str | Path | None = None):
    """Start the FastAPI server."""
    import uvicorn

    if workspace:
        global _server
        _server = AgentServer(workspace=Path(workspace))

    uvicorn.run(app, host=host, port=port)
