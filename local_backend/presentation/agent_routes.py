from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import List
from presentation.schemas import AgentChatMessage, AgentResponse, ChatHistoryItem
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
    """WebSocket 端点用于实时聊天和工具调用追踪"""
    # 验证用户
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

                # 发送用户消息回显
                await websocket.send_json({
                    "type": "message",
                    "role": "user",
                    "content": message
                })

                try:
                    # 处理消息
                    result = await agent_service.process_with_local_agent(
                        user_id=user_id,
                        message=message,
                        session_id=actual_session_id
                    )

                    # 发送工具调用事件
                    for tool in result.get('tool_calls', []):
                        await websocket.send_json({
                            "type": "tool",
                            "tool": tool
                        })

                    # 发送助手响应
                    if result.get('response'):
                        await websocket.send_json({
                            "type": "message",
                            "role": "assistant",
                            "content": result['response']
                        })

                    # 发送完成信号
                    await websocket.send_json({
                        "type": "done",
                        "iterations": result.get('iterations', 0),
                        "tools_used": result.get('tool_calls', [])
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
