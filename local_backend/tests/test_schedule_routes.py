import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    mock_schedule_service = MagicMock()
    with patch('presentation.schedule_routes.schedule_service', mock_schedule_service):
        from main import app
        yield TestClient(app)


class TestGetSchedules:
    def test_get_schedules_empty(self, client):
        from presentation.schedule_routes import schedule_service
        schedule_service.get_schedules = MagicMock(return_value={
            'success': True,
            'schedules': [],
        })

        response = client.get('/schedules/')

        assert response.status_code == 200
        assert response.json() == []

    def test_get_schedules_with_data(self, client):
        from presentation.schedule_routes import schedule_service
        schedule_service.get_schedules = MagicMock(return_value={
            'success': True,
            'schedules': [
                {'id': 1, 'title': 'Meeting', 'start_time': '2026-05-20T10:00:00'},
            ],
        })

        response = client.get('/schedules/')

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_schedules_failure(self, client):
        from presentation.schedule_routes import schedule_service
        schedule_service.get_schedules = MagicMock(return_value={
            'success': False,
            'message': 'Database error',
        })

        response = client.get('/schedules/')

        assert response.status_code == 400


class TestCreateSchedule:
    def test_create_schedule_success(self, client):
        from presentation.schedule_routes import schedule_service
        schedule_service.create_schedule = MagicMock(return_value={
            'success': True,
            'message': 'Schedule created',
        })

        response = client.post('/schedules/', json={
            'title': 'Meeting',
            'start_time': '2026-05-20T10:00:00',
            'end_time': '2026-05-20T11:00:00',
        })

        assert response.status_code == 200
        assert response.json()['success'] is True

    def test_create_schedule_validation_error(self, client):
        """Pydantic rejects empty title — returns 422 before reaching service."""
        response = client.post('/schedules/', json={'title': ''})

        assert response.status_code == 422


class TestUpdateSchedule:
    def test_update_schedule_success(self, client):
        from presentation.schedule_routes import schedule_service
        schedule_service.update_schedule = MagicMock(return_value={'success': True})

        response = client.put('/schedules/1', json={'title': 'Updated Meeting'})

        assert response.status_code == 200

    def test_update_schedule_not_found(self, client):
        from presentation.schedule_routes import schedule_service
        schedule_service.update_schedule = MagicMock(return_value={
            'success': False,
            'message': 'Schedule not found',
        })

        response = client.put('/schedules/999', json={'title': 'Ghost'})

        assert response.status_code == 404


class TestDeleteSchedule:
    def test_delete_schedule_success(self, client):
        from presentation.schedule_routes import schedule_service
        schedule_service.delete_schedule = MagicMock(return_value={'success': True})

        response = client.delete('/schedules/1')

        assert response.status_code == 200

    def test_delete_schedule_not_found(self, client):
        from presentation.schedule_routes import schedule_service
        schedule_service.delete_schedule = MagicMock(return_value={
            'success': False,
            'message': 'Schedule not found',
        })

        response = client.delete('/schedules/999')

        assert response.status_code == 404
