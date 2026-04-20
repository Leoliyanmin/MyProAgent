from database.code.database_task_operations import TaskOperations


class TaskHandle:
    """任务功能调用入口"""

    def __init__(self):
        self.operations = TaskOperations()

    def create_task(self, user_id: str, title: str, description: str = None, due_date: str = None, linked_schedule_id: int = None) -> dict:
        """创建任务入口"""
        if not user_id or not title:
            return {'ok': False, 'status': 400, 'message': 'user_id 和 title 不能为空'}
        
        try:
            task_id = self.operations.create_task(
                user_id=user_id,
                title=title,
                description=description,
                due_date=due_date,
                linked_schedule_id=linked_schedule_id,
            )
            return {'ok': True, 'status': 201, 'data': {'task_id': task_id}}
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'创建任务失败: {str(e)}'}

    def get_tasks(self, user_id: str) -> dict:
        """获取用户任务列表入口"""
        # 验证输入
        if not user_id:
            return {'ok': False, 'status': 400, 'message': 'user_id 不能为空'}
        
        try:
            tasks = self.operations.get_tasks_by_user(user_id)
            return {'ok': True, 'status': 200, 'data': tasks}
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'获取任务失败: {str(e)}'}

    def update_task(self, user_id: str, task_id: int, title: str = None, description: str = None, due_date: str = None, linked_schedule_id: int | None | object = None) -> dict:
        """更新任务入口"""
        if not task_id:
            return {'ok': False, 'status': 400, 'message': 'task_id 不能为空'}
        
        try:
            self.operations.update_task(
                user_id=user_id,
                task_id=task_id,
                title=title,
                description=description,
                due_date=due_date,
                linked_schedule_id=linked_schedule_id,
            )
            return {'ok': True, 'status': 200, 'message': '任务更新成功'}
        except ValueError as e:
            return {'ok': False, 'status': 404, 'message': str(e)}
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'更新任务失败: {str(e)}'}

    def delete_task(self, user_id: str, task_id: int) -> dict:
        """删除任务入口"""
        # 验证输入
        if not task_id:
            return {'ok': False, 'status': 400, 'message': 'task_id 不能为空'}
        
        try:
            deleted = self.operations.delete_task(user_id, task_id)
            if not deleted:
                return {
                    'ok': True,
                    'status': 200,
                    'message': '任务不存在，已视为删除成功',
                    'already_deleted': True,
                }
            return {'ok': True, 'status': 200, 'message': '任务删除成功'}
        except ValueError as e:
            return {'ok': False, 'status': 404, 'message': str(e)}
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'删除任务失败: {str(e)}'}