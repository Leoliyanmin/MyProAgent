import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    mock_task_service = MagicMock()
    with patch('presentation.task_routes.task_service', mock_task_service):
        from main import app
        yield TestClient(app)


class TestGetTasks:
    def test_get_tasks_empty(self, client):
        from presentation.task_routes import task_service
        task_service.get_tasks = MagicMock(return_value={
            'success': True,
            'tasks': [],
        })

        response = client.get('/tasks/')

        assert response.status_code == 200
        assert response.json() == []

    def test_get_tasks_with_data(self, client):
        from presentation.task_routes import task_service
        task_service.get_tasks = MagicMock(return_value={
            'success': True,
            'tasks': [
                {'id': 1, 'title': 'Task 1', 'status': 'pending'},
                {'id': 2, 'title': 'Task 2', 'status': 'completed'},
            ],
        })

        response = client.get('/tasks/')

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_tasks_failure(self, client):
        from presentation.task_routes import task_service
        task_service.get_tasks = MagicMock(return_value={
            'success': False,
            'message': 'Database error',
        })

        response = client.get('/tasks/')

        assert response.status_code == 400


class TestCreateTask:
    def test_create_task_success(self, client):
        from presentation.task_routes import task_service
        task_service.create_task = MagicMock(return_value={
            'success': True,
            'message': 'Task created',
            'task': {'id': 1, 'title': 'New Task'},
        })

        response = client.post('/tasks/', json={
            'title': 'New Task',
            'priority': 'high',
            'status': 'pending',
        })

        assert response.status_code == 200
        assert response.json()['success'] is True

    def test_create_task_failure(self, client):
        from presentation.task_routes import task_service
        task_service.create_task = MagicMock(return_value={
            'success': False,
            'message': 'Invalid data',
        })

        response = client.post('/tasks/', json={'title': 'Bad Task'})

        assert response.status_code == 400


class TestUpdateTask:
    def test_update_task_success(self, client):
        from presentation.task_routes import task_service
        task_service.update_task = MagicMock(return_value={
            'success': True,
        })

        response = client.put('/tasks/1', json={'title': 'Updated'})

        assert response.status_code == 200
        assert response.json()['success'] is True

    def test_update_task_not_found(self, client):
        from presentation.task_routes import task_service
        task_service.update_task = MagicMock(return_value={
            'success': False,
            'message': 'Task not found',
        })

        response = client.put('/tasks/999', json={'title': 'Ghost'})

        assert response.status_code == 404


class TestDeleteTask:
    def test_delete_task_success(self, client):
        from presentation.task_routes import task_service
        task_service.delete_task = MagicMock(return_value={'success': True})

        response = client.delete('/tasks/1')

        assert response.status_code == 200

    def test_delete_task_not_found(self, client):
        from presentation.task_routes import task_service
        task_service.delete_task = MagicMock(return_value={
            'success': False,
            'message': 'Task not found',
        })

        response = client.delete('/tasks/999')

        assert response.status_code == 404
