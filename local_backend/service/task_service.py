from database.repositories import TaskRepository
from business.task_logic import TaskLogic


class TaskService:
    def __init__(self):
        self.task_repo = TaskRepository()
        self.task_logic = TaskLogic()

    def create_task(self, user_id: int, task_data: dict):
        validation = self.task_logic.validate_task(task_data)
        if not validation['success']:
            return validation
        
        task_data['user_id'] = user_id
        task = self.task_repo.create_task(task_data)
        
        return {
            'success': True,
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'priority': task.priority,
                'status': task.status
            }
        }

    def get_user_tasks(self, user_id: int):
        tasks = self.task_repo.get_tasks_by_user(user_id)
        return [
            {
                'id': t.id,
                'title': t.title,
                'description': t.description,
                'due_date': t.due_date.isoformat() if t.due_date else None,
                'priority': t.priority,
                'status': t.status
            }
            for t in tasks
        ]

    def update_task(self, task_id: int, update_data: dict):
        task = self.task_repo.get_task_by_id(task_id)
        if not task:
            return {'success': False, 'message': 'Task not found'}
        
        if 'due_date' in update_data:
            validation = self.task_logic.validate_task(update_data)
            if not validation['success']:
                return validation
        
        task = self.task_repo.update_task(task_id, update_data)
        if task:
            return {'success': True, 'message': 'Task updated successfully'}
        return {'success': False, 'message': 'Task not found'}

    def delete_task(self, task_id: int):
        if self.task_repo.delete_task(task_id):
            return {'success': True, 'message': 'Task deleted successfully'}
        return {'success': False, 'message': 'Task not found'}

    def get_study_plan(self, user_id: int):
        tasks = self.task_repo.get_tasks_by_user(user_id)
        prioritized_tasks = self.task_logic.prioritize_tasks(tasks)
        overdue_tasks = self.task_logic.get_overdue_tasks(tasks)
        
        return {
            'prioritized_tasks': [
                {
                    'id': t.id,
                    'title': t.title,
                    'due_date': t.due_date.isoformat() if t.due_date else None,
                    'priority': t.priority
                }
                for t in prioritized_tasks[:5]
            ],
            'overdue_tasks': [
                {
                    'id': t.id,
                    'title': t.title,
                    'due_date': t.due_date.isoformat()
                }
                for t in overdue_tasks
            ],
            'suggestions': [
                'Complete overdue tasks first',
                'Focus on high priority tasks',
                'Break down large tasks into smaller ones'
            ]
        }
