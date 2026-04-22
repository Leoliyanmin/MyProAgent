"""Simple SMTP 邮件发送服务。"""

import logging
import smtplib
from base64 import b64decode
from email.message import EmailMessage
from typing import Iterable, List, Optional


logger = logging.getLogger(__name__)


class EmailAttachmentPayload:
    """轻量级附件载体，用于在 service 层统一处理。"""

    def __init__(self, filename: str, content: str, content_type: str = "application/octet-stream"):
        self.filename = filename
        self.content = content
        self.content_type = content_type


class SMTPMailService:
    """封装 SMTP 发送逻辑，支持明文/HTML、抄送、密送与附件。"""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 465,
        use_ssl: bool = True,
    ) -> None:
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.use_ssl = use_ssl

    def _build_message(
        self,
        subject: str,
        sender: str,
        to: Iterable[str],
        cc: Optional[Iterable[str]] = None,
        bcc: Optional[Iterable[str]] = None,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        attachments: Optional[List[EmailAttachmentPayload]] = None,
    ) -> tuple[EmailMessage, List[str]]:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = sender
        to_list = list(to)
        if not to_list:
            raise ValueError("收件人列表不能为空")
        msg["To"] = ", ".join(to_list)

        all_recipients: List[str] = list(to_list)

        if cc:
            cc_list = [addr for addr in cc if addr]
            if cc_list:
                msg["Cc"] = ", ".join(cc_list)
                all_recipients.extend(cc_list)

        if bcc:
            bcc_list = [addr for addr in bcc if addr]
            all_recipients.extend(bcc_list)

        if body_text:
            msg.set_content(body_text)
        else:
            msg.set_content("此邮件没有纯文本正文。")

        if body_html:
            msg.add_alternative(body_html, subtype="html")

        for attachment in attachments or []:
            try:
                data = b64decode(attachment.content)
            except Exception as exc:  # pragma: no cover - base64 解码失败时记录日志
                logger.warning("Base64 解码附件失败: %s", exc)
                raise ValueError("附件内容不是有效的 Base64 编码") from exc

            maintype, _, subtype = attachment.content_type.partition("/")
            maintype = maintype or "application"
            subtype = subtype or "octet-stream"
            msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=attachment.filename)

        return msg, all_recipients

    def send_email(
        self,
        subject: str,
        sender: Optional[str],
        to: Iterable[str],
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        cc: Optional[Iterable[str]] = None,
        bcc: Optional[Iterable[str]] = None,
        attachments: Optional[List[EmailAttachmentPayload]] = None,
    ) -> None:
        message_sender = sender or self.username
        if not message_sender:
            raise ValueError("发件人地址不能为空")

        message, recipients = self._build_message(
            subject=subject,
            sender=message_sender,
            to=to,
            cc=cc,
            bcc=bcc,
            body_text=body_text,
            body_html=body_html,
            attachments=attachments,
        )

        logger.info("准备向 %d 个收件人发送邮件", len(recipients))

        if self.use_ssl:
            smtp_client = smtplib.SMTP_SSL(self.host, self.port)
        else:
            smtp_client = smtplib.SMTP(self.host, self.port)
            smtp_client.ehlo()
            if smtp_client.has_extn("starttls"):
                smtp_client.starttls()

        try:
            smtp_client.login(self.username, self.password)
        except smtplib.SMTPNotSupportedError:
            logger.info("SMTP AUTH not supported by server, skipping login.")

        try:
            smtp_client.send_message(message, from_addr=message_sender, to_addrs=recipients)
            logger.info("邮件发送成功")
        finally:
            smtp_client.quit()
