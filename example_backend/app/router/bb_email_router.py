from typing import List, Dict, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from service.email import email_query_service

router = APIRouter(prefix="/blackboard/email", tags=["blackboard"]) 


@router.get("/", response_model=Dict[str, Any])
async def list_blackboard_email(
    user_id: int = Query(..., ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    使用 SQL 在 email_query_service 中筛选 sender 包含 'blackboard@sustech.edu.cn' 的邮件，
    返回 JSON：
    {
      "total": int,
      "items": [
        {
          "id": int,
          "subject": str,
          "sender": str,
          "received_time": str,   # YYYY-MM-DD HH:MM
          "summary": str          # 优先 summary，其次 snippet，再次 body_text（截断160字）
        }
      ]
    }
    """
    result = email_query_service.list_blackboard_emails_for_user(db, user_id)

    # 兼容多种返回结构：对象 / dict / list
    items = []
    total = 0
    if isinstance(result, dict):
        items = result.get("items", [])
        total = result.get("total", len(items))
    elif hasattr(result, "items"):
        items = getattr(result, "items")
        total = getattr(result, "total", len(items))
    elif isinstance(result, (list, tuple)):
        items = list(result)
        total = len(items)
    else:
        try:
            d = getattr(result, "__dict__", {})
            items = d.get("items", [])
            total = d.get("total", len(items))
        except Exception:
            items = []
            total = 0

    # 路由层数量截断
    items = items[:limit]

    # 构造 JSON item
    json_items: List[Dict[str, Any]] = []
    for em in items:
        subject = (getattr(em, "subject", "") or "").strip()
        sender = (getattr(em, "sender", "") or "").strip()
        received_dt = getattr(em, "received_time", None)
        received = received_dt.strftime("%Y-%m-%d %H:%M") if received_dt else ""
        content = (
            (getattr(em, "summary", None) or "")
            or (getattr(em, "snippet", None) or "")
            or (getattr(em, "body_text", None) or "")
        ).strip()[:160]

        json_items.append({
            "id": getattr(em, "id", None),
            "subject": subject,
            "sender": sender,
            "received_time": received,
            "summary": content,
        })

    return {"total": total, "items": json_items}
