"""种子数据：在 local_backend 数据库中创建 MVP 测试用户
用法（在项目根目录）：
    python seed_test_user.py
"""
import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'local_backend'))

from database.code.database_init import init_database
from database.code.database_user_handle import UserHandle

TEST_EMAIL = "local_test_user@mail.sustech.edu.cn"
TEST_NAME = "MVP Test User"

# 1. 初始化数据库
print("正在初始化数据库...")
init_database()
print("数据库初始化完成")

# 2. 创建用户（如果已存在则忽略）
handle = UserHandle()
result = handle.create_user(TEST_EMAIL, TEST_NAME)
if result['ok']:
    print(f"测试用户创建成功: {TEST_EMAIL}")
elif '已存在' in result.get('message', ''):
    print(f"测试用户已存在: {TEST_EMAIL}")
else:
    print(f"创建失败: {result['message']}")
    sys.exit(1)

# 3. 验证
user = handle.get_user(email=TEST_EMAIL)
if user['ok']:
    print("用户可以正常查询，请使用以下凭据登录：")
    print(f"  邮箱: {TEST_EMAIL}")
    print(f"  密码: Password123（TEST_MODE 下无需密码校验）")
