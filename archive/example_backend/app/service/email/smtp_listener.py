# service/email/smtp_listener.py
"""
SMTP 接收器（轻量）—— 当外部 MTA 把邮件推给此服务时，立即写入数据库。
"""

import logging
from aiosmtpd.controller import Controller
from email import message_from_bytes
from core.database import get_db_sync
from crud import email as email_crud
from model.entities import User

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

_controller = None


class InboundHandler:
    async def handle_DATA(self, server, session, envelope):
        raw_bytes = envelope.content
        rcpts = envelope.rcpt_tos or []

        db = get_db_sync()
        try:
            target_user = None
            for r in rcpts:
                u = db.query(User).filter(User.email == r).first()
                if u:
                    target_user = u
                    break

            if not target_user:
                logger.warning("SMTPReceiver: 未在 user 表找到收件人匹配 (%s)，邮件将被忽略。", rcpts)
                return "250 OK"

            item = {
                "raw_content": raw_bytes,
                "encoding": None,
                "message_id": None,
                "received_at": None,
                "parsed": None,
            }
            created, skipped = email_crud.bulk_upsert_emails(db, target_user.user_id, [item])
            logger.info("SMTPReceiver: user_id=%s created=%s skipped=%s", target_user.user_id, created, skipped)
            return "250 Message accepted for delivery"
        except Exception:
            logger.exception("SMTPReceiver: 处理邮件时发生异常")
            return "451 Temporary server error"
        finally:
            db.close()


def start_smtp_listener(host: str = "0.0.0.0", port: int = 2525):
    """
    启动 SMTP 接收器（后台线程）。
    """
    global _controller
    if _controller is not None:
        logger.info("SMTPReceiver 已启动，跳过重复启动")
        return _controller

    try:
        handler = InboundHandler()
        controller = Controller(handler, hostname=host, port=port)
        controller.start()
        _controller = controller
        logger.info(f"SMTPReceiver 已启动：{host}:{port}")
        return controller
    except OSError as e:
        logger.error(f"SMTPReceiver 启动失败: {e}")
        _controller = None
        return None


def stop_smtp_listener():
    global _controller
    if _controller:
        try:
            _controller.stop()
            logger.info("SMTPReceiver 已停止")
        except Exception as e:
            logger.warning(f"SMTPReceiver 停止时出现异常: {e}")
        finally:
            _controller = None
