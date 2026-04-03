from layers.database.repositories import UserRepository
from layers.business.auth_service import AuthService


class UserService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.auth_service = AuthService()

    def register_user(self, user_data: dict):
        if not self.auth_service.validate_email(user_data.get('email', '')):
            return {'success': False, 'message': 'Invalid email domain'}
        
        existing_user = self.user_repo.get_user_by_email(user_data['email'])
        if existing_user:
            return {'success': False, 'message': 'User already exists'}
        
        user_data['hashed_password'] = self.auth_service.hash_password(user_data.pop('password'))
        user = self.user_repo.create_user(user_data)
        
        return {
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'student_id': user.student_id
            }
        }

    def authenticate_user(self, email: str, password: str):
        user = self.user_repo.get_user_by_email(email)
        if not user:
            return {'success': False, 'message': 'User not found'}
        
        if not self.auth_service.verify_password(password, user.hashed_password):
            return {'success': False, 'message': 'Invalid password'}
        
        if not user.is_active:
            return {'success': False, 'message': 'User is inactive'}
        
        token = self.auth_service.create_access_token({'sub': user.email, 'user_id': user.id})
        
        return {
            'success': True,
            'access_token': token,
            'token_type': 'bearer',
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'student_id': user.student_id
            }
        }

    def get_user_profile(self, user_id: int):
        user = self.user_repo.get_user_by_id(user_id)
        if user:
            return {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'student_id': user.student_id,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat()
            }
        return None
