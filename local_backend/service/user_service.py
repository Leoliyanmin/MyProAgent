from business.auth_service import AuthService
from database.code.database_user_handle import UserHandle
import requests
from config import settings


class UserService:
    def __init__(self):
        self.auth_service = AuthService()
        self.user_handle = UserHandle()

    def register_user(self, user_data: dict):
        email = user_data.get('email', '')
        password = user_data.get('password', '')
        confirm_password = user_data.get('confirm_password', '')
        verification_code = user_data.get('verification_code', '')
        full_name = user_data.get('full_name', '')
        
        # 验证数据
        if password != confirm_password:
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
            response = requests.post(f"{settings.SERVER_BACKEND_URL}/auth/register", json=server_data)
            if response.status_code != 200:
                return {'success': False, 'message': f'服务器注册失败: {response.text}'}
            server_result = response.json()
        except Exception as e:
            print(f"Failed to register with server: {e}")
            return {'success': False, 'message': '服务器注册失败，请稍后重试'}
        
        # 服务器注册成功后，本地注册
        result = self.user_handle.create_user(email, full_name)
        if not result['ok']:
            return {'success': False, 'message': result['message']}
        
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
                'full_name': full_name
            }
        }

    def login_user(self, email: str, password: str):
        # 首先尝试本地登录
        user_result = self.user_handle.get_user(email=email)
        if user_result['ok']:
            # 本地用户存在，验证密码（本地不存储密码，直接成功）
            access_token = self.auth_service.create_access_token(
                data={"sub": email, "user_id": email}
            )
            return {
                'success': True,
                'access_token': access_token,
                'token_type': 'bearer'
            }
        
        # 本地登录失败，尝试服务器登录
        try:
            response = requests.post(
                f"{settings.SERVER_BACKEND_URL}/auth/login",
                json={'email': email, 'password': password}
            )
            if response.status_code == 200:
                server_data = response.json()
                # 同步用户到本地
                full_name = server_data.get('user', {}).get('full_name', '')
                self.user_handle.create_user(email, full_name)
                
                # 使用本地生成的token
                access_token = self.auth_service.create_access_token(
                    data={"sub": email, "user_id": email}
                )
                return {
                    'success': True,
                    'access_token': access_token,
                    'token_type': 'bearer'
                }
        except Exception as e:
            print(f"Failed to login with server: {e}")
        
        return {'success': False, 'message': '邮箱或密码错误'}

    def get_user_by_email(self, email: str):
        result = self.user_handle.get_user(email=email)
        return result.get('data') if result['ok'] else None

    def get_user_by_id(self, user_id: str):
        result = self.user_handle.get_user(user_id=user_id)
        return result.get('data') if result['ok'] else None