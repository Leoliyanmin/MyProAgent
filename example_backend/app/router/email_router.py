import base64
from typing import Literal, Optional, cast, Tuple

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, BackgroundTasks, Request
from sqlalchemy.orm import Session

from core import email_crypto
from core.database import get_db, get_db_sync
from crud import email as email_crud
from model import schemas
from model.entities import EmailAccount
from service.email import email_query_service
from service.email.email_logging_service import EmailService
from service.email.email_sync_service import sync_mailbox
from service.email.email_send_service import EmailAttachmentPayload, SMTPMailService

from service.email.email_time_update import start_email_scheduler, stop_email_scheduler

from model.entities import EmailAccount
from service import ai_service
from crud import important_email

router = APIRouter(prefix="/emails", tags=["emails"])


@router.get("/public-key")
async def fetch_public_key():
    """返回加密邮箱密码所需的 RSA 公钥。"""

    return {"public_key": email_crypto.get_public_key_pem()}


DEFAULT_SMTP_SSL_PORT = 465
DEFAULT_SMTP_TLS_PORT = 587

SMTP_HOST_OVERRIDES: dict[str, Tuple[str, int, bool]] = {
    "imap.qq.com": ("smtp.qq.com", DEFAULT_SMTP_SSL_PORT, True),
    "imap.exmail.qq.com": ("smtp.exmail.qq.com", DEFAULT_SMTP_SSL_PORT, True),
    "imap.gmail.com": ("smtp.gmail.com", DEFAULT_SMTP_SSL_PORT, True),
    "imap.mail.yahoo.com": ("smtp.mail.yahoo.com", DEFAULT_SMTP_SSL_PORT, True),
    "imap.163.com": ("smtp.163.com", DEFAULT_SMTP_SSL_PORT, True),
    "imap.126.com": ("smtp.126.com", DEFAULT_SMTP_SSL_PORT, True),
    "imap-mail.outlook.com": ("smtp-mail.outlook.com", DEFAULT_SMTP_TLS_PORT, True),
    "outlook.office365.com": ("smtp.office365.com", DEFAULT_SMTP_TLS_PORT, False),
}


def _resolve_smtp_settings(account: EmailAccount) -> tuple[str, int, bool]:
    """把存储的 IMAP host 转换为 SMTP 设置，兼容常见邮箱服务。"""

    host_value = (account.host or "").strip()
    if not host_value:
        raise HTTPException(status_code=400, detail="邮箱凭据缺少 host 配置，请重新登录邮箱")

    normalized = host_value.lower()
    port_value = cast(int, account.port)
    use_ssl_value = cast(bool, account.use_ssl)

    # 若用户手动保存了非 IMAP 端口，则认为已经是 SMTP 设置，直接返回
    if port_value not in (993, 143):
        return host_value, port_value, use_ssl_value

    override = SMTP_HOST_OVERRIDES.get(normalized)
    if override:
        return override

    candidate = host_value

    prefix_rules = (
        ("imap-mail.", "smtp-mail."),
        ("imap.", "smtp."),
    )

    for prefix, replacement in prefix_rules:
        prefix_lower = prefix
        if normalized.startswith(prefix_lower):
            candidate = replacement + host_value[len(prefix):]
            break
    else:
        marker = ".imap."
        if marker in normalized:
            idx = normalized.index(marker)
            candidate = host_value[:idx] + ".smtp." + host_value[idx + len(marker):]

    default_port = DEFAULT_SMTP_SSL_PORT if use_ssl_value else DEFAULT_SMTP_TLS_PORT
    return candidate, default_port, use_ssl_value


@router.get("/", response_model=schemas.EmailListResponse)
async def list_emails(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(default=None, max_length=100),
    view: Literal["parsed", "raw"] = Query("parsed"),
    db: Session = Depends(get_db),
    user_id: int = Query(..., ge=1),
):
    """获取当前用户的邮件列表（支持分页与关键字搜索）。"""
    return email_query_service.list_emails(
        db=db,
        user_id=user_id,
        skip=skip,
        limit=limit,
        search=search,
        view=view,
    )


@router.get("/get_emails_by_sid", response_model=schemas.EmailListResponse)
async def list_all_emails_by_sid(
    user_id: int = Query(..., ge=1),
    view: Literal["parsed", "raw"] = Query("parsed"),
    db: Session = Depends(get_db),
):
    """测试入口：返回指定用户的全部邮件，用于后台排查。"""
    return email_query_service.list_all_emails_for_user(
        db=db,
        user_id=user_id,
        view=view,
    )


@router.get("/{email_id}", response_model=schemas.EmailDetail)
async def get_email_detail(
    email_id: int,
    view: Literal["parsed", "raw"] = Query("parsed"),
    db: Session = Depends(get_db),
    user_id: int = Query(..., ge=1),
):
    """获取指定邮件的详细内容。"""
    return email_query_service.get_email_detail(
        db=db,
        user_id=user_id,
        email_id=email_id,
        view=view,
    )


