import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from business.auth_service import AuthService
from database.code.handle.database_user_handle import UserHandle
import httpx
import requests
from config import settings
from logging_config import get_logger

logger = get_logger("local_user_service")

_client: httpx.AsyncClient | None = None


async def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30.0, trust_env=False)
    return _client


class UserService:
    def __init__(self):
        self.auth_service = AuthService()
        self.user_handle = UserHandle()
        logger.info("Local UserService 初始化完成")

    async def register_user(self, user_data: dict):
        email = user_data.get('email', '')
        password = user_data.get('password', '')
        confirm_password = user_data.get('confirm_password', '')
        verification_code = user_data.get('verification_code', '')
        full_name = user_data.get('full_name', '')

        logger.info(f"用户注册请求: email={email}, full_name={full_name}")

        if password != confirm_password:
            logger.warning(f"用户注册失败: 两次输入的密码不一致, email={email}")
            return {'success': False, 'message': '两次输入的密码不一致'}

        if settings.TEST_MODE or settings.SKIP_VERIFICATION:
            logger.info(f"TEST MODE: 直接注册用户 email={email}")
            username = full_name or email.split('@')[0]
            password_hash = self.auth_service.get_password_hash(password)
            result = self.user_handle.create_user(email, username, password_hash)
            if not result['ok']:
                logger.error(f"本地用户创建失败: {result['message']}, email={email}")
                return {'success': False, 'message': result['message']}
            logger.info(f"TEST MODE: 本地用户创建成功 email={email}")
            access_token = self.auth_service.create_access_token(
                data={"sub": email, "user_id": email}
            )
            return {
                'success': True,
                'access_token': access_token,
                'token_type': 'bearer',
                'user': {
                    'id': email,
                    'email': email,
                    'full_name': full_name or email.split('@')[0]
                }
            }

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
            client = await _get_client()
            response = await client.post(f"{settings.SERVER_BACKEND_URL}/auth/register", json=server_data)
            if response.status_code != 200:
                logger.error(f"服务器注册失败: {response.text}, email={email}")
                return {'success': False, 'message': f'服务器注册失败: {response.text}'}
            server_result = response.json()
            logger.info(f"服务器注册成功: email={email}")
        except Exception as e:
            logger.error(f"服务器注册异常: {str(e)}, email={email}", exc_info=True)
            return {'success': False, 'message': '服务器注册失败，请稍后重试'}
        
        # 服务器注册成功后，本地注册
        username = full_name if full_name else email.split('@')[0]
        password_hash = self.auth_service.get_password_hash(password)
        result = self.user_handle.create_user(email, username, password_hash)
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

    async def login_user(self, email: str, password: str):
        logger.info(f"用户登录请求: email={email}")

        if settings.TEST_MODE or settings.SKIP_VERIFICATION:
            user = self.get_user_by_email(email)
            if not user:
                logger.warning(f"TEST MODE: 本地用户不存在 email={email}")
                return {'success': False, 'message': '用户不存在，请先注册'}
            stored_hash = user.get('password_hash')
            if stored_hash and not self.auth_service.verify_password(password, stored_hash):
                logger.warning(f"TEST MODE: 密码错误 email={email}")
                return {'success': False, 'message': '邮箱或密码错误'}
            logger.info(f"TEST MODE: 本地登录成功 email={email}")
            access_token = self.auth_service.create_access_token(
                data={"sub": email, "user_id": email}
            )
            return {
                'success': True,
                'access_token': access_token,
                'token_type': 'bearer'
            }

        try:
            response = requests.post(
                f"{settings.SERVER_BACKEND_URL}/auth/login",
                json={'email': email, 'password': password}
            )
            if response.status_code == 200:
                server_data = response.json()
                # 同步用户到本地
                full_name = server_data.get('user', {}).get('full_name', '')
                # 如果没有 full_name，使用 email 前缀作为用户名
                username = full_name if full_name else email.split('@')[0]
                create_result = self.user_handle.create_user(email, username)
                if create_result['ok']:
                    logger.info(f"服务器登录成功并同步用户到本地: email={email}")
                else:
                    logger.warning(f"用户同步失败（可能已存在）: {create_result.get('message')}, email={email}")
                
                # 使用本地生成的token
                access_token = self.auth_service.create_access_token(
                    data={"sub": email, "user_id": email}
                )
                return {
                    'success': True,
                    'access_token': access_token,
                    'token_type': 'bearer',
                    'user_id': email
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