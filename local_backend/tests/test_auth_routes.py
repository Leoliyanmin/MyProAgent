import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from config import settings


def _async_return(value):
    """Helper: returns a coroutine that resolves to `value`."""
    async def _inner(*args, **kwargs):
        return value
    return _inner


@pytest.fixture
def client():
    mock_user_service = MagicMock()
    mock_auth_service = MagicMock()

    with patch('presentation.auth_routes.user_service', mock_user_service), \
         patch('presentation.auth_routes.auth_service', mock_auth_service):
        from main import app
        yield TestClient(app)


class TestSendVerificationCode:
    def test_send_code_returns_test_code_in_test_mode(self, client):
        from presentation.auth_routes import auth_service
        auth_service.send_verification_code = _async_return({
            'success': True,
            'message': 'TEST MODE',
            'test_code': '123456',
            'expires_in': 300,
            'retry_after': 60,
        })

        response = client.post('/auth/verification/send', json={
            'email': 'test@mail.sustech.edu.cn',
            'purpose': 'register',
        })

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['test_code'] == '123456'


class TestRegister:
    def test_register_success(self, client):
        from presentation.auth_routes import user_service
        user_service.register_user = _async_return({
            'success': True,
            'access_token': 'token-abc',
            'token_type': 'bearer',
            'user': {'id': 'test@mail.sustech.edu.cn'},
        })

        response = client.post('/auth/register', json={
            'email': 'test@mail.sustech.edu.cn',
            'password': 'Abcdefgh1',
            'confirm_password': 'Abcdefgh1',
            'verification_code': '123456',
            'full_name': 'Test User',
        })

        assert response.status_code == 200
        assert response.json()['success'] is True

    def test_register_failure(self, client):
        from presentation.auth_routes import user_service
        user_service.register_user = _async_return({
            'success': False,
            'message': 'Email already registered',
        })

        response = client.post('/auth/register', json={
            'email': 'test@mail.sustech.edu.cn',
            'password': 'Abcdefgh1',
            'confirm_password': 'Abcdefgh1',
            'verification_code': '123456',
        })

        assert response.status_code == 400
        assert 'Email already registered' in response.json()['detail']


class TestLogin:
    def test_login_success(self, client):
        from presentation.auth_routes import user_service
        user_service.login_user = _async_return({
            'success': True,
            'access_token': 'token-abc',
            'token_type': 'bearer',
        })

        response = client.post('/auth/login', json={
            'email': 'test@mail.sustech.edu.cn',
            'password': 'Abcdefgh1',
        })

        assert response.status_code == 200
        assert response.json()['success'] is True

    def test_login_failure(self, client):
        from presentation.auth_routes import user_service
        user_service.login_user = _async_return({
            'success': False,
            'message': 'Invalid credentials',
        })

        response = client.post('/auth/login', json={
            'email': 'test@mail.sustech.edu.cn',
            'password': 'wrong',
        })

        assert response.status_code == 401
        assert 'Invalid credentials' in response.json()['detail']


class TestGetCurrentUser:
    @pytest.fixture(autouse=True)
    def _enable_test_mode(self):
        old = settings.TEST_MODE
        settings.TEST_MODE = True
        yield
        settings.TEST_MODE = old

    def test_get_current_user_in_test_mode(self, client):
        from presentation.auth_routes import user_service
        user_service.get_user_by_id = MagicMock(return_value=None)
        user_service.get_user_by_email = MagicMock(return_value=None)

        response = client.get('/auth/me')

        assert response.status_code == 200
        data = response.json()
        assert data['id'] == 'test_user'
        assert data['is_active'] is True

    def test_get_current_user_from_db(self, client):
        from presentation.auth_routes import user_service
        user_service.get_user_by_id = MagicMock(return_value={
            'user_id': 'real@mail.sustech.edu.cn',
            'user_email': 'real@mail.sustech.edu.cn',
            'username': 'Real User',
            'user_is_active': True,
            'user_created_at': '2026-01-01T00:00:00',
        })

        response = client.get('/auth/me')

        assert response.status_code == 200
        assert response.json()['email'] == 'real@mail.sustech.edu.cn'
