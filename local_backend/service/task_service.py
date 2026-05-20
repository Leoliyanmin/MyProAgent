import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from business.task_logic import TaskLogic
from database.code.handle.database_task_v2_handle import TaskV2Handle
from logging_config import get_logger

# 创建日志器
logger = get_logger("task_service")


class TaskService:
    def __init__(self):
        self.task_logic = TaskLogic()
        self.task_handle = TaskV2Handle()
        logger.info("TaskService 初始化完成")

    def create_task(self, user_id: str, task_data: dict):
        title = task_data.get('title', '')
        description = task_data.get('description', '')
        due_date = task_data.get('due_date')
        linked_schedule_id = task_data.get('linked_schedule_id')
        
        logger.info(f"创建任务: user_id={user_id}, title={title}")
        
        if not title:
            logger.warning(f"创建任务失败: 任务标题不能为空, user_id={user_id}")
            return {'success': False, 'message': '任务标题不能为空'}
        
        result = self.task_handle.create_task(user_id, title, description, due_date, linked_schedule_id=linked_schedule_id)
        if not result['ok']:
            logger.error(f"创建任务失败: {result['message']}, user_id={user_id}")
            return {'success': False, 'message': result['message']}
        
        logger.info(f"任务创建成功: user_id={user_id}, task_id={result['data']['task_id']}")
        return {
            'success': True,
            'task_id': result['data']['task_id']
        }

    def get_tasks(self, user_id: str):
        logger.debug(f"获取任务列表: user_id={user_id}")
        
        result = self.task_handle.get_tasks(user_id)
        if not result['ok']:
            logger.warning(f"获取任务列表失败: {result['message']}, user_id={user_id}")
            return {'success': False, 'message': result['message']}
        
        logger.debug(f"获取任务列表成功: user_id={user_id}, task_count={len(result['data'])}")
        return {
            'success': True,
            'tasks': result['data']
        }

    def update_task(self, user_id: str, task_id: int, task_data: dict):
        title = task_data.get('title')
        description = task_data.get('description')
        due_date = task_data.get('due_date')
        linked_schedule_id = task_data.get('linked_schedule_id')
        
        logger.info(f"更新任务: user_id={user_id}, task_id={task_id}")
        
        result = self.task_handle.update_task(user_id, task_id, title=title, description=description, due_date=due_date, linked_schedule_id=linked_schedule_id)
        if not result['ok']:
            logger.error(f"更新任务失败: {result['message']}, user_id={user_id}, task_id={task_id}")
            return {'success': False, 'message': result['message']}
        
        logger.info(f"任务更新成功: user_id={user_id}, task_id={task_id}")
        return {'success': True, 'message': '任务更新成功'}

    def delete_task(self, user_id: str, task_id: int):
        logger.info(f"删除任务: user_id={user_id}, task_id={task_id}")
        
        result = self.task_handle.delete_task(user_id, task_id)
        if not result['ok']:
            logger.error(f"删除任务失败: {result['message']}, user_id={user_id}, task_id={task_id}")
            return {'success': False, 'message': result['message']}
        
        if result.get('already_deleted'):
            logger.warning(f"删除任务目标不存在，按幂等删除处理: user_id={user_id}, task_id={task_id}")
            return {'success': True, 'message': result['message']}
        
        logger.info(f"任务删除成功: user_id={user_id}, task_id={task_id}")
        return {'success': True, 'message': '任务删除成功'}

    def get_study_plan(self, user_id: str):
        """获取学习计划"""
        logger.debug(f"获取学习计划: user_id={user_id}")
        
        # 获取用户的任务列表作为学习计划
        result = self.task_handle.get_tasks(user_id)
        if not result['ok']:
            logger.warning(f"获取学习计划失败: {result['message']}, user_id={user_id}")
            return {'success': False, 'message': result['message']}
        
        logger.debug(f"获取学习计划成功: user_id={user_id}, plan_count={len(result['data'])}")
        return {
            'success': True,
            'study_plan': result['data']
        }