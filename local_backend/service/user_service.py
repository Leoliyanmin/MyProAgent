import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from business.auth_service import AuthService
from database.code.database_user_handle import UserHandle
import requests
from config import settings
from logging_config import get_logger

# 创建日志器
logger = get_logger("local_user_service")


class UserService:
    def __init__(self):
        self.auth_service = AuthService()
        self.user_handle = UserHandle()
        logger.info("Local UserService 初始化完成")

    def register_user(self, user_data: dict):
        email = user_data.get('email', '')
        password = user_data.get('password', '')
        confirm_password = user_data.get('confirm_password', '')
        verification_code = user_data.get('verification_code', '')
        full_name = user_data.get('full_name', '')
        
        logger.info(f"用户注册请求: email={email}, full_name={full_name}")
        
        # 验证数据
        if password != confirm_password:
            logger.warning(f"用户注册失败: 两次输入的密码不一致, email={email}")
            return {'success': False, 'message': '两次输入的密码不一致'}
        
        # 先调用服务器注册
        try:
            server_data = {
                'email': email,
                'password': password,
                'confirm_password': confirm_password,
                'verification_code': verification_code,
                'full_name': full_name,
                'student_id': user_data.get('student_id')
            }
            logger.debug(f"向服务器发送注册请求: {settings.SERVER_BACKEND_URL}/auth/register")
            response = requests.post(f"{settings.SERVER_BACKEND_URL}/auth/register", json=server_data)
            if response.status_code != 200:
                logger.error(f"服务器注册失败: {response.text}, email={email}")
                return {'success': False, 'message': f'服务器注册失败: {response.text}'}
            server_result = response.json()
            logger.info(f"服务器注册成功: email={email}")
        except Exception as e:
            logger.error(f"服务器注册异常: {str(e)}, email={email}", exc_info=True)
            return {'success': False, 'message': '服务器注册失败，请稍后重试'}
        
        # 服务器注册成功后，本地注册
        result = self.user_handle.create_user(email, full_name)
        if not result['ok']:
            logger.error(f"本地用户创建失败: {result['message']}, email={email}")
            return {'success': False, 'message': result['message']}
        
        logger.info(f"本地用户创建成功: email={email}")
        
        access_token = self.auth_service.create_access_token(
            data={"sub": email, "user_id": email}
        )
        
        logger.info(f"用户注册完成: email={email}")
        return {
            'success': True,
            'access_token': access_token,
            'token_type': 'bearer',
            'user': {
                'id': email,
                'email': email,
                'full_name': full_name
            }
        }

    def login_user(self, email: str, password: str):
        logger.info(f"用户登录请求: email={email}")
        
        # 首先尝试本地登录
        # user_result = self.user_handle.get_user(email=email)
        # if user_result['ok']:
        #     logger.info(f"本地登录成功: email={email}")
        #     # 本地用户存在，验证密码（本地不存储密码，直接成功）
        #     access_token = self.auth_service.create_access_token(
        #         data={"sub": email, "user_id": email}
        #     )
        #     return {
        #         'success': True,
        #         'access_token': access_token,
        #         'token_type': 'bearer'
        #     }
        
        # logger.debug(f"本地登录失败，尝试服务器登录: email={email}")
        
        # 本地登录失败，尝试服务器登录
        try:
            response = requests.post(
                f"{settings.SERVER_BACKEND_URL}/auth/login",
                json={'email': email, 'password': password}
            )
            if response.status_code == 200:
                server_data = response.json()
                # 同步用户到本地
                full_name = server_data.get('user', {}).get('full_name', '') or email.split('@')[0]
                self.user_handle.create_user(email, full_name)
                logger.info(f"服务器登录成功并同步用户到本地: email={email}")
                
                # 使用本地生成的token
                access_token = self.auth_service.create_access_token(
                    data={"sub": email, "user_id": email}
                )
                return {
                    'success': True,
                    'access_token': access_token,
                    'token_type': 'bearer'
                }
            else:
                logger.warning(f"服务器登录失败: {response.text}, email={email}")
        except Exception as e:
            logger.error(f"服务器登录异常: {str(e)}, email={email}", exc_info=True)
        
        logger.warning(f"用户登录失败: 邮箱或密码错误, email={email}")
        return {'success': False, 'message': '邮箱或密码错误'}

    def get_user_by_email(self, email: str):
        logger.debug(f"获取用户信息(按邮箱): email={email}")
        result = self.user_handle.get_user(email=email)
        if result['ok']:
            logger.debug(f"获取用户信息成功(按邮箱): email={email}")
        else:
            logger.debug(f"获取用户信息失败(按邮箱): {result['message']}, email={email}")
        return result.get('data') if result['ok'] else None

    def get_user_by_id(self, user_id: str):
        logger.debug(f"获取用户信息(按ID): user_id={user_id}")
        result = self.user_handle.get_user(user_id=user_id)
        if result['ok']:
            logger.debug(f"获取用户信息成功(按ID): user_id={user_id}")
        else:
            logger.debug(f"获取用户信息失败(按ID): {result['message']}, user_id={user_id}")
        return result.get('data') if result['ok'] else None