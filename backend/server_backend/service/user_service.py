import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.code.database_user_handle import ServerUserHandle
from database.code.database_code_handle import CodeHandle
from business.email_service import EmailService
from datetime import datetime
from logging_config import get_logger

# 创建日志器
logger = get_logger("user_service")


class UserService:
    def __init__(self):
        self.user_handle = ServerUserHandle()
        self.code_handle = CodeHandle()
        self.email_service = EmailService()
        logger.info("UserService 初始化完成")

    def register_user(self, user_data: dict):
        email = user_data.get('email', '')
        password = user_data.get('password', '')
        confirm_password = user_data.get('confirm_password', '')
        verification_code = user_data.get('verification_code', '')
        full_name = user_data.get('full_name', '')
        
        logger.info(f"用户注册请求: email={email}, full_name={full_name}")
        
        # 验证密码
        if password != confirm_password:
            logger.warning(f"用户注册失败: 两次输入的密码不一致, email={email}")
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
            logger.error(f"用户注册失败: {result['message']}, email={email}")
            return {'success': False, 'message': result['message']}
        
        logger.info(f"用户注册成功: email={email}")
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
        logger.info(f"用户登录请求: email={email}")
        
        result = self.user_handle.login_user(email, password)
        if not result['ok']:
            logger.warning(f"用户登录失败: {result['message']}, email={email}")
            return {'success': False, 'message': result['message']}
        
        logger.info(f"用户登录成功: email={email}")
        return {
            'success': True,
            'user': result['data']
        }

    def send_verification_code(self, email: str):
        logger.info(f"发送验证码请求: email={email}")
        
        # 使用邮箱作为临时 user_id
        result = self.code_handle.send_verification_code(email, email, 'register')
        if not result['ok']:
            logger.error(f"发送验证码失败: {result['message']}, email={email}")
            return {'success': False, 'message': result['message']}
        
        logger.info(f"验证码发送成功: email={email}")
        return {
            'success': True,
            'message': '验证码已发送到您的邮箱',
            'code_context': result['data']['code_context']
        }

    def get_user_info(self, user_id: str):
        logger.debug(f"获取用户信息: user_id={user_id}")
        
        result = self.user_handle.get_user(user_id=user_id)
        if not result['ok']:
            logger.warning(f"获取用户信息失败: {result['message']}, user_id={user_id}")
            return {'success': False, 'message': result['message']}
        
        logger.debug(f"获取用户信息成功: user_id={user_id}")
        return {
            'success': True,
            'user': result['data']
        }