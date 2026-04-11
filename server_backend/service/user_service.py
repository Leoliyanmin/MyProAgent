from business.auth_service import AuthService
from database.repositories import UserRepository
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
        
        # 验证注册数据（不包括验证码验证）
        validation = self.auth_service.validate_registration_data(email, password, confirm_password, verification_code)
        if not validation['valid']:
            return {'success': False, 'message': validation['message']}
        
        existing_user = self.user_repo.get_user_by_email(email)
        if existing_user:
            return {'success': False, 'message': '邮箱已被注册'}
        
        # 检查是否跳过验证码验证
        if not settings.SKIP_VERIFICATION:
            if not self.auth_service.verify_registration_code(email, verification_code):
                return {'success': False, 'message': '验证码错误或已过期'}
        else:
            print("跳过验证码验证模式：直接进行注册")
        
        user_data['hashed_password'] = self.auth_service.get_password_hash(password)
        user_data.pop('password', None)
        user_data.pop('confirm_password', None)
        user_data.pop('verification_code', None)
        
        user = self.user_repo.create_user(user_data)
        
        if not user:
            return {'success': False, 'message': '创建用户失败，请稍后重试'}
        
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
        user = self.user_repo.get_user_by_email(email)
        if not user:
            return {'success': False, 'message': 'User not found'}
        
        if not self.auth_service.verify_password(password, user.hashed_password):
            return {'success': False, 'message': 'Incorrect password'}
        
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

    def get_user_by_email(self, email: str):
        return self.user_repo.get_user_by_email(email)

    def get_user_by_id(self, user_id: int):
        return self.user_repo.get_user_by_id(user_id)