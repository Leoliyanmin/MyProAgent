from fastapi import APIRouter, Depends, HTTPException
from typing import List
from presentation.schemas import AgentChatMessage, AgentResponse, ChatHistoryItem
from presentation.dependencies import get_current_user_id
from service.agent_service import AgentService

router = APIRouter(prefix="/agent", tags=["Agent"])
agent_service = AgentService()


@router.post("/chat", response_model=AgentResponse)
async def chat_with_agent(chat_data: AgentChatMessage, user_id: int = Depends(get_current_user_id)):
    result = agent_service.process_query(user_id, chat_data.message, chat_data.session_id or "default")
    return AgentResponse(
        response=result['response'],
        thought_trace=result['thought_trace'],
        tool_calls=result.get('tool_calls', []),
        requires_confirmation=result.get('requires_confirmation', False)
    )


@router.get("/history/{session_id}", response_model=List[ChatHistoryItem])
async def get_chat_history(session_id: str, user_id: int = Depends(get_current_user_id)):
    history = agent_service.get_chat_history(session_id)
    return history
