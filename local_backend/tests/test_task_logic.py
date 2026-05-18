from datetime import datetime, timedelta
import pytest
from business.task_logic import TaskLogic


class FakeTask:
    """Minimal object that mimics a task row for get_overdue_tasks / prioritize_tasks."""
    def __init__(self, id, due_date, priority, status='pending'):
        self.id = id
        self.due_date = due_date
        self.priority = priority
        self.status = status


class TestTaskValidate:
    def setup_method(self):
        self.logic = TaskLogic()

    def test_rejects_empty_title(self):
        result = self.logic.validate_task({})
        assert result['success'] is False
        assert 'Title' in result['message']

    def test_accepts_valid_task(self):
        result = self.logic.validate_task({'title': 'Buy milk'})
        assert result['success'] is True

    def test_accepts_valid_iso_due_date(self):
        result = self.logic.validate_task({
            'title': 'Buy milk',
            'due_date': '2026-05-20T10:00:00'
        })
        assert result['success'] is True

    def test_rejects_invalid_due_date_string(self):
        result = self.logic.validate_task({
            'title': 'Buy milk',
            'due_date': 'not-a-date'
        })
        assert result['success'] is False
        assert 'date' in result['message'].lower()

    def test_accepts_datetime_object_as_due_date(self):
        result = self.logic.validate_task({
            'title': 'Buy milk',
            'due_date': datetime(2026, 5, 20)
        })
        assert result['success'] is True


class TestGetOverdueTasks:
    def setup_method(self):
        self.logic = TaskLogic()

    def test_empty_list_returns_empty(self):
        assert self.logic.get_overdue_tasks([]) == []

    def test_overdue_task_returned(self):
        past = datetime.utcnow() - timedelta(days=1)
        tasks = [FakeTask(1, past, 'high')]
        result = self.logic.get_overdue_tasks(tasks)
        assert len(result) == 1
        assert result[0].id == 1

    def test_future_task_not_returned(self):
        future = datetime.utcnow() + timedelta(days=1)
        tasks = [FakeTask(1, future, 'high')]
        assert self.logic.get_overdue_tasks(tasks) == []

    def test_completed_overdue_task_not_returned(self):
        past = datetime.utcnow() - timedelta(days=1)
        tasks = [FakeTask(1, past, 'high', status='completed')]
        assert self.logic.get_overdue_tasks(tasks) == []

    def test_task_without_due_date_not_returned(self):
        tasks = [FakeTask(1, None, 'high')]
        assert self.logic.get_overdue_tasks(tasks) == []


class TestPrioritizeTasks:
    def setup_method(self):
        self.logic = TaskLogic()

    def test_empty_list(self):
        assert self.logic.prioritize_tasks([]) == []

    def test_sorts_high_before_low(self):
        nowish = datetime.utcnow()
        tasks = [
            FakeTask(1, nowish, 'low'),
            FakeTask(2, nowish, 'high'),
        ]
        sorted_tasks = self.logic.prioritize_tasks(tasks)
        assert sorted_tasks[0].id == 2
        assert sorted_tasks[1].id == 1

    def test_same_priority_sorts_by_due_date(self):
        early = datetime.utcnow()
        late = early + timedelta(days=10)
        tasks = [
            FakeTask(1, late, 'medium'),
            FakeTask(2, early, 'medium'),
        ]
        sorted_tasks = self.logic.prioritize_tasks(tasks)
        assert sorted_tasks[0].id == 2
        assert sorted_tasks[1].id == 1

    def test_task_without_due_date_goes_last(self):
        nowish = datetime.utcnow()
        tasks = [
            FakeTask(1, None, 'high'),
            FakeTask(2, nowish, 'high'),
        ]
        sorted_tasks = self.logic.prioritize_tasks(tasks)
        assert sorted_tasks[0].id == 2
        assert sorted_tasks[1].id == 1
