from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import List
import asyncio
from presentation.schemas import (
    AgentChatMessage,
    AgentFileManagerDirectoryCreateRequest,
    AgentFileManagerFileCreateRequest,
    AgentFileManagerFileDeleteRequest,
    AgentFileManagerFileReadRequest,
    AgentFileManagerFileRenameRequest,
    AgentFileManagerFileUpdateRequest,
    AgentFileManagerPathDeleteRequest,
    AgentFileManagerListRequest,
    AgentFileManagerListResponse,
    AgentFileManagerMessage,
    AgentFileManagerOperationResponse,
    AgentFileManagerFileReadResponse,
    AgentResponse,
    ChatHistoryItem,
    AgentConfigUpdateRequest,
    AgentConfigUpdateResponse,
    AgentTestConnectionResponse,
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


@router.post("/file-manager/dir/create", response_model=AgentFileManagerOperationResponse)
async def create_directory(
    request: AgentFileManagerDirectoryCreateRequest,
    _: str = Depends(get_current_user_id),
):
    """创建目录：在指定目录下新建文件夹。"""
    try:
        result = agent_service.create_directory(
            working_directory=request.working_directory,
            relative_path=request.relative_path or "",
            dirname=request.dirname,
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


@router.post("/file-manager/file/delete-path", response_model=AgentFileManagerOperationResponse)
async def delete_file_by_path(
    request: AgentFileManagerPathDeleteRequest,
    _: str = Depends(get_current_user_id),
):
    """按路径删除文件（支持绝对路径或相对路径）。"""
    try:
        result = agent_service.delete_by_path(
            path=request.path,
            working_directory=request.working_directory,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return AgentFileManagerOperationResponse(
        success=result["success"],
        message=result["message"],
        working_directory=request.working_directory or "",
        relative_path="",
        filename=Path(request.path).name,
    )


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
async def get_agent_session(session_id: str, user_id: str = Depends(get_current_user_id)):
    """获取 LocalAgent 会话消息"""
    actual_session_id = f"{user_id}_{session_id}"
    result = agent_service.get_local_agent_session(actual_session_id)
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
        "api_key": f"{agent_service.agent.provider.api_key[:10]}..." if agent_service.agent.provider.api_key else "None",
    }

@router.post("/config/update", response_model=AgentConfigUpdateResponse)
async def update_agent_config(
    request: AgentConfigUpdateRequest,
    _: str = Depends(get_current_user_id)
):
    """更新 Agent 配置"""
    try:
        result = agent_service.update_agent_config(
            provider=request.provider,
            model=request.model,
            api_key=request.api_key,
            api_base=request.api_base,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/test", response_model=AgentTestConnectionResponse)
async def test_agent_connection(_: str = Depends(get_current_user_id)):
    """测试 Agent API 连接"""
    try:
        result = await agent_service.test_connection()
        return result
    except Exception as e:
        return AgentTestConnectionResponse(
            success=False,
            message=f"测试失败: {str(e)}",
            error=str(e),
            type=type(e).__name__,
        )


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
        await websocket.accept()
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


# ==================== 用户画像端点 ====================

@router.get("/profile")
async def get_user_profile(user_id: str = Depends(get_current_user_id)):
    """获取当前用户的完整画像（含 MBTI）"""
    profile = agent_service.get_user_profile(user_id)
    return profile


@router.get("/profile/mbti")
async def get_user_mbti(user_id: str = Depends(get_current_user_id)):
    """获取 MBTI 推断结果"""
    mbti = agent_service.get_user_mbti(user_id)
    return mbti


@router.get("/profile/interactions")
async def get_user_interactions(
    limit: int = 20,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
):
    """获取交互历史列表（分页）"""
    return agent_service.get_user_interactions(user_id, limit, offset)


@router.get("/profile/interactions/{conversation_id}")
async def get_interaction_detail(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """获取单条交互详情"""
    interaction = agent_service.interaction_logger.get_interaction(conversation_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="交互记录不存在")
    if interaction.get("metadata", {}).get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="无权查看他人的交互记录")
    return interaction


@router.post("/profile/reanalyze")
async def reanalyze_profile(user_id: str = Depends(get_current_user_id)):
    """重新分析所有交互，更新画像和 MBTI"""
    import datetime
    start_time = datetime.datetime.now()
    print(f"\n{'='*60}")
    print(f"[Reanalyze] 开始重新分析用户 {user_id}")

    interactions = agent_service.interaction_logger.get_user_interactions(user_id, limit=9999)
    if not interactions:
        print(f"[Reanalyze] 没有交互记录需要分析")
        print(f"{'='*60}")
        return {"success": True, "message": "没有交互记录需要分析", "interactions_processed": 0}

    total = len(interactions)
    print(f"[Reanalyze] 找到 {total} 条交互记录，开始逐条分析...")

    agent_service.profile_store.delete_profile(user_id)
    print(f"[Reanalyze] 已清除旧画像")

    for i, interaction in enumerate(interactions, 1):
        msg = interaction.get("user_input", {}).get("raw_message", "")[:50]
        print(f"\n[Reanalyze] [{i}/{total}] 正在分析交互: \"{msg}...\"")
        try:
            update = await asyncio.wait_for(
                agent_service.profile_extractor.extract_from_interaction(interaction),
                timeout=15.0,
            )
            agent_service.profile_store.update_profile(user_id, update)
            print(f"[Reanalyze] [{i}/{total}] 完成")
        except asyncio.TimeoutError:
            print(f"[Reanalyze] [{i}/{total}] 超时跳过")
        except Exception as e:
            print(f"[Reanalyze] [{i}/{total}] 错误: {e}")

    profile = agent_service.profile_store.get_profile(user_id)
    raw_messages = [
        it["user_input"]["raw_message"]
        for it in interactions
        if it.get("user_input", {}).get("raw_message")
    ]
    print(f"\n[Reanalyze] 开始 MBTI 大模型分析（共 {len(raw_messages)} 条对话）...")
    try:
        mbti = await asyncio.wait_for(
            agent_service.mbti_inferencer.infer_mbti(profile, raw_messages=raw_messages),
            timeout=30.0,
        )
        agent_service.profile_store.update_mbti(user_id, mbti)
        print(f"[Reanalyze] MBTI 分析完成: {mbti.get('mbti_type', 'unknown')}")
    except asyncio.TimeoutError:
        print("[Reanalyze] MBTI 分析超时")
    except Exception as e:
        print(f"[Reanalyze] MBTI 分析错误: {e}")

    elapsed = (datetime.datetime.now() - start_time).total_seconds()
    print(f"[Reanalyze] 全部完成！耗时 {elapsed:.1f} 秒")
    print(f"{'='*60}\n")

    return {
        "success": True,
        "message": "重新分析完成",
        "interactions_processed": len(interactions),
        "profile_updated": True,
        "mbti_updated": True
    }


@router.delete("/profile/interactions/{conversation_id}")
async def delete_interaction(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """删除单条交互记录"""
    interaction = agent_service.interaction_logger.get_interaction(conversation_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="交互记录不存在")
    if interaction.get("metadata", {}).get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="无权删除他人的交互记录")

    success = agent_service.interaction_logger.delete_interaction(conversation_id)
    return {"success": success, "message": "删除成功" if success else "删除失败"}
