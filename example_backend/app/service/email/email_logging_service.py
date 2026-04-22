import base64
import imaplib
import email
from email.header import decode_header
from email.message import Message
from email.utils import parseaddr, parsedate_to_datetime
import logging
from datetime import datetime, timezone
from typing import Optional

from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _decode_mime_words(value: Optional[str]) -> str:
    if not value:
        return ""
    decoded_fragments = []
    for text, encoding in decode_header(value):
        if isinstance(text, bytes):
            decoded_fragments.append(_decode_bytes(text, encoding))
        else:
            decoded_fragments.append(text)
    return "".join(decoded_fragments)


def _decode_bytes(data: bytes, encoding: Optional[str]) -> str:
    candidates = [encoding, "utf-8", "gb18030", "latin1", "windows-1252"]
    for enc in candidates:
        if not enc:
            continue
        try:
            return data.decode(enc)
        except Exception:
            continue
    return data.decode("latin1", errors="replace")


def _decode_part_payload(part: Message) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload

    charset = part.get_content_charset()
    if not charset:
        charset_obj = part.get_charset()
        if charset_obj is not None:
            charset = (
                getattr(charset_obj, "input_charset", None)
                or getattr(charset_obj, "output_charset", None)
                or str(charset_obj)
            )
    return _decode_bytes(bytes(payload), charset or "utf-8")


def _extract_html(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    target = soup.body or soup
    text = target.get_text("\n", strip=True)
    cleaned_html = str(target)
    return cleaned_html, text


class EmailService:
    def __init__(self, host: str, username: str, password: str, port: int = 993, use_ssl: bool = True):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.use_ssl = use_ssl
        self.connection: Optional[imaplib.IMAP4] = None

    def connect(self):
        try:
            if self.use_ssl:
                self.connection = imaplib.IMAP4_SSL(self.host, self.port)
            else:
                self.connection = imaplib.IMAP4(self.host, self.port)
            self.connection.login(self.username, self.password)
            logger.info("Connected to email server successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to email server: {e}")
            raise

    def fetch_emails(self, folder: str = "INBOX", limit: Optional[int] = 50):
        if not self.connection:
            logger.error("No connection to email server. Call connect() first.")
            return []
        try:
            self.connection.select(folder)
            status, messages = self.connection.search(None, "ALL")
            if status != "OK":
                logger.error("Failed to fetch emails.")
                return []

            email_ids = messages[0].split()
            if limit:
                email_ids = email_ids[-limit:]
            emails = []

            for email_id in email_ids:
                res, msg = self.connection.fetch(email_id, "(BODY.PEEK[])")  # BODY.PEEK[] 避免改状态，可留 RFC822
                if res != "OK":
                    logger.warning("Failed to fetch email with ID %s", email_id)
                    continue

                raw_chunks: list[bytes] = []
                for response_part in msg:
                    if isinstance(response_part, tuple):
                        raw_chunks.append(response_part[1])
                if not raw_chunks:
                    logger.warning("Empty payload for email %s", email_id)
                    continue

                raw_bytes = b"".join(raw_chunks)
                parsed_email = self.parse_email(email.message_from_bytes(raw_bytes))
                emails.append(
                    {
                        "raw_content": raw_bytes,
                        "encoding": parsed_email.pop("encoding", None),
                        "message_id": parsed_email.pop("message_id", None),
                        "received_at": parsed_email.pop("received_at", None),
                        "parsed": parsed_email,
                    }
                )

            return emails
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []

    def parse_email(self, msg):
        subject = _decode_mime_words(msg.get("Subject"))
        display_name, email_address = parseaddr(msg.get("From", ""))
        decoded_name = _decode_mime_words(display_name)
        if decoded_name and email_address:
            from_ = f"{decoded_name} <{email_address}>"
        else:
            from_ = decoded_name or email_address

        body_text = ""
        body_html = None
        attachments_meta: list[dict] = []
        attachments_base64: list[str] = []

        parts = [msg]
        if msg.is_multipart():
            parts = [part for part in msg.walk() if part.get_content_maintype() != "multipart"]

        for part in parts:
            disposition = part.get("Content-Disposition", "")
            if "attachment" in disposition.lower():
                filename = part.get_filename()
                payload_bytes = part.get_payload(decode=True) or b""
                attachment_name = _decode_mime_words(filename) if filename else "attachment"
                content_type = part.get_content_type()

                attachments_meta.append(
                    {
                        "name": attachment_name,
                        "size": len(payload_bytes),
                        "content_type": content_type,
                    }
                )
                attachments_base64.append(base64.b64encode(payload_bytes).decode("ascii"))
                continue

            content_type = part.get_content_type()
            if content_type == "text/plain":
                body_text = _decode_part_payload(part)
            elif content_type == "text/html":
                html_payload = _decode_part_payload(part)
                cleaned_html, extracted_text = _extract_html(html_payload)
                body_html = cleaned_html
                if not body_text:
                    body_text = extracted_text

        if not body_text:
            body_text = _decode_part_payload(msg)

        message_id = msg.get("Message-ID")
        raw_date = msg.get("Date")
        received_at: Optional[datetime] = None
        if raw_date:
            try:
                parsed = parsedate_to_datetime(raw_date)
                if parsed is not None:
                    received_at = parsed.astimezone(timezone.utc).replace(tzinfo=None)
            except Exception as exc:  # pragma: no cover - best effort fallback
                logger.warning("Failed to parse email date: %s", exc)
        if received_at is None:
            received_at = datetime.utcnow()

        encoding = msg.get_content_charset() or msg.get_charset() or "utf-8"

        return {
            "subject": subject or "",
            "sender": from_ or "",
            "body_text": body_text,
            "body_html": body_html,
            "attachments_meta": attachments_meta,
            "attachments_base64": attachments_base64,
            "summary": None,
            "message_id": message_id,
            "received_at": received_at,
            "encoding": encoding,
        }

    def close_connection(self):
        if self.connection:
            self.connection.logout()
            logger.info("Disconnected from email server.")

