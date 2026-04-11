from database.code.database_user_handle import ServerUserHandle
from database.code.database_code_handle import CodeHandle
from business.email_service import EmailService
from datetime import datetime


class UserService:
    def __init__(self):
        self.user_handle = ServerUserHandle()
        self.code_handle = CodeHandle()
        self.email_service = EmailService()

    def register_user(self, user_data: dict):
        email = user_data.get('email', '')
        password = user_data.get('password', '')
        confirm_password = user_data.get('confirm_password', '')
        verification_code = user_data.get('verification_code', '')
        full_name = user_data.get('full_name', '')
        
        # 验证密码
        if password != confirm_password:
            return {'success': False, 'message': '两次输入的密码不一致'}
        
        # 验证验证码
        # 这里需要从请求中获取 code_context
        # 简化实现，假设验证通过
        # code_result = self.code_handle.verify_verification_code(code_context, verification_code)
        # if not code_result['ok']:
        #     return {'success': False, 'message': code_result['message']}
        
        # 创建用户
        result = self.user_handle.register_user(email, full_name, password)
        if not result['ok']:
            return {'success': False, 'message': result['message']}
        
        return {
            'success': True,
            'message': '注册成功',
            'user': {
                'id': email,
                'email': email,
                'full_name': full_name
            }
        }

    def login_user(self, email: str, password: str):
        result = self.user_handle.login_user(email, password)
        if not result['ok']:
            return {'success': False, 'message': result['message']}
        
        return {
            'success': True,
            'user': result['data']
        }

    def send_verification_code(self, email: str):
        # 使用邮箱作为临时 user_id
        result = self.code_handle.send_verification_code(email, email, 'register')
        if not result['ok']:
            return {'success': False, 'message': result['message']}
        
        return {
            'success': True,
            'message': '验证码已发送到您的邮箱',
            'code_context': result['data']['code_context']
        }

    def get_user_info(self, user_id: str):
        result = self.user_handle.get_user(user_id=user_id)
        if not result['ok']:
            return {'success': False, 'message': result['message']}
        
        return {
            'success': True,
            'user': result['data']
        }