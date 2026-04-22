import threading
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from sqlalchemy.orm import Session
from core.database import SessionLocal

from util.bb_course import get_bb_courses
from util.bb_calendar import get_bb_calendar
from util.tis_schedule import fetch_and_process_schedule
from service.bb_file_service import BBFileService   # ⭐ 新增

from crud.schedule import save_schedule_to_db
from crud.ddl import save_ddl_to_db
from model.entities import User

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

stop_event = threading.Event()
scheduler = None


def _update_for_one_user(db: Session, user: User):
    sid = str(user.user_id)

    logger.info(f"[bb_tis_scheduler] 为用户 {sid} 更新数据...")

    # 1️⃣ 更新 TIS 课表
    try:
        schedule = fetch_and_process_schedule()
        save_schedule_to_db(db, sid, schedule)
        logger.info(f"[bb_tis_scheduler] 用户 {sid} TIS 课表更新完成")
    except Exception as e:
        logger.exception(f"[bb_tis_scheduler] 用户 {sid} TIS 课表更新失败：{e}")

    # 2️⃣ 更新 Blackboard 日历（DDL）
    try:
        calendar = get_bb_calendar()
        save_ddl_to_db(db, sid, calendar)
        logger.info(f"[bb_tis_scheduler] 用户 {sid} Blackboard 日历更新完成")
    except Exception as e:
        logger.exception(f"[bb_tis_scheduler] 用户 {sid} Blackboard 日历更新失败：{e}")

    # 3️⃣ 更新 Blackboard 文件
    try:
        result = BBFileService.sync_bb_files(db, user.user_id)
        logger.info(f"[bb_tis_scheduler] 用户 {sid} BB 文件同步结束：{result}")
    except Exception as e:
        logger.exception(f"[bb_tis_scheduler] 用户 {sid} BB 文件同步失败：{e}")


def _update_bb_and_tis_once():
    logger.info("[bb_tis_scheduler] ========== 开始执行自动更新任务 ==========")

    if stop_event.is_set():
        logger.info("[bb_tis_scheduler] 收到停止信号，中止执行")
        return

    try:
        db = SessionLocal()

        users = db.query(User).all()
        if not users:
            logger.warning("[bb_tis_scheduler] 无用户记录，跳过更新")
            return

        for user in users:
            if stop_event.is_set():
                break
            _update_for_one_user(db, user)

        logger.info("[bb_tis_scheduler] 所有用户数据更新完成")

    except Exception as e:
        logger.exception(f"[bb_tis_scheduler] 未捕获错误：{e}")

    finally:
        db.close()


def start_scheduler(interval_minutes: int = 60*24):
    global scheduler
    if scheduler:
        logger.warning("[bb_tis_scheduler] 调度器已在运行")
        return

    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    scheduler.add_job(
        _update_bb_and_tis_once,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="bb_tis_update",
        replace_existing=True,
        max_instances=1
    )

    scheduler.start()
    logger.info(f"[bb_tis_scheduler] 已启动定时任务，每 {interval_minutes} 分钟执行一次")


def stop_scheduler():
    global scheduler
    stop_event.set()

    if scheduler and scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("[bb_tis_scheduler] 调度器已停止")
        scheduler = None
