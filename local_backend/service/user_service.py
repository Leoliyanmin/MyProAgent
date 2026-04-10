from business.auth_service import AuthService
from database.repositories import UserRepository
import requests
from config import settings


class UserService:
    def __init__(self):
        self.auth_service = AuthService()
        self.user_repo = UserRepository()

    def register_user(self, user_data: dict):
        email = user_data.get('email', '')
        password = user_data.get('password', '')
        confirm_password = user_data.get('confirm_password', '')
        verification_code = user_data.get('verification_code', '')
        
        validation = self.auth_service.validate_registration_data(email, password, confirm_password, verification_code)
        if not validation['valid']:
            return {'success': False, 'message': validation['message']}
        
        existing_user = self.user_repo.get_user_by_email(email)
        if existing_user:
            return {'success': False, 'message': '邮箱已被注册'}
        
        # 先调用服务器注册，验证验证码
        try:
            server_data = {
                'email': email,
                'password': password,
                'confirm_password': confirm_password,
                'verification_code': verification_code,
                'full_name': user_data.get('full_name'),
                'student_id': user_data.get('student_id')
            }
            response = requests.post(f"{settings.SERVER_BACKEND_URL}/auth/register", json=server_data)
            if response.status_code == 200:
                server_result = response.json()
            else:
                return {'success': False, 'message': f'服务器注册失败: {response.text}'}
        except Exception as e:
            print(f"Failed to register with server: {e}")
            return {'success': False, 'message': '服务器注册失败，请稍后重试'}
        
        # 服务器注册成功后，本地注册
        user_data['hashed_password'] = self.auth_service.get_password_hash(password)
        user_data.pop('password', None)
        user_data.pop('confirm_password', None)
        user_data.pop('verification_code', None)
        
        user = self.user_repo.create_user(user_data)
        
        access_token = self.auth_service.create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )
        
        return {
            'success': True,
            'access_token': access_token,
            'token_type': 'bearer',
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'student_id': user.student_id
            }
        }

    def login_user(self, email: str, password: str):
        # 首先尝试本地登录
        user = self.user_repo.get_user_by_email(email)
        if user and self.auth_service.verify_password(password, user.hashed_password):
            access_token = self.auth_service.create_access_token(
                data={"sub": user.email, "user_id": user.id}
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
                user_data = {
                    'email': email,
                    'hashed_password': self.auth_service.get_password_hash(password),
                    'full_name': server_data.get('user', {}).get('full_name'),
                    'student_id': server_data.get('user', {}).get('student_id')
                }
                existing_user = self.user_repo.get_user_by_email(email)
                if existing_user:
                    self.user_repo.update_user(existing_user.id, user_data)
                else:
                    self.user_repo.create_user(user_data)
                
                # 使用本地生成的token
                local_user = self.user_repo.get_user_by_email(email)
                access_token = self.auth_service.create_access_token(
                    data={"sub": local_user.email, "user_id": local_user.id}
                )
                return {
                    'success': True,
                    'access_token': access_token,
                    'token_type': 'bearer'
                }
        except Exception as e:
            print(f"Failed to login with server: {e}")
        
        return {'success': False, 'message': 'Incorrect email or password'}

    def get_user_by_email(self, email: str):
        return self.user_repo.get_user_by_email(email)

    def get_user_by_id(self, user_id: int):
        return self.user_repo.get_user_by_id(user_id)