@router.post("/login", response_model=schemas.EmailLoginResponse)
async def login_mailbox(payload: schemas.EmailLoginRequest, db: Session = Depends(get_db)):
    """测试指定 IMAP 邮箱账号是否可以成功连接，如果成功，则加入数据库，后续可以在本地使用加密。"""
    try:
        plain_password = email_crypto.resolve_login_password(
            encrypted_password=payload.encrypted_password,
            plaintext_password=payload.password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    service = EmailService(
        host=payload.host,
        username=payload.email,
        password=plain_password,
        port=payload.port,
        use_ssl=payload.use_ssl,
    )

    try:
        service.connect()
        email_crud.upsert_email_account(
            db,
            user_id=payload.user_id,
            email=payload.email,
            password=email_crypto.encrypt_password_for_storage(plain_password),
            host=payload.host,
            port=payload.port,
            use_ssl=payload.use_ssl,
        )
        # ★ 启动调度器（每 1 分钟一次，可以改）
        start_email_scheduler(interval_minutes=10, limit=6)

        try:
            fetched, stored, skipped = sync_mailbox(
                db,
                user_id=payload.user_id,
                host=payload.host,
                username=payload.email,
                password=plain_password,
                port=payload.port,
                folder="INBOX",
                limit=5,
                use_ssl=payload.use_ssl,
            )
            message = f"邮箱连接成功，已同步 {stored}/{fetched} 封"
        except Exception as sync_exc:
            raise HTTPException(status_code=400, detail=f"邮箱连接成功但同步失败: {sync_exc}")
        return schemas.EmailLoginResponse(success=True, message=message)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"邮箱连接失败: {exc}")
    finally:
        service.close_connection()


