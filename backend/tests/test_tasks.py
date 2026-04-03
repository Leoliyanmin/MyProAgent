from fastapi.testclient import TestClient
from main import app

client = TestClient(app=app)


def test_create_task():
    """测试创建任务功能"""
    # 先登录获取token
    login_response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    
    # 创建任务
    response = client.post("/tasks/", json={
        "title": "Test Task",
        "description": "This is a test task",
        "priority": "high",
        "due_date": "2024-01-10T23:59:59",
        "status": "pending"
    }, headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["priority"] == "high"


def test_get_tasks():
    """测试获取任务列表"""
    # 先登录获取token
    login_response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    
    # 获取任务列表
    response = client.get("/tasks/", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_update_task():
    """测试更新任务功能"""
    # 先登录获取token
    login_response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    
    # 创建一个任务
    create_response = client.post("/tasks/", json={
        "title": "Task to Update",
        "description": "Original description",
        "priority": "medium",
        "due_date": "2024-01-11T23:59:59",
        "status": "pending"
    }, headers={
        "Authorization": f"Bearer {token}"
    })
    task_id = create_response.json()["id"]
    
    # 更新任务
    response = client.put(f"/tasks/{task_id}", json={
        "title": "Updated Task",
        "status": "in_progress"
    }, headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Task"
    assert data["status"] == "in_progress"


def test_delete_task():
    """测试删除任务功能"""
    # 先登录获取token
    login_response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    
    # 创建一个任务
    create_response = client.post("/tasks/", json={
        "title": "Task to Delete",
        "description": "This will be deleted",
        "priority": "low",
        "due_date": "2024-01-12T23:59:59",
        "status": "pending"
    }, headers={
        "Authorization": f"Bearer {token}"
    })
    task_id = create_response.json()["id"]
    
    # 删除任务
    response = client.delete(f"/tasks/{task_id}", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True


def test_get_study_plan():
    """测试获取学习计划"""
    # 先登录获取token
    login_response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    
    # 获取学习计划
    response = client.get("/tasks/study-plan", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert "schedule" in data
