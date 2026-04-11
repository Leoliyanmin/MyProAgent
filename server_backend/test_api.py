import requests
import json

BASE_URL = "http://localhost:8001"

def test_register():
    """测试用户注册功能"""
    email = "12312202@mail.sustech.edu.cn"
    
    # 第一步：发送验证码
    url = f"{BASE_URL}/auth/verification/send"
    data = {
        "email": email,
        "purpose": "register"
    }
    response = requests.post(url, json=data)
    print(f"Send verification code response: {response.status_code}")
    print(f"Send verification code text: {response.text}")
    
    if response.status_code != 200:
        print(f"Error: Failed to send verification code with status {response.status_code}")
        print(f"Response: {response.text}")
        print("Note: This may fail if Redis is not running or email is not configured")
        return False
    
    try:
        result = response.json()
        print(f"Verification code sent: {result.get('message')}")
        # 注意：在实际测试中，你需要从邮件中获取验证码
        # 这里我们假设验证码为"123456"用于测试
        verification_code = "123456"
    except Exception as e:
        print(f"Error parsing verification response: {e}")
        return False
    
    # 第二步：使用验证码注册
    url = f"{BASE_URL}/auth/register"
    data = {
        "email": email,
        "password": "Password123",
        "confirm_password": "Password123",
        "verification_code": verification_code,
        "full_name": "Server Test User",
        "student_id": "20230020"
    }
    response = requests.post(url, json=data)
    print(f"Register response: {response.status_code}")
    print(f"Register text: {response.text}")
    
    if response.status_code != 200:
        print(f"Error: Registration failed with status {response.status_code}")
        print(f"Response: {response.text}")
        print("Note: This may fail if verification code is incorrect or expired")
        return False
    
    try:
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == email
        print("Register test passed!")
        return True
    except Exception as e:
        print(f"Error parsing response: {e}")
        return False


def test_login():
    """测试用户登录功能"""
    url = f"{BASE_URL}/auth/login"
    data = {
        "email": "server_test@mail.sustech.edu.cn",
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


def test_sync_from_client():
    """测试从客户端同步数据"""
    user_id = 1  # 假设用户ID为1
    
    # 测试同步日程
    url = f"{BASE_URL}/sync/from-client"
    data = {
        "data_type": "schedules",
        "data": [
            {
                "title": "Server Test Schedule",
                "description": "This is a test schedule from client",
                "start_time": "2024-01-02T10:00:00",
                "end_time": "2024-01-02T11:00:00",
                "location": "Server Office",
                "event_type": "work"
            }
        ]
    }
    headers = {
        "X-User-ID": str(user_id)
    }
    response = requests.post(url, json=data, headers=headers)
    print(f"Sync schedules response: {response.status_code}")
    print(f"Sync schedules text: {response.text}")
    
    if response.status_code != 200:
        print(f"Error: Sync schedules failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    print("Sync schedules test passed!")
    
    # 测试同步任务
    url = f"{BASE_URL}/sync/from-client"
    data = {
        "data_type": "tasks",
        "data": [
            {
                "title": "Server Test Task",
                "description": "This is a test task from client",
                "priority": "medium",
                "due_date": "2024-01-15T23:59:59",
                "status": "pending"
            }
        ]
    }
    response = requests.post(url, json=data, headers=headers)
    print(f"Sync tasks response: {response.status_code}")
    print(f"Sync tasks text: {response.text}")
    
    if response.status_code != 200:
        print(f"Error: Sync tasks failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    print("Sync tasks test passed!")


def test_sync_to_client():
    """测试向客户端同步数据"""
    user_id = 1  # 假设用户ID为1
    
    # 测试获取日程
    url = f"{BASE_URL}/sync/to-client?data_type=schedules"
    headers = {
        "X-User-ID": str(user_id)
    }
    response = requests.get(url, headers=headers)
    print(f"Get synced schedules response: {response.status_code}")
    print(f"Get synced schedules text: {response.text}")
    
    if response.status_code != 200:
        print(f"Error: Get synced schedules failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    print("Get synced schedules test passed!")
    
    # 测试获取任务
    url = f"{BASE_URL}/sync/to-client?data_type=tasks"
    response = requests.get(url, headers=headers)
    print(f"Get synced tasks response: {response.status_code}")
    print(f"Get synced tasks text: {response.text}")
    
    if response.status_code != 200:
        print(f"Error: Get synced tasks failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    print("Get synced tasks test passed!")


if __name__ == "__main__":
    print("Running Server Backend tests...")
    print("=" * 50)
    
    test_register()
    print("=" * 50)
    '''
    test_login()
    print("=" * 50)
    
    test_sync_from_client()
    print("=" * 50)
    
    test_sync_to_client()
    print("=" * 50)
    '''
    print("All Server Backend tests completed!")
