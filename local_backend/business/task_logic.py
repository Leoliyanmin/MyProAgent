from datetime import datetime, timedelta


class TaskLogic:
    def validate_task(self, task_data: dict) -> dict:
        """验证任务数据"""
        if not task_data.get('title'):
            return {'success': False, 'message': 'Title is required'}
        
        if task_data.get('due_date'):
            try:
                # 检查是否已经是datetime对象
                due_date = task_data['due_date']
                # 如果是字符串，转换为datetime对象
                if isinstance(due_date, str):
                    datetime.fromisoformat(due_date)
            except ValueError:
                return {'success': False, 'message': 'Invalid due date format'}
        
        return {'success': True}

    def get_overdue_tasks(self, tasks: list) -> list:
        """获取过期任务"""
        overdue_tasks = []
        now = datetime.utcnow()
        
        for task in tasks:
            if task.due_date and task.due_date < now and task.status != 'completed':
                overdue_tasks.append(task)
        
        return overdue_tasks

    def prioritize_tasks(self, tasks: list) -> list:
        """任务优先级排序"""
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        
        def sort_key(task):
            priority_score = priority_order.get(task.priority, 2)
            due_date_score = task.due_date.timestamp() if task.due_date else float('inf')
            return (priority_score, due_date_score)
        
        return sorted(tasks, key=sort_key)
