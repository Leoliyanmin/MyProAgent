from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import List
from presentation.schemas import (
    AgentChatMessage,
    AgentFileManagerFileCreateRequest,
    AgentFileManagerFileDeleteRequest,
    AgentFileManagerFileReadRequest,
    AgentFileManagerFileRenameRequest,
    AgentFileManagerFileUpdateRequest,
    AgentFileManagerListRequest,
    AgentFileManagerListResponse,
    AgentFileManagerMessage,
    AgentFileManagerOperationResponse,
    AgentFileManagerFileReadResponse,
    AgentResponse,
    ChatHistoryItem,
)
from presentation.dependencies import get_current_user_id, get_current_user_id_websocket
from service.agent_service import AgentService

router = APIRouter(prefix="/agent", tags=["Agent"])
agent_service = AgentService()


# ==================== 核心聊天端点（使用 LocalAgent）====================

@router.post("/chat", response_model=AgentResponse)
async def chat_with_agent(chat_data: AgentChatMessage, user_id: str = Depends(get_current_user_id)):
    """使用 LocalAgent 处理聊天请求（支持文件管理功能）- 核心端点"""
    result = await agent_service.process_with_local_agent(
        user_id=user_id,
        message=chat_data.message,
        session_id=chat_data.session_id or f"{user_id}_default"
    )
    return AgentResponse(
        response=result.get('response', ''),
        thought_trace=result.get('thought_trace', []),
        tool_calls=result.get('tool_calls', []),
        requires_confirmation=result.get('requires_confirmation', False)
    )


