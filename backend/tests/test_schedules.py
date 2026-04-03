from fastapi.testclient import TestClient
from main import app

client = TestClient(app=app)


def test_create_schedule():
    """测试创建日程功能"""
    # 先登录获取token
    login_response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    
    # 创建日程
    response = client.post("/schedules/", json={
        "title": "Test Schedule",
        "description": "This is a test schedule",
        "start_time": "2024-01-01T09:00:00",
        "end_time": "2024-01-01T10:00:00",
        "location": "Office",
        "is_recurring": False
    }, headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Schedule"


def test_get_schedules():
    """测试获取日程列表"""
    # 先登录获取token
    login_response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    
    # 获取日程列表
    response = client.get("/schedules/", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_update_schedule():
    """测试更新日程功能"""
    # 先登录获取token
    login_response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    
    # 创建一个日程
    create_response = client.post("/schedules/", json={
        "title": "Schedule to Update",
        "description": "Original description",
        "start_time": "2024-01-02T09:00:00",
        "end_time": "2024-01-02T10:00:00",
        "location": "Office",
        "is_recurring": False
    }, headers={
        "Authorization": f"Bearer {token}"
    })
    schedule_id = create_response.json()["id"]
    
    # 更新日程
    response = client.put(f"/schedules/{schedule_id}", json={
        "title": "Updated Schedule",
        "description": "Updated description"
    }, headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Schedule"
    assert data["description"] == "Updated description"


def test_delete_schedule():
    """测试删除日程功能"""
    # 先登录获取token
    login_response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    
    # 创建一个日程
    create_response = client.post("/schedules/", json={
        "title": "Schedule to Delete",
        "description": "This will be deleted",
        "start_time": "2024-01-03T09:00:00",
        "end_time": "2024-01-03T10:00:00",
        "location": "Office",
        "is_recurring": False
    }, headers={
        "Authorization": f"Bearer {token}"
    })
    schedule_id = create_response.json()["id"]
    
    # 删除日程
    response = client.delete(f"/schedules/{schedule_id}", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
