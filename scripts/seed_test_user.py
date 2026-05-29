"""种子数据：在 local_backend 数据库中创建 MVP 测试用户
用法（在项目根目录）：
    python seed_test_user.py
"""
import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'local_backend'))

from database.code.init.database_init import init_database
from database.code.handle.database_user_handle import UserHandle
from business.auth_service import AuthService

TEST_EMAIL = "local_test_user@mail.sustech.edu.cn"
TEST_NAME = "MVP Test User"
TEST_PASSWORD = "Password123"

auth = AuthService()

print("正在初始化数据库...")
init_database()
print("数据库初始化完成")

handle = UserHandle()
password_hash = auth.get_password_hash(TEST_PASSWORD)
result = handle.create_user(TEST_EMAIL, TEST_NAME, password_hash)
if result['ok']:
    print(f"测试用户创建成功: {TEST_EMAIL}")
elif '已存在' in result.get('message', ''):
    print(f"测试用户已存在: {TEST_EMAIL}")
else:
    print(f"创建失败: {result['message']}")
    sys.exit(1)

user = handle.get_user(email=TEST_EMAIL)
if user['ok']:
    print("用户可以正常查询，请使用以下凭据登录：")
    print(f"  邮箱: {TEST_EMAIL}")
    print(f"  密码: {TEST_PASSWORD}")
