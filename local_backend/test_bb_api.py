import requests
import json
import sys
import os

BASE_URL = "http://localhost:8002"
TEST_USER_ID = "local_test_user@mail.sustech.edu.cn"
TEST_EMAIL = "local_test_user@mail.sustech.edu.cn"
TEST_PASSWORD = "Password123"

# 全局变量存储token
ACCESS_TOKEN = None

def print_response(response):
    """打印响应信息"""
    print(f"\n状态码: {response.status_code}")
    try:
        data = response.json()
        print(f"响应内容: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data
    except:
        print(f"响应内容: {response.text}")
        return None

def get_auth_headers():
    """获取认证请求头"""
    if ACCESS_TOKEN:
        return {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    return {}

def test_send_verification_code():
    """测试发送验证码"""
    print("\n" + "="*60)
    print("测试: 发送验证码")
    print("="*60)
    
    url = f"{BASE_URL}/auth/verification-code"
    data = {
        "email": TEST_EMAIL,
        "purpose": "register"
    }
    
    try:
        response = requests.post(url, json=data)
        data = print_response(response)
        
        if data and data.get('success'):
            print("✓ 发送验证码成功")
            return True
        else:
            print("✗ 发送验证码失败")
            return False
            
    except Exception as e:
        print(f"✗ 请求失败: {str(e)}")
        return False

def test_register():
    """测试用户注册"""
    print("\n" + "="*60)
    print("测试: 用户注册")
    print("="*60)
    
    # 先尝试登录，如果能登录说明用户已存在
    if try_login():
        print("✓ 用户已存在，跳过注册")
        return True
        
    # 需要注册，先获取验证码
    if not test_send_verification_code():
        print("✗ 获取验证码失败")
        return False
        
    # 输入验证码（开发环境默认验证码通常是固定的）
    verification_code = input("请输入收到的验证码: ").strip()
    
    url = f"{BASE_URL}/auth/register"
    data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "confirm_password": TEST_PASSWORD,
        "name": "Blackboard Test User",
        "verification_code": verification_code
    }
    
    try:
        response = requests.post(url, json=data)
        data = print_response(response)
        
        if data and data.get('success'):
            print("✓ 注册成功")
            return True
        else:
            print("✗ 注册失败")
            return False
            
    except Exception as e:
        print(f"✗ 请求失败: {str(e)}")
        return False

def try_login():
    """尝试登录，检查用户是否已存在"""
    url = f"{BASE_URL}/auth/login"
    data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            data = response.json()
            global ACCESS_TOKEN
            ACCESS_TOKEN = data.get('access_token')
            return True
        return False
    except:
        return False

def test_login():
    """测试用户登录"""
    global ACCESS_TOKEN
    
    print("\n" + "="*60)
    print("测试: 用户登录")
    print("="*60)
    
    url = f"{BASE_URL}/auth/login"
    data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(url, json=data)
        data = print_response(response)
        
        if data and data.get('success'):
            ACCESS_TOKEN = data.get('access_token')
            print("✓ 登录成功")
            print(f"  - Access Token: {ACCESS_TOKEN[:20]}...")
            return True
        else:
            print("✗ 登录失败")
            return False
            
    except Exception as e:
        print(f"✗ 请求失败: {str(e)}")
        return False

def test_blackboard_status():
    """测试获取Blackboard绑定状态"""
    print("\n" + "="*60)
    print("测试: 获取Blackboard绑定状态")
    print("="*60)
    
    url = f"{BASE_URL}/api/v1/blackboard/status"
    headers = get_auth_headers()
    
    try:
        response = requests.get(url, headers=headers)
        data = print_response(response)
        
        if data and data.get('success'):
            print("✓ 获取状态成功")
            print(f"  - 是否已绑定: {data.get('is_bound', False)}")
            if data.get('username'):
                print(f"  - 绑定的用户名: {data.get('username')}")
            if data.get('last_sync_time'):
                print(f"  - 最后同步时间: {data.get('last_sync_time')}")
        else:
            print("✗ 获取状态失败")
            
    except Exception as e:
        print(f"✗ 请求失败: {str(e)}")

def test_blackboard_bind():
    """测试发起Blackboard绑定"""
    print("\n" + "="*60)
    print("测试: 发起Blackboard绑定")
    print("="*60)
    
    url = f"{BASE_URL}/api/v1/blackboard/bind"
    headers = get_auth_headers()
    
    try:
        response = requests.post(url, headers=headers)
        data = print_response(response)
        
        if data and data.get('success'):
            print("✓ 发起绑定成功")
            print(f"  - CAS登录URL: {data.get('cas_login_url')}")
            print(f"  - State: {data.get('state')}")
            return data
        else:
            print("✗ 发起绑定失败")
            return None
            
    except Exception as e:
        print(f"✗ 请求失败: {str(e)}")
        return None

def test_blackboard_callback():
    """测试CAS回调（模拟）"""
    print("\n" + "="*60)
    print("测试: CAS回调（模拟）")
    print("="*60)
    
    # 注意：真实的CAS回调需要有效的ticket，这里仅测试接口格式
    url = f"{BASE_URL}/api/v1/blackboard/callback"
    params = {
        "ticket": "ST-TEST-TICKET",
        "state": "test-state-123",
        "user_id": TEST_USER_ID
    }
    
    try:
        response = requests.get(url, params=params)
        print(f"状态码: {response.status_code}")
        print(f"重定向位置: {response.headers.get('Location', '无')}")
        
        if response.status_code in [302, 301]:
            print("✓ 回调接口正常工作（重定向）")
        else:
            print("✗ 回调接口可能有问题")
            
    except Exception as e:
        print(f"✗ 请求失败: {str(e)}")

def test_blackboard_sync():
    """测试手动同步Blackboard数据"""
    print("\n" + "="*60)
    print("测试: 手动同步Blackboard数据")
    print("="*60)
    
    url = f"{BASE_URL}/api/v1/blackboard/sync"
    headers = get_auth_headers()
    
    try:
        response = requests.post(url, headers=headers)
        data = print_response(response)
        
        if data and data.get('success'):
            print("✓ 同步成功")
            print(f"  - 同步消息: {data.get('message')}")
            if data.get('synced_courses'):
                print(f"  - 同步课程数: {len(data.get('synced_courses', []))}")
            if data.get('synced_assignments'):
                print(f"  - 同步作业数: {len(data.get('synced_assignments', []))}")
        else:
            print("✗ 同步失败")
            
    except Exception as e:
        print(f"✗ 请求失败: {str(e)}")

def test_blackboard_unbind():
    """测试解绑Blackboard账号"""
    print("\n" + "="*60)
    print("测试: 解绑Blackboard账号")
    print("="*60)
    
    url = f"{BASE_URL}/api/v1/blackboard/unbind"
    headers = get_auth_headers()
    
    try:
        response = requests.post(url, headers=headers)
        data = print_response(response)
        
        if data and data.get('success'):
            print("✓ 解绑成功")
        else:
            print("✗ 解绑失败")
            
    except Exception as e:
        print(f"✗ 请求失败: {str(e)}")

def main():
    """主测试函数"""
    print("\n" + "="*80)
    print("Blackboard API 测试套件")
    print("="*80)
    print(f"测试地址: {BASE_URL}")
    print(f"测试用户: {TEST_EMAIL}")
    print("="*80)
    '''
    # 1. 注册用户
    if not test_register():
        print("✗ 注册失败，退出测试")
        return
    '''
    # 2. 登录获取token
    if not test_login():
        print("✗ 登录失败，退出测试")
        return
    
    # 3. Blackboard相关测试
    test_blackboard_status()    # 获取绑定状态
    bind_result = test_blackboard_bind()  # 发起绑定
    # test_blackboard_callback() # CAS回调（需要真实ticket）
    test_blackboard_sync()      # 同步数据（模拟）
    # test_blackboard_unbind()   # 解绑（按需测试）
    
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)

if __name__ == "__main__":
    main()
