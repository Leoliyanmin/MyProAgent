from business.auth_service import AuthService
from database.repositories import UserRepository
import requests
from config import settings


class UserService:
    def __init__(self):
        self.auth_service = AuthService()
        self.user_repo = UserRepository()

    def register_user(self, user_data: dict):
        if not self.auth_service.validate_email(user_data.get('email', '')):
            return {'success': False, 'message': 'Invalid email domain'}
        
        existing_user = self.user_repo.get_user_by_email(user_data['email'])
        if existing_user:
            return {'success': False, 'message': 'User already exists'}
        
        # 本地注册
        user_data['hashed_password'] = self.auth_service.get_password_hash(user_data.pop('password'))
        user = self.user_repo.create_user(user_data)
        
        # 同步到服务器
        try:
            server_data = {
                'email': user_data['email'],
                'password': user_data.get('password'),  # 注意：这里需要处理密码同步
                'full_name': user_data.get('full_name'),
                'student_id': user_data.get('student_id')
            }
            response = requests.post(f"{settings.SERVER_BACKEND_URL}/auth/register", json=server_data)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to sync user to server: {e}")
            # 即使服务器同步失败，本地注册仍成功
        
        return {
            'success': True,
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
