from business.task_logic import TaskLogic
from database.code.database_task_handle import TaskHandle


class TaskService:
    def __init__(self):
        self.task_logic = TaskLogic()
        self.task_handle = TaskHandle()

    def create_task(self, user_id: str, task_data: dict):
        title = task_data.get('title', '')
        description = task_data.get('description', '')
        due_date = task_data.get('due_date')
        
        if not title:
            return {'success': False, 'message': '任务标题不能为空'}
        
        result = self.task_handle.create_task(user_id, title, description, due_date)
        if not result['ok']:
            return {'success': False, 'message': result['message']}
        
        return {
            'success': True,
            'task_id': result['data']['task_id']
        }

    def get_tasks(self, user_id: str):
        result = self.task_handle.get_tasks(user_id)
        if not result['ok']:
            return {'success': False, 'message': result['message']}
        
        return {
            'success': True,
            'tasks': result['data']
        }

    def update_task(self, user_id: str, task_id: int, task_data: dict):
        title = task_data.get('title')
        description = task_data.get('description')
        due_date = task_data.get('due_date')
        
        result = self.task_handle.update_task(user_id, task_id, title, description, due_date)
        if not result['ok']:
            return {'success': False, 'message': result['message']}
        
        return {'success': True, 'message': '任务更新成功'}

    def delete_task(self, user_id: str, task_id: int):
        result = self.task_handle.delete_task(user_id, task_id)
        if not result['ok']:
            return {'success': False, 'message': result['message']}
        
        return {'success': True, 'message': '任务删除成功'}

    def get_study_plan(self, user_id: str):
        """获取学习计划"""
        # 获取用户的任务列表作为学习计划
        result = self.task_handle.get_tasks(user_id)
        if not result['ok']:
            return {'success': False, 'message': result['message']}
        
        return {
            'success': True,
            'study_plan': result['data']
        }