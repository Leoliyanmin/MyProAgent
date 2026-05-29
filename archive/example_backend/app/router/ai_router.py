from fastapi import APIRouter, Depends, Body, Form, File, UploadFile, Response
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from core.database import get_db
from service import user_service, ai_service
from model import schemas

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

@router.post("/chat")
async def chat_with_ai(
    llm: str,
    query: str = Body(..., embed=True),
    conversation_id: str | None = Body(None, embed=True),
    db: Session = Depends(get_db),
    current_user: schemas.UserInDB = Depends(user_service.get_current_user)
):
    """与AI助手聊天"""
    response = ai_service.process_user_query(llm, db, current_user.user_id, query, conversation_id)
    return {"response": response}

@router.post("/agent")
async def chat_with_sql_agent(
    llm: str,
    query: str = Body(..., embed=True),
    conversation_id: str | None = Body(None, embed=True),
    current_user: schemas.UserInDB = Depends(user_service.get_current_user)
):
    """
    专门调用 LangChain SQL Agent 进行数据库查询和修改。
    """
    response = ai_service.process_agent_query(llm, query, current_user.user_id, conversation_id)
    return {"response": response}

@router.post("/voice-chat")
async def voice_chat_with_ai(
    llm: str = Form(...),  # 使用 Form 接收普通参数，因为不能和 File 混用 Pydantic Body
    file: UploadFile = File(...), # 接收音频文件
    conversation_id: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: schemas.UserInDB = Depends(user_service.get_current_user)
):
    """
    语音对话接口：
    1. 接收语音 (ASR) -> 转文本
    2. 文本问答 (RAG) -> 获取回复
    3. 回复转语音 (TTS) -> 返回音频流
    """
    
    # 1. 语音转文本
    try:
        user_query_text = ai_service.transcribe_audio(file)
        print(f"用户语音转录结果: {user_query_text}")
    except Exception as e:
        return {"error": f"语音识别失败: {str(e)}"}

    if not user_query_text:
        return {"error": "未识别到有效的语音内容"}

    # 2. 调用现有的 RAG 业务逻辑
    # 注意：这里复用了 ai_service.process_user_query
    ai_response_text = ai_service.process_user_query(llm, db, current_user.user_id, user_query_text, conversation_id)
    
    # 3. 文本转语音
    audio_content = ai_service.text_to_speech(ai_response_text)

    # 4. 返回音频流
    # 前端接收到 blob 后可以直接播放
    return Response(content=audio_content, media_type="audio/mpeg")


@router.post("/reset-memory")
async def reset_memory(conversation_id: str = Body(..., embed=True)):
    """清空指定对话框的短期记忆。"""
    ai_service.reset_conversation_memory(conversation_id)
    return {"ok": True}


@router.post("/recommend-activities", response_model=schemas.ActivityRecommendationsResponse)
async def recommend_activities(
    llm: str,
    count: int = 3,
    db: Session = Depends(get_db),
    current_user: schemas.UserInDB = Depends(user_service.get_current_user)
):
    """根据邮件内容与兴趣推荐 2-3 个活动。"""
    items = ai_service.recommend_activities(llm, db, current_user.user_id, count=count)
    return {"items": items}