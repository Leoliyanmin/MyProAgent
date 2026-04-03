from layers.database.repositories import TaskRepository
from layers.business.task_logic import TaskBusinessLogic


class TaskService:
    def __init__(self):
        self.task_repo = TaskRepository()
        self.task_logic = TaskBusinessLogic()

    def create_task(self, user_id: int, task_data: dict):
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
        task_dicts = [
            {
                'id': t.id,
                'title': t.title,
                'due_date': t.due_date,
                'priority': t.priority,
                'status': t.status
            }
            for t in tasks
        ]
        
        return self.task_logic.generate_study_plan(task_dicts, [])