@router.post("/chat/file-manager", response_model=AgentResponse)
async def chat_with_agent_for_file_manager(
    chat_data: AgentFileManagerMessage,
    user_id: str = Depends(get_current_user_id),
):
    """文件管理专用聊天端点：要求传入工作目录并注入到 agent 上下文。"""
    try:
        result = await agent_service.process_with_local_agent(
            user_id=user_id,
            message=chat_data.message,
            session_id=chat_data.session_id or f"{user_id}_file_manager",
            working_directory=chat_data.working_directory,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return AgentResponse(
        response=result.get('response', ''),
        thought_trace=result.get('thought_trace', []),
        tool_calls=result.get('tool_calls', []),
        requires_confirmation=result.get('requires_confirmation', False)
    )


@router.post("/file-manager/list", response_model=AgentFileManagerListResponse)
async def list_file_manager_directory(
    request: AgentFileManagerListRequest,
    _: str = Depends(get_current_user_id),
):
    """列出工作目录下指定子目录内容，用于 Finder 风格文件浏览。"""
    try:
        result = agent_service.list_working_directory(
            working_directory=request.working_directory,
            relative_path=request.relative_path or "",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return AgentFileManagerListResponse(**result)


@router.post("/file-manager/file/create", response_model=AgentFileManagerOperationResponse)
async def create_file_by_name(
    request: AgentFileManagerFileCreateRequest,
    _: str = Depends(get_current_user_id),
):
    """文件名级创建：在指定目录创建空文件。"""
    try:
        result = agent_service.create_file_name(
            working_directory=request.working_directory,
            relative_path=request.relative_path or "",
            filename=request.filename,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return AgentFileManagerOperationResponse(**result)


@router.post("/file-manager/file/rename", response_model=AgentFileManagerOperationResponse)
async def rename_file_by_name(
    request: AgentFileManagerFileRenameRequest,
    _: str = Depends(get_current_user_id),
):
    """文件名级更新：仅重命名文件，不改内容。"""
    try:
        result = agent_service.rename_file_name(
            working_directory=request.working_directory,
            relative_path=request.relative_path or "",
            old_filename=request.old_filename,
            new_filename=request.new_filename,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return AgentFileManagerOperationResponse(**result)


@router.post("/file-manager/file/read", response_model=AgentFileManagerFileReadResponse)
async def read_file_by_name(
    request: AgentFileManagerFileReadRequest,
    _: str = Depends(get_current_user_id),
):
    """文件名级读取：读取指定文件的内容。"""
    try:
        result = agent_service.read_file_name(
            working_directory=request.working_directory,
            filename=request.filename,
            relative_path=request.relative_path or "",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return AgentFileManagerFileReadResponse(**result)


@router.post("/file-manager/file/update", response_model=AgentFileManagerOperationResponse)
async def update_file_by_name(
    request: AgentFileManagerFileUpdateRequest,
    _: str = Depends(get_current_user_id),
):
    """文件名级更新：修改文件内容。"""
    try:
        result = agent_service.update_file_name(
            working_directory=request.working_directory,
            filename=request.filename,
            content=request.content,
            relative_path=request.relative_path or "",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return AgentFileManagerOperationResponse(**result)


@router.post("/file-manager/file/delete", response_model=AgentFileManagerOperationResponse)
async def delete_file_by_name(
    request: AgentFileManagerFileDeleteRequest,
    _: str = Depends(get_current_user_id),
):
    """文件名级删除：删除指定文件。"""
    try:
        result = agent_service.delete_file_name(
            working_directory=request.working_directory,
            relative_path=request.relative_path or "",
            filename=request.filename,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return AgentFileManagerOperationResponse(**result)


@router.get("/history/{session_id}", response_model=List[ChatHistoryItem])
async def get_chat_history(session_id: str, user_id: str = Depends(get_current_user_id)):
    """获取聊天历史"""
    result = agent_service.get_chat_history(user_id, session_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', 'Failed to get chat history'))
    return result.get('history', [])


@router.get("/session/{session_id}")
async def get_agent_session(session_id: str, _: str = Depends(get_current_user_id)):
    """获取 LocalAgent 会话消息"""
    result = agent_service.get_local_agent_session(session_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', 'Failed to get session'))
    return result


@router.post("/session/{session_id}/clear")
async def clear_agent_session(session_id: str, _: str = Depends(get_current_user_id)):
    """清除 LocalAgent 会话"""
    result = agent_service.clear_local_agent_session(session_id)
    return result


@router.get("/memory")
async def get_agent_memory(_: str = Depends(get_current_user_id)):
    """获取 LocalAgent 记忆内容"""
    result = agent_service.get_memory_content()
    return result


@router.post("/memory/consolidate")
async def consolidate_agent_memory(_: str = Depends(get_current_user_id)):
    """运行 LocalAgent 记忆整合"""
    result = await agent_service.consolidate_memory()
    return result


@router.get("/status")
async def get_agent_status(_: str = Depends(get_current_user_id)):
    """获取 LocalAgent 状态"""
    return {
        "model": agent_service.agent.model,
        "provider": agent_service.agent.provider_name,
        "api_base": agent_service.agent.api_base,
        "workspace": str(agent_service.agent.workspace),
        "has_api_key": bool(agent_service.agent.provider.api_key)
    }


# ==================== Nanobot 端点（可选）====================

@router.post("/nanobot/chat")
async def chat_with_nanobot(message: str, client_id: str = "local_backend"):
    """连接到 Nanobot 服务"""
    result = await agent_service.chat_with_nanobot(message, client_id)
    if not result.get('success'):
        raise HTTPException(status_code=503, detail=result.get('response', 'Failed to connect to nanobot'))
    return JSONResponse(content=result, media_type="application/json; charset=utf-8")


# ==================== WebSocket 端点 ====================

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket 端点，支持流式 token 推送"""
    user_id = await get_current_user_id_websocket(websocket)
    if not user_id:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()
    actual_session_id = f"{user_id}_{session_id}"

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "chat":
                message = data.get("message", "")

                await websocket.send_json({
                    "type": "message",
                    "role": "user",
                    "content": message
                })

                try:
                    streamed_content_parts: list[str] = []

                    async def on_stream(chunk: str):
                        streamed_content_parts.append(chunk)
                        await websocket.send_json({
                            "type": "stream",
                            "content": chunk,
                        })

                    async def on_tool(name: str, args: dict):
                        await websocket.send_json({
                            "type": "tool_start",
                            "tool": name,
                            "args": args,
                        })

                    result = await agent_service.process_with_local_agent(
                        user_id=user_id,
                        message=message,
                        session_id=actual_session_id,
                        on_stream=on_stream,
                    )

                    for tool in result.get('tool_calls', []):
                        await websocket.send_json({
                            "type": "tool",
                            "tool": tool
                        })

                    final_content = result.get('response', '')
                    if final_content and not streamed_content_parts:
                        await websocket.send_json({
                            "type": "message",
                            "role": "assistant",
                            "content": final_content
                        })

                    await websocket.send_json({
                        "type": "done",
                        "iterations": result.get('iterations', 0),
                        "tools_used": result.get('tool_calls', []),
                        "pending_deletions": result.get('pending_deletions', []),
                    })

                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "content": f"错误: {str(e)}"
                    })
                    await websocket.send_json({"type": "done"})

            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close(code=4000, reason=str(e))
        except:
            pass
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close(code=4000, reason=str(e))
        except:
            pass