@router.post("/logout", response_model=schemas.EmailLogoutResponse)
async def logout_mailbox(user_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    """删除指定用户的邮箱账号与历史邮件。"""
    important_deleted = important_email.clear_important_emails(db, user_id, commit=False)
    parsed_deleted, raw_deleted, account_deleted = email_crud.delete_email_account_with_data(db, user_id)
    if not (parsed_deleted or raw_deleted or account_deleted):
        raise HTTPException(status_code=404, detail="未找到对应的邮箱数据，无需登出")

    total_msg = (
        f"已删除账号 {account_deleted} 条，原始邮件 {raw_deleted} 条，解析邮件 {parsed_deleted} 条，重要邮件 {important_deleted} 条"
    )

    #//检查传入的 user_id 是否仍有邮箱账号
    remaining = db.query(EmailAccount).filter(EmailAccount.user_id == user_id).count()
    if remaining == 0:
        stop_email_scheduler()

    return schemas.EmailLogoutResponse(
        success=True,
        deleted_parsed=parsed_deleted,
        deleted_raw=raw_deleted,
        deleted_accounts=account_deleted,
        deleted_important=important_deleted,
        message=total_msg,
    )


@router.post("/send", response_model=schemas.EmailSendResponse)
async def send_email(
    payload: schemas.EmailSendRequest,
    user_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):
    """使用 SMTP 发送邮件，需要用户已完成登录绑定。"""

    account = email_crud.get_email_account(db, user_id)
    if not account:
        raise HTTPException(status_code=404, detail="未找到邮箱凭据，请先调用 /emails/login")

    username_str = cast(str, account.email)
    try:
        password_str = email_crypto.decrypt_stored_password(cast(str, account.password))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    smtp_host, smtp_port, smtp_use_ssl = _resolve_smtp_settings(account)

    service = SMTPMailService(
        host=smtp_host,
        username=username_str,
        password=password_str,
        port=smtp_port,
        use_ssl=smtp_use_ssl,
    )

    attachments = None
    if payload.attachments:
        attachments = [
            EmailAttachmentPayload(
                filename=item.filename,
                content=item.content,
                content_type=item.content_type,
            )
            for item in payload.attachments
        ]

    try:
        service.send_email(
            subject=payload.subject,
            sender=username_str,
            to=payload.to,
            body_text=payload.body_text,
            body_html=payload.body_html,
            cc=payload.cc,
            bcc=payload.bcc,
            attachments=attachments,
        )
        return schemas.EmailSendResponse(success=True, message="邮件发送成功")
    except Exception as exc:  # pragma: no cover - SMTP 登录或发送失败直接提示
        raise HTTPException(status_code=400, detail=f"邮件发送失败: {exc}")


MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/sync", response_model=schemas.EmailSyncResponse)
async def sync_mailbox_endpoint(
    payload: schemas.EmailLoginRequest,
    folder: str = Query("INBOX", min_length=1),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    user_id: int = Query(..., ge=1),
):
    """拉取邮箱内的邮件并保存到数据库，跳过已存在的记录。"""
    if payload.user_id != user_id:
        raise HTTPException(status_code=400, detail="payload.user_id 与 query user_id 不一致")

    try:
        plain_password = email_crypto.resolve_login_password(
            encrypted_password=payload.encrypted_password,
            plaintext_password=payload.password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    email_crud.upsert_email_account(
        db,
        user_id=user_id,
        email=payload.email,
        password=email_crypto.encrypt_password_for_storage(plain_password),
        host=payload.host,
        port=payload.port,
        use_ssl=payload.use_ssl,
    )

    try:
        fetched, stored, skipped = sync_mailbox(
            db,
            user_id=user_id,
            host=payload.host,
            username=payload.email,
            password=plain_password,
            port=payload.port,
            folder=folder,
            limit=limit,
            use_ssl=payload.use_ssl,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"邮件同步失败: {exc}")

    return schemas.EmailSyncResponse(fetched=fetched, stored=stored, skipped=skipped)


@router.post("/auto-sync", response_model=schemas.EmailSyncResponse)
async def auto_sync_mailbox(
    user_id: int = Query(..., ge=1),
    folder: str = Query("INBOX", min_length=1),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """使用持久化凭据自动同步邮箱。"""
    account = email_crud.get_email_account(db, user_id)
    if not account:
        raise HTTPException(status_code=404, detail="未找到邮箱凭据，请先调用 /emails/login")

    try:
        decrypted_password = email_crypto.decrypt_stored_password(cast(str, account.password))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        fetched, stored, skipped = sync_mailbox(
            db,
            user_id=user_id,
            host=cast(str, account.host),
            username=cast(str, account.email),
            password=decrypted_password,
            port=cast(int, account.port),
            folder=folder,
            limit=limit,
            use_ssl=cast(bool, account.use_ssl),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"邮件同步失败: {exc}")

    return schemas.EmailSyncResponse(fetched=fetched, stored=stored, skipped=skipped)


@router.post("/attachments/upload", response_model=schemas.EmailAttachmentUploadResponse)
async def upload_attachment(
    file: UploadFile = File(...),
):
    """上传附件并返回 Base64 编码结果，便于发送邮件时复用。"""
    content = await file.read()
    size = len(content)
    if size == 0:
        raise HTTPException(status_code=400, detail="附件文件为空")
    if size > MAX_ATTACHMENT_SIZE:
        raise HTTPException(status_code=400, detail="附件超过 10MB 限制")

    encoded = base64.b64encode(content).decode("ascii")
    return schemas.EmailAttachmentUploadResponse(
        filename=file.filename or "attachment",
        content_type=file.content_type or "application/octet-stream",
        size=size,
        content=encoded,
    )


# Webhook: 外部邮件/网关在检测到新邮件时调用此接口以实现即时入库
@router.post("/webhook")
async def email_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    接收外部系统（邮件网关或 BB/TIS 登录后触发）的推送，payload 可包含：
    {
      "user_id": 1,
      "host": "imap.xxx",
      "username": "xx",
      "password": "xx",
      "folder": "INBOX"
    }
    我们在后台触发 sync_mailbox（不会阻塞请求）。
    """
    payload = await request.json()
    user_id = payload.get("user_id")
    host = payload.get("host")
    username = payload.get("username")
    password = payload.get("password")
    port = payload.get("port", 993)
    folder = payload.get("folder", "INBOX")
    use_ssl = payload.get("use_ssl", True)
    limit = payload.get("limit", 200)

    if user_id is None:
        return {"error": "user_id 必填"}, 400

    # 后台任务：调用现有 sync_mailbox（同步并入库）
    def _bg_sync():
        db = get_db_sync()
        try:
            sync_mailbox(
                db,
                user_id=user_id,
                host=host,
                username=username,
                password=password,
                port=port,
                folder=folder,
                limit=limit,
                use_ssl=use_ssl,
            )
        finally:
            db.close()

    background_tasks.add_task(_bg_sync)
    return {"status": "ok", "message": "sync triggered"}

@router.post("/important/generate", response_model=list[schemas.ImportantEmailResponse])
async def generate_important_emails(
    user_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):
    """
    调用AI从最近邮件中筛选3条重要邮件并保存。
    """
    # 1. 调用 AI 服务筛选并保存
    ai_service.select_important_emails(user_id, db)
    
    # 2. 获取保存的结果并返回
    important_emails = important_email.get_important_emails(db, user_id)
    
    # 构造返回结果
    results = []
    for ie in important_emails:
        # 确保 email_parsed 已经加载
        if ie.email_parsed:
            results.append({
                "id": ie.id,
                "email_id": ie.email_parsed_id,
                "subject": ie.email_parsed.subject,
                "sender": ie.email_parsed.sender,
                "summary": ie.email_parsed.summary,
                "reason": ie.reason,
                "received_time": ie.email_parsed.received_time
            })
    
    return results
