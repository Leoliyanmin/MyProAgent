import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from database.code.operations.database_user_operations import list_users
from database.code.operations.database_task_operations import TaskOperations
from database.code.operations.database_schedule_operations import ScheduleOperations

# 创建操作类实例
schedule_ops = ScheduleOperations()
from config import settings
import requests

logger = logging.getLogger("scheduler_service")

class SchedulerService:
    """定时任务调度服务 - 本地到服务器单向同步"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
        self.is_running = False
    
    def start(self, sync_interval_seconds: int = 3600, email_sync_interval_seconds: int = 1800):
        """启动定时任务调度器"""
        if self.is_running:
            logger.warning("调度器已在运行中")
            return

        self.scheduler.add_job(
            self.sync_local_to_server,
            trigger=IntervalTrigger(seconds=sync_interval_seconds),
            id="local_to_server_sync",
            name="本地到服务器数据同步",
            replace_existing=True
        )

        self.scheduler.add_job(
            self.sync_emails_for_all_users,
            trigger=IntervalTrigger(seconds=email_sync_interval_seconds),
            id="email_sync",
            name="邮件定时同步",
            replace_existing=True
        )

        self.scheduler.start()
        self.is_running = True
        logger.info(
            f"定时任务调度器已启动: "
            f"本地同步间隔={sync_interval_seconds}秒, "
            f"邮件同步间隔={email_sync_interval_seconds}秒"
        )
    
    def stop(self):
        """停止定时任务调度器"""
        if self.is_running:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("定时任务调度器已停止")
    
    def sync_local_to_server(self):
        """本地数据同步到服务器"""
        logger.info("开始执行本地到服务器同步任务")
        
        try:
            users = list_users()
            
            if not users:
                logger.info("没有找到用户，跳过同步")
                return
            
            total_synced = 0
            total_failed = 0
            
            for user in users:
                user_id = user.get('user_id')
                if not user_id:
                    continue
                
                try:
                    # 获取用户的任务数据
                    tasks = TaskOperations.get_tasks_by_user(user_id)
                    # 获取用户的日程数据
                    schedules = schedule_ops.get_schedules_by_user(user_id)
                    
                    # 如果没有数据，跳过
                    if not tasks and not schedules:
                        continue
                    
                    headers = {"X-User-ID": str(user_id)}
                    all_ok = True

                    if tasks:
                        resp = requests.post(
                            f"{settings.SERVER_BACKEND_URL}/sync/from-client",
                            json={"data_type": "data", "data": tasks},
                            headers=headers,
                        )
                        if resp.status_code != 200:
                            all_ok = False
                            logger.error(f"用户 {user_id} 任务同步HTTP错误: {resp.status_code}")

                    if schedules:
                        resp = requests.post(
                            f"{settings.SERVER_BACKEND_URL}/sync/from-client",
                            json={"data_type": "schedule", "data": schedules},
                            headers=headers,
                        )
                        if resp.status_code != 200:
                            all_ok = False
                            logger.error(f"用户 {user_id} 日程同步HTTP错误: {resp.status_code}")

                    if all_ok:
                        total_synced += 1
                        logger.info(f"用户 {user_id} 同步成功: {len(tasks)} 个任务, {len(schedules)} 个日程")
                    else:
                        total_failed += 1
                        
                except Exception as e:
                    total_failed += 1
                    logger.error(f"用户 {user_id} 同步异常: {str(e)}")
            
            logger.info(f"本地到服务器同步完成: 成功 {total_synced} 人, 失败 {total_failed} 人")
            
        except Exception as e:
            logger.error(f"同步任务执行异常: {str(e)}")
    
    def sync_emails_for_all_users(self):
        """定时同步所有已绑定邮箱用户的邮件"""
        logger.info("开始执行邮件定时同步任务")

        try:
            users = list_users()

            if not users:
                logger.info("没有找到用户，跳过邮件同步")
                return

            total_synced = 0
            total_skipped = 0
            total_failed = 0

            for user in users:
                user_id = user.get('user_id')
                if not user_id:
                    continue

                try:
                    from service.email_service import EmailService
                    email_service = EmailService()

                    result = email_service.sync_email_data(user_id, max_messages=50)

                    if result.get('success'):
                        total_synced += 1
                        data = result.get('data', {})
                        logger.info(f"用户 {user_id} 邮件同步成功: {data.get('synced', 0)} 封")
                    else:
                        msg = result.get('message', '')
                        if '未绑定邮箱' in msg:
                            total_skipped += 1
                        else:
                            total_failed += 1
                            logger.error(f"用户 {user_id} 邮件同步失败: {msg}")

                except Exception as e:
                    total_failed += 1
                    logger.error(f"用户 {user_id} 邮件同步异常: {str(e)}")

            logger.info(
                f"邮件定时同步完成: "
                f"成功 {total_synced} 人, "
                f"跳过(未绑定) {total_skipped} 人, "
                f"失败 {total_failed} 人"
            )

        except Exception as e:
            logger.error(f"邮件同步任务执行异常: {str(e)}")

    def get_jobs(self):
        """获取当前所有定时任务"""
        if not self.is_running:
            return []
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return jobs

# 创建全局调度器实例
scheduler_service = SchedulerService()
