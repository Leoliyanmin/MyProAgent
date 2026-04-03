from typing import List, Dict, Any
from datetime import datetime


class TaskBusinessLogic:
    def prioritize_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        return sorted(tasks, key=lambda x: (priority_order.get(x.get('priority'), 2), x.get('due_date') or datetime.max))

    def detect_overdue_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        now = datetime.now()
        return [task for task in tasks if task.get('due_date') and task.get('due_date') < now and task.get('status') != 'completed']

    def generate_study_plan(self, tasks: List[Dict[str, Any]], schedules: List[Dict[str, Any]]) -> Dict[str, Any]:
        prioritized_tasks = self.prioritize_tasks(tasks)
        overdue_tasks = self.detect_overdue_tasks(tasks)
        
        return {
            'prioritized_tasks': prioritized_tasks,
            'overdue_tasks': overdue_tasks,
            'suggestions': []
        }
