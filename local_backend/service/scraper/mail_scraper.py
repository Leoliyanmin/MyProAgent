import imaplib
from email import message_from_bytes
from email.header import decode_header
from email.utils import parsedate_to_datetime
from email.message import Message
import os
import ssl
import traceback
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
import json
import re

logger = logging.getLogger(__name__)

IMAP_SERVER = "imap.exmail.qq.com"
IMAP_PORT = 993

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'mail_result.txt')


def write_mail_result(payload: Dict[str, Any]) -> None:
    try:
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total = payload.get("total", 0)
        returned = payload.get("returned", 0)
        messages = payload.get("messages", [])

        lines = [
            "=" * 40,
            "邮件爬取结果",
            "=" * 40,
            f"时间: {current_time}",
            f"邮件总数: {total}",
            f"本次获取: {returned}",
            "",
            "=" * 40,
            "邮件详情列表",
            "=" * 40,
        ]
        for i, msg in enumerate(messages, 1):
            body = msg.get('body', '')
            lines.extend([
                f"--- 邮件 {i} ---",
                f"邮件ID: {msg.get('mail_id', '')}",
                f"发件人: {msg.get('sender', '')}",
                f"主题: {msg.get('subject', '')}",
                f"时间: {msg.get('time', '')}",
                f"正文:",
                body,
                "",
            ])
        lines.append("=" * 40)
        lines.append("完整原始数据(JSON)")
        lines.append("=" * 40)
        lines.append(json.dumps(payload, ensure_ascii=False, indent=2))

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        logger.info(f"邮件爬取结果已保存到: {OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"写入邮件结果文件失败: {e}")


def _decode_mime_header(header_value: Optional[str]) -> str:
    if not header_value:
        return ""
    decoded_parts = decode_header(header_value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            try:
                result.append(part.decode(charset or "utf-8", errors="replace"))
            except (LookupError, UnicodeDecodeError):
                result.append(part.decode("utf-8", errors="replace"))
        else:
            result.append(str(part))
    return " ".join(result).strip()


def _extract_email_body(msg: Message, max_size: int = 10240) -> str:
    body = _extract_raw_html(msg)
    cleaned = re.sub(r"<[^>]+>", "", body)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > max_size:
        cleaned = cleaned[:max_size] + "...(truncated)"
    return cleaned


def _extract_raw_html(msg: Message, max_size: int = 10240) -> str:
    raw = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in content_disposition:
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            try:
                decoded = payload.decode(charset, errors="replace")
            except (LookupError, UnicodeDecodeError):
                decoded = payload.decode("utf-8", errors="replace")
            if content_type == "text/html":
                raw = decoded
                break
            elif content_type == "text/plain" and not raw:
                raw = decoded
        if not raw:
            for part in msg.walk():
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                charset = part.get_content_charset() or "utf-8"
                try:
                    decoded = payload.decode(charset, errors="replace")
                except (LookupError, UnicodeDecodeError):
                    decoded = payload.decode("utf-8", errors="replace")
                if part.get_content_type() == "text/html":
                    raw = decoded
                    break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            try:
                raw = payload.decode(charset, errors="replace")
            except (LookupError, UnicodeDecodeError):
                raw = payload.decode("utf-8", errors="replace")
    if len(raw) > max_size:
        raw = raw[:max_size] + "...(truncated)"
    return raw


def _parse_email_date(date_str: Optional[str]) -> str:
    if not date_str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return date_str


class MailScraper:
    def __init__(self, email_address: str, app_password: str):
        self.email_address = email_address
        self.app_password = app_password
        self._conn: Optional[imaplib.IMAP4_SSL] = None

    def _connect(self) -> imaplib.IMAP4_SSL:
        if self._conn is not None:
            try:
                self._conn.noop()
                return self._conn
            except (imaplib.IMAP4.error, OSError):
                self._conn = None
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = True
            ctx.verify_mode = ssl.CERT_REQUIRED
            conn = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT, ssl_context=ctx)
            conn.login(self.email_address, self.app_password)
            self._conn = conn
            return conn
        except imaplib.IMAP4.error as e:
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "login" in error_msg.lower() or "auth" in error_msg.lower():
                raise ConnectionError(f"IMAP认证失败，请检查邮箱地址和客户端专用密码是否正确: {error_msg}")
            raise ConnectionError(f"IMAP服务器拒绝连接: {error_msg}")
        except OSError as e:
            raise ConnectionError(f"无法连接到IMAP服务器 {IMAP_SERVER}:{IMAP_PORT}，请检查网络连接: {e}")
        except ssl.SSLError as e:
            raise ConnectionError(f"IMAP SSL/TLS连接失败: {e}")

    def disconnect(self):
        if self._conn is not None:
            try:
                self._conn.logout()
            except Exception:
                pass
            self._conn = None

    def test_connection(self) -> bool:
        try:
            conn = self._connect()
            status, _ = conn.list()
            return status == "OK"
        except Exception as e:
            logger.error(f"IMAP连接测试失败:\n{traceback.format_exc()}")
            raise

    def scrape_mail_meta(self, max_messages: int = 50, folder: str = "INBOX") -> Dict[str, Any]:
        conn = self._connect()
        status, _ = conn.select(folder, readonly=True)
        if status != "OK":
            raise RuntimeError(f"Failed to select folder: {folder}")

        _, search_data = conn.uid('search', None, "ALL")
        message_ids = search_data[0].split() if search_data[0] else []
        total = len(message_ids)
        logger.info(f"Total messages in {folder}: {total}")

        if max_messages and max_messages > 0:
            message_ids = message_ids[-max_messages:]

        messages = []
        for msg_id in message_ids:
            _, msg_data = conn.uid('fetch', msg_id, "(FLAGS BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
            raw_header = msg_data[0][1] if msg_data and len(msg_data[0]) > 1 else b""
            msg = message_from_bytes(raw_header)
            sender = _decode_mime_header(msg.get("From", ""))
            subject = _decode_mime_header(msg.get("Subject", ""))
            date_str = _parse_email_date(msg.get("Date", ""))
            messages.append({
                "mail_id": msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id),
                "subject": subject,
                "sender": sender,
                "time": date_str,
            })

        conn.close()
        return {
            "total": total,
            "returned": len(messages),
            "messages": messages,
        }

    def scrape_mail_detail(self, max_messages: int = 50, folder: str = "INBOX") -> Dict[str, Any]:
        conn = self._connect()
        status, _ = conn.select(folder, readonly=True)
        if status != "OK":
            raise RuntimeError(f"Failed to select folder: {folder}")

        _, search_data = conn.uid('search', None, "ALL")
        message_ids = search_data[0].split() if search_data[0] else []
        total = len(message_ids)

        if max_messages and max_messages > 0:
            message_ids = message_ids[-max_messages:]

        messages = []
        for msg_id in message_ids:
            _, msg_data = conn.uid('fetch', msg_id, "(FLAGS BODY.PEEK[])")
            raw_email = msg_data[0][1] if msg_data and len(msg_data[0]) > 1 else b""
            msg = message_from_bytes(raw_email)
            sender = _decode_mime_header(msg.get("From", ""))
            subject = _decode_mime_header(msg.get("Subject", ""))
            date_str = _parse_email_date(msg.get("Date", ""))
            body = _extract_email_body(msg)
            raw_html = _extract_raw_html(msg)
            messages.append({
                "mail_id": msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id),
                "subject": subject,
                "sender": sender,
                "time": date_str,
                "body": body,
                "raw_html": raw_html,
            })

        conn.close()
        return {
            "total": total,
            "returned": len(messages),
            "messages": messages,
        }

    def scrape_recent_mails(self, days: int = 7, folder: str = "INBOX") -> Dict[str, Any]:
        conn = self._connect()
        status, _ = conn.select(folder, readonly=True)
        if status != "OK":
            raise RuntimeError(f"Failed to select folder: {folder}")

        since_date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
        _, search_data = conn.uid('search', None, f"SINCE {since_date}")
        message_ids = search_data[0].split() if search_data[0] else []

        messages = []
        for msg_id in message_ids:
            _, msg_data = conn.uid('fetch', msg_id, "(FLAGS BODY.PEEK[])")
            raw_email = msg_data[0][1] if msg_data and len(msg_data[0]) > 1 else b""
            msg = message_from_bytes(raw_email)
            sender = _decode_mime_header(msg.get("From", ""))
            subject = _decode_mime_header(msg.get("Subject", ""))
            date_str = _parse_email_date(msg.get("Date", ""))
            body = _extract_email_body(msg)
            raw_html = _extract_raw_html(msg)
            messages.append({
                "mail_id": msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id),
                "subject": subject,
                "sender": sender,
                "time": date_str,
                "body": body,
                "raw_html": raw_html,
            })

        conn.close()
        return {
            "total": len(messages),
            "returned": len(messages),
            "messages": messages,
        }
