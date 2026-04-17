from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from presentation.schemas import AgentChatMessage, AgentResponse, ChatHistoryItem
from presentation.dependencies import get_current_user_id
from service.agent_service import AgentService

router = APIRouter(prefix="/agent", tags=["Agent"])
agent_service = AgentService()


@router.post("/chat", response_model=AgentResponse)
async def chat_with_agent(chat_data: AgentChatMessage, user_id: str = Depends(get_current_user_id)):
    result = agent_service.process_query(user_id, chat_data.message, chat_data.session_id or "default")
    return AgentResponse(
        response=result['response'],
        thought_trace=result['thought_trace'],
        tool_calls=result.get('tool_calls', []),
        requires_confirmation=result.get('requires_confirmation', False)
    )


@router.get("/history/{session_id}", response_model=List[ChatHistoryItem])
async def get_chat_history(session_id: str, user_id: str = Depends(get_current_user_id)):
    result = agent_service.get_chat_history(user_id, session_id)
    if not result.get('success'):
        raise HTTPException(status_code=400, detail=result.get('message', 'Failed to get chat history'))
    return result.get('history', [])


@router.post("/nanobot/chat")
async def chat_with_nanobot(message: str, client_id: str = "local_backend"):
    result = await agent_service.chat_with_nanobot(message, client_id)
    if not result.get('success'):
        raise HTTPException(status_code=503, detail=result.get('response', 'Failed to connect to nanobot'))
    return JSONResponse(content=result, media_type="application/json; charset=utf-8")
