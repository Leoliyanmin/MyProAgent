# service/email/email_time_update.py

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from core.database import get_db_sync
from core import email_crypto
from model.entities import EmailAccount
from service.email.email_sync_service import sync_mailbox

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

email_scheduler = None


def _update_email_once(limit: int = 50):
    """
    每次调度执行：扫描 EmailAccount，按账号同步邮件。
    只拉取最新 limit 封，由 bulk_upsert 自动去重。
    """
    logger.info("[email_scheduler] 开始同步任务 %s", datetime.now())
    db: Session = get_db_sync()

    try:
        # ★ 现在所有邮箱凭据都在 EmailAccount 表中
        accounts = db.query(EmailAccount).all()

        for acc in accounts:
            try:
                # 解密存储的密码
                decrypted_password = email_crypto.decrypt_stored_password(acc.password)

                fetched, created, skipped = sync_mailbox(
                    db=db,
                    user_id=acc.user_id,
                    host=acc.host,
                    username=acc.email,
                    password=decrypted_password,
                    port=acc.port,
                    folder="INBOX",
                    limit=limit,
                    use_ssl=acc.use_ssl,
                )

                logger.info(
                    "[email_scheduler] user_id=%s email=%s -> fetched=%s created=%s skipped=%s",
                    acc.user_id, acc.email, fetched, created, skipped
                )

            except Exception as e:
                logger.exception(
                    "[email_scheduler] 同步用户 %s (%s) 的邮箱失败: %s",
                    acc.user_id, acc.email, e
                )

        db.commit()

    except Exception:
        logger.exception("[email_scheduler] 邮件调度执行错误")

    finally:
        db.close()


def start_email_scheduler(interval_minutes: int = 10, limit: int = 50):
    """
    启动邮件调度器（全局单例，重复调用不重复启动）。
    """
    global email_scheduler
    if email_scheduler:
        logger.info("email_scheduler 已经在运行，跳过重复启动")
        return email_scheduler

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _update_email_once,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="email_update_job",
        max_instances=1,
        replace_existing=True,
        kwargs={"limit": limit},
    )
    scheduler.start()

    email_scheduler = scheduler
    logger.info("email_scheduler 已启动：每 %d 分钟同步一次", interval_minutes)
    return scheduler


def stop_email_scheduler():
    """
    停止调度器（通常在 /emails/logout 时调用）
    """
    global email_scheduler
    if email_scheduler:
        try:
            email_scheduler.shutdown()
            logger.info("email_scheduler 已停止")
        except Exception as e:
            logger.warning("停止 email_scheduler 时出现异常: %s", e)
        finally:
            email_scheduler = None
