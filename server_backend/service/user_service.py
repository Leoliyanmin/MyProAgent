from business.auth_service import AuthService
from database.repositories import UserRepository


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
        
        user_data['hashed_password'] = self.auth_service.get_password_hash(user_data.pop('password'))
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
