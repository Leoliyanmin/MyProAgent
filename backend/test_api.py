import requests
import json

BASE_URL = "http://localhost:8000"

def test_register():
    """测试用户注册功能"""
    url = f"{BASE_URL}/auth/register"
    data = {
        "email": "test3@mail.sustech.edu.cn",
        "password": "password123",
        "full_name": "Test User",
        "student_id": "20230002"
    }
    response = requests.post(url, json=data)
    print(f"Register response: {response.status_code}")
    print(f"Register text: {response.text}")
    
    if response.status_code != 200:
        print(f"Error: Registration failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    try:
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == "test2@mail.sustech.edu.cn"
        print("Register test passed!")
        return True
    except Exception as e:
        print(f"Error parsing response: {e}")
        return False


def test_login():
    """测试用户登录功能"""
    url = f"{BASE_URL}/auth/login"
    data = {
        "email": "test2@mail.sustech.edu.cn",
        "password": "password123"
    }
    response = requests.post(url, json=data)
    print(f"Login response: {response.status_code}")
    print(f"Login text: {response.text}")
    
    if response.status_code != 200:
        print(f"Error: Login failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    try:
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        print("Login test passed!")
        return data["access_token"]
    except Exception as e:
        print(f"Error parsing response: {e}")
        return None


def test_get_current_user():
    """测试获取当前用户信息"""
    token = test_login()
    if not token:
        print("Skipping get_current_user test due to login failure")
        return
    
    url = f"{BASE_URL}/auth/me"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    print(f"Get user response: {response.status_code}")
    print(f"Get user text: {response.text}")
    
    if response.status_code != 200:
        print(f"Error: Get user failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    try:
        data = response.json()
        assert data["email"] == "test2@mail.sustech.edu.cn"
        print("Get user test passed!")
    except Exception as e:
        print(f"Error parsing response: {e}")


def test_schedules():
    """测试日程管理功能"""
    token = test_login()
    if not token:
        print("Skipping schedules test due to login failure")
        return
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 创建日程
    url = f"{BASE_URL}/schedules/"
    data = {
        "title": "Test Schedule",
        "description": "This is a test schedule",
        "start_time": "2024-01-01T09:00:00",
        "end_time": "2024-01-01T10:00:00",
        "location": "Office",
        "event_type": "personal"
    }
    response = requests.post(url, json=data, headers=headers)
    print(f"Create schedule response: {response.status_code}")
    print(f"Create schedule text: {response.text}")
    
    if response.status_code != 200:
        print(f"Error: Create schedule failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    try:
        result = response.json()
        assert result["success"] == True
        schedule_id = result["schedule"]["id"]
        print("Create schedule test passed!")
    except Exception as e:
        print(f"Error parsing response: {e}")
        return
    
    # 获取日程列表
    url = f"{BASE_URL}/schedules/"
    response = requests.get(url, headers=headers)
    print(f"Get schedules response: {response.status_code}")
    print(f"Get schedules text: {response.text}")
    
    if response.status_code != 200:
        print(f"Error: Get schedules failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    print("Get schedules test passed!")
    
    # 更新日程
    url = f"{BASE_URL}/schedules/{schedule_id}"
    data = {
        "title": "Updated Schedule",
        "description": "Updated description"
    }
    response = requests.put(url, json=data, headers=headers)
    print(f"Update schedule response: {response.status_code}")
    print(f"Update schedule text: {response.text}")
    
    if response.status_code != 200:
        print(f"Error: Update schedule failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    print("Update schedule test passed!")
    
    # 删除日程
    url = f"{BASE_URL}/schedules/{schedule_id}"
    response = requests.delete(url, headers=headers)
    print(f"Delete schedule response: {response.status_code}")
    print(f"Delete schedule text: {response.text}")
    
    if response.status_code != 200:
        print(f"Error: Delete schedule failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    print("Delete schedule test passed!")


def test_tasks():
    """测试任务管理功能"""
    token = test_login()
    if not token:
        print("Skipping tasks test due to login failure")
        return
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 创建任务
    url = f"{BASE_URL}/tasks/"
    data = {
        "title": "Test Task",
        "description": "This is a test task",
        "priority": "high",
        "due_date": "2024-01-10T23:59:59",
        "status": "pending"
    }
    response = requests.post(url, json=data, headers=headers)
    print(f"Create task response: {response.status_code}")
    print(f"Create task text: {response.text}")
    
    if response.status_code != 200:
        print(f"Error: Create task failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    try:
        result = response.json()
        assert result["success"] == True
        task_id = result["task"]["id"]
        print("Create task test passed!")
    except Exception as e:
        print(f"Error parsing response: {e}")
        return
    
    # 获取任务列表
    url = f"{BASE_URL}/tasks/"
    response = requests.get(url, headers=headers)
    print(f"Get tasks response: {response.status_code}")
    print(f"Get tasks text: {response.text}")
    
    if response.status_code != 200:
        print(f"Error: Get tasks failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    print("Get tasks test passed!")
    
    # 更新任务
    url = f"{BASE_URL}/tasks/{task_id}"
    data = {
        "title": "Updated Task",
        "status": "in_progress"
    }
    response = requests.put(url, json=data, headers=headers)
    print(f"Update task response: {response.status_code}")
    print(f"Update task text: {response.text}")
    
    if response.status_code != 200:
        print(f"Error: Update task failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    print("Update task test passed!")
    
    # 删除任务
    url = f"{BASE_URL}/tasks/{task_id}"
    response = requests.delete(url, headers=headers)
    print(f"Delete task response: {response.status_code}")
    print(f"Delete task text: {response.text}")
    
    if response.status_code != 200:
        print(f"Error: Delete task failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    print("Delete task test passed!")
    
    # 获取学习计划
    url = f"{BASE_URL}/tasks/study-plan"
    response = requests.get(url, headers=headers)
    print(f"Get study plan response: {response.status_code}")
    print(f"Get study plan text: {response.text}")
    
    if response.status_code != 200:
        print(f"Error: Get study plan failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    print("Get study plan test passed!")


def test_agent():
    """测试Agent交互功能"""
    token = test_login()
    if not token:
        print("Skipping agent test due to login failure")
        return
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 与Agent聊天
    url = f"{BASE_URL}/agent/chat"
    data = {
        "message": "Hello, what can you do?",
        "session_id": "test_session_123"
    }
    response = requests.post(url, json=data, headers=headers)
    print(f"Agent chat response: {response.status_code}")
    print(f"Agent chat text: {response.text}")
    
    if response.status_code != 200:
        print(f"Error: Agent chat failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    print("Agent chat test passed!")
    
    # 获取聊天历史
    url = f"{BASE_URL}/agent/history/test_session_123"
    response = requests.get(url, headers=headers)
    print(f"Get chat history response: {response.status_code}")
    print(f"Get chat history text: {response.text}")
    
    if response.status_code != 200:
        print(f"Error: Get chat history failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    print("Get chat history test passed!")


if __name__ == "__main__":
    print("Running tests...")
    print("=" * 50)
    
    test_register()
    print("=" * 50)
    
    test_login()
    print("=" * 50)
    
    test_get_current_user()
    print("=" * 50)
    
    test_schedules()
    print("=" * 50)
    
    test_tasks()
    print("=" * 50)
    
    test_agent()
    print("=" * 50)
    
    print("All tests completed!")
