import json
from datetime import datetime
from typing import Optional, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session

from crud import email as email_crud
from model import schemas
from model.entities import EmailParsed, EmailRaw


def _decode_mime_content(raw: EmailRaw) -> str:
    encoding = raw.encoding or "utf-8"
    try:
        return raw.mime_content.decode(encoding)
    except (LookupError, UnicodeDecodeError):
        # Fallback keeps every byte even if declared charset is missing/wrong
        return raw.mime_content.decode("latin-1", errors="replace")


def _load_attachment_meta(raw: Optional[str]) -> list[schemas.EmailAttachmentMeta]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    metas: list[schemas.EmailAttachmentMeta] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                name = str(item.get("name") or "attachment")
                size_val = item.get("size")
                try:
                    size = int(size_val) if size_val is not None else 0
                except (TypeError, ValueError):
                    size = 0
                content_type = item.get("content_type")
                metas.append(
                    schemas.EmailAttachmentMeta(
                        name=name,
                        size=size,
                        content_type=str(content_type) if content_type else None,
                    )
                )
            elif isinstance(item, str):
                metas.append(schemas.EmailAttachmentMeta(name=item, size=0, content_type=None))
    return metas


def _build_list_item(email_obj: EmailParsed, view: email_crud.EmailView) -> schemas.EmailListItem:
    attachments = _load_attachment_meta(cast(Optional[str], email_obj.attachments))
    subject = cast(str, email_obj.subject)
    sender = cast(str, email_obj.sender)
    received_time = cast(datetime, email_obj.received_time)

    snippet_source: str
    if view == "raw" and email_obj.raw:
        snippet_source = _decode_mime_content(email_obj.raw)
    else:
        snippet_source = cast(Optional[str], email_obj.body_text) or ""
    snippet = " ".join(snippet_source.split())
    if len(snippet) > 160:
        snippet = snippet[:157] + "..."

    return schemas.EmailListItem(
        id=cast(int, email_obj.id),
        raw_id=cast(Optional[int], getattr(email_obj, "raw_id", None)),
        subject=subject,
        sender=sender,
        received_time=received_time,
        snippet=snippet,
        summary=None if view == "raw" else cast(Optional[str], email_obj.summary),
        has_attachments=bool(attachments),
    )


def list_emails(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    view: email_crud.EmailView = "parsed",
) -> schemas.EmailListResponse:
    emails, total = email_crud.list_emails(
        db,
        user_id,
        skip=skip,
        limit=limit,
        search=search,
        view=view,
    )

    items = [_build_list_item(email, view) for email in emails]
    return schemas.EmailListResponse(total=total, items=items)


def list_all_emails_for_user(
    db: Session,
    user_id: int,
    view: email_crud.EmailView = "parsed",
) -> schemas.EmailListResponse:
    emails = email_crud.get_email_by_sid(db, user_id=user_id, view=view)
    items = [_build_list_item(email, view) for email in emails]
    return schemas.EmailListResponse(total=len(items), items=items)


def get_email_detail(
    db: Session,
    user_id: int,
    email_id: int,
    view: email_crud.EmailView = "parsed",
) -> schemas.EmailDetail:
    email_obj = email_crud.get_email_with_raw(db, user_id, email_id)
    if not email_obj:
        raise HTTPException(status_code=404, detail="邮件不存在或无访问权限")

    attachments = _load_attachment_meta(cast(Optional[str], email_obj.attachments))
    subject = cast(str, email_obj.subject)
    sender = cast(str, email_obj.sender)
    received_time = cast(datetime, email_obj.received_time)
    raw = email_obj.raw

    body_text = cast(Optional[str], email_obj.body_text)
    body_html = cast(Optional[str], email_obj.body_html)
    summary = cast(Optional[str], email_obj.summary)
    mime_content: Optional[str] = None

    if view == "raw":
        if not raw:
            raise HTTPException(status_code=404, detail="邮件原始内容不存在")
        mime_content = _decode_mime_content(raw)
        body_text = None
        body_html = None
        summary = None

    return schemas.EmailDetail(
        id=cast(int, email_obj.id),
        raw_id=cast(Optional[int], raw.id) if raw else None,
        subject=subject,
        sender=sender,
        received_time=received_time,
        body_text=body_text,
        body_html=body_html,
        attachments=attachments,
        summary=summary,
        message_id=cast(Optional[str], raw.message_id if raw else None),
        encoding=cast(Optional[str], raw.encoding if raw else None),
        stored_time=cast(Optional[datetime], raw.stored_time if raw else None),
        mime_content=mime_content,
    )


def list_blackboard_emails_for_user(
    db: Session,
    user_id: int,
    view: email_crud.EmailView = "parsed",
) -> schemas.EmailListResponse:
    """获取由 Blackboard 发送的全部邮件，并封装为列表响应。"""
    emails = email_crud.get_blackboard_emails(db, user_id=user_id, view=view)
    items = [_build_list_item(email, view) for email in emails]
    return schemas.EmailListResponse(total=len(items), items=items)
