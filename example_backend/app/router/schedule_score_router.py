from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db
from service import user_service
from model import schemas
from service.schedule_score_service import score_schedule

router = APIRouter(prefix="/schedule-score", tags=["Schedule AI"])

@router.get("/")
async def get_schedule_score(
    llm: str | None = Query(None, description="可选指定用于生成建议的LLM模型，如 gpt-4o"),
    db: Session = Depends(get_db),
    current_user: schemas.UserInDB = Depends(user_service.get_current_user)
):
    """对当前用户的日程进行AI评分并生成建议。"""
    return score_schedule(db, current_user.user_id, llm)
