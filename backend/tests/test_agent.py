from fastapi.testclient import TestClient
from main import app

client = TestClient(app=app)


def test_chat_with_agent():
    """测试与Agent聊天功能"""
    # 先登录获取token
    login_response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    
    # 与Agent聊天
    response = client.post("/agent/chat", json={
        "query": "Hello, what can you do?",
        "session_id": "test_session_123"
    }, headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "thought_trace" in data


def test_get_chat_history():
    """测试获取聊天历史"""
    # 先登录获取token
    login_response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    
    # 先发送一条消息
    client.post("/agent/chat", json={
        "query": "Hello, what can you do?",
        "session_id": "test_session_456"
    }, headers={
        "Authorization": f"Bearer {token}"
    })
    
    # 获取聊天历史
    response = client.get("/agent/history/test_session_456", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
