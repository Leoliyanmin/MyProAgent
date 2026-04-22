import json
from datetime import datetime
from typing import List, Literal, Optional, Sequence, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from model.entities import EmailAccount, EmailParsed, EmailRaw

EmailView = Literal["parsed", "raw"]


def list_emails(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    view: EmailView = "parsed",
) -> Tuple[List[EmailParsed], int]:
    query = db.query(EmailParsed).filter(EmailParsed.user_id == user_id)

    if view == "raw":
        query = query.options(joinedload(EmailParsed.raw))

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                EmailParsed.subject.ilike(pattern),
                EmailParsed.sender.ilike(pattern),
                EmailParsed.body_text.ilike(pattern),
                EmailParsed.body_html.ilike(pattern),
                EmailParsed.summary.ilike(pattern),
            )
        )

    total = query.count()

    emails = (
        query.order_by(EmailParsed.received_time.desc(), EmailParsed.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return emails, total


def get_email_by_sid(
    db: Session,
    user_id: int,
    view: EmailView = "parsed",
) -> List[EmailParsed]:
    query = db.query(EmailParsed).filter(EmailParsed.user_id == user_id)
    if view == "raw":
        query = query.options(joinedload(EmailParsed.raw))
    return query.order_by(EmailParsed.received_time.desc(), EmailParsed.id.desc()).all()


def get_email_with_raw(
    db: Session,
    user_id: int,
    email_id: int,
) -> Optional[EmailParsed]:
    return (
        db.query(EmailParsed)
        .options(joinedload(EmailParsed.raw))
        .filter(EmailParsed.user_id == user_id, EmailParsed.id == email_id)
        .first()
    )

def get_blackboard_emails(
    db: Session,
    user_id: int,
    view: EmailView = "parsed",
) -> List[EmailParsed]:
    """获取由 Blackboard 发送的所有邮件。

    通过匹配发件人字段中包含 "blackboard" 的记录进行筛选。
    如需扩展，可在此处加入更多域名/关键字匹配规则。
    """
    query = (
        db.query(EmailParsed)
        .filter(
            EmailParsed.user_id == user_id,
            EmailParsed.sender.ilike("%blackboard%"),
        )
    )

    if view == "raw":
        query = query.options(joinedload(EmailParsed.raw))

    return query.order_by(EmailParsed.received_time.desc(), EmailParsed.id.desc()).all()


def _email_exists(
    db: Session,
    user_id: int,
    *,
    message_id: Optional[str],
    subject: str,
    sender: str,
    received_time,
) -> bool:
    if message_id:
        return db.query(EmailRaw.id).filter(EmailRaw.message_id == message_id).first() is not None

    return (
        db.query(EmailParsed.id)
        .filter(
            EmailParsed.user_id == user_id,
            EmailParsed.subject == subject,
            EmailParsed.sender == sender,
            EmailParsed.received_time == received_time,
        )
        .first()
        is not None
    )


def bulk_upsert_emails(
    db: Session,
    user_id: int,
    emails: Sequence[dict],
) -> Tuple[int, int]:
    created = 0
    skipped = 0

    for email_data in emails:
        parsed_block = email_data.get("parsed", {})
        subject = parsed_block.get("subject") or "No subject"
        sender = parsed_block.get("sender") or ""
        body_text = parsed_block.get("body_text")
        body_html = parsed_block.get("body_html")
        summary = parsed_block.get("summary")
        attachments_meta = parsed_block.get("attachments_meta") or []

        received_time = email_data.get("received_at") or datetime.utcnow()
        message_id = email_data.get("message_id")
        raw_bytes = email_data.get("raw_content")
        encoding = email_data.get("encoding")

        if raw_bytes is None:
            continue

        if _email_exists(
            db,
            user_id,
            message_id=message_id,
            subject=subject,
            sender=sender,
            received_time=received_time,
        ):
            skipped += 1
            continue

        raw_entry = EmailRaw(
            user_id=user_id,
            message_id=message_id,
            mime_content=raw_bytes,
            encoding=encoding,
        )
        db.add(raw_entry)
        db.flush()

        attachments_json = json.dumps(attachments_meta, ensure_ascii=False) if attachments_meta else None

        parsed_entry = EmailParsed(
            raw_id=raw_entry.id,
            user_id=user_id,
            subject=subject,
            sender=sender,
            body_text=body_text,
            body_html=body_html,
            attachments=attachments_json,
            summary=summary,
            received_time=received_time,
        )
        db.add(parsed_entry)

        created += 1

    if created:
        db.commit()

    return created, skipped


def upsert_email_account(
    db: Session,
    *,
    user_id: int,
    email: str,
    password: str,
    host: str,
    port: int,
    use_ssl: bool,
) -> EmailAccount:
    account = db.query(EmailAccount).filter(EmailAccount.user_id == user_id).first()
    if account:
        setattr(account, "email", email)
        setattr(account, "password", password)
        setattr(account, "host", host)
        setattr(account, "port", port)
        setattr(account, "use_ssl", use_ssl)
    else:
        account = EmailAccount(
            user_id=user_id,
            email=email,
            password=password,
            host=host,
            port=port,
            use_ssl=use_ssl,
        )
        db.add(account)

    db.commit()
    db.refresh(account)
    return account


def get_email_account(db: Session, user_id: int) -> Optional[EmailAccount]:
    return db.query(EmailAccount).filter(EmailAccount.user_id == user_id).first()


def delete_email_account_with_data(db: Session, user_id: int) -> Tuple[int, int, int]:
    parsed_deleted = (
        db.query(EmailParsed)
        .filter(EmailParsed.user_id == user_id)
        .delete(synchronize_session=False)
    )
    raw_deleted = (
        db.query(EmailRaw)
        .filter(EmailRaw.user_id == user_id)
        .delete(synchronize_session=False)
    )
    account_deleted = (
        db.query(EmailAccount)
        .filter(EmailAccount.user_id == user_id)
        .delete(synchronize_session=False)
    )

    if parsed_deleted or raw_deleted or account_deleted:
        db.commit()
    else:
        db.rollback()

    return parsed_deleted, raw_deleted, account_deleted
