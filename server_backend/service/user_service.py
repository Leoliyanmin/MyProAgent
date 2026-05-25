import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.code.handle.database_user_handle import ServerUserHandle
from database.code.handle.database_code_handle import CodeHandle
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
        username = user_data.get('username', '')
        
        logger.info(f"用户注册请求: email={email}, full_name={full_name}, username={username}")
        
        # 验证密码
        if password != confirm_password:
            logger.warning(f"用户注册失败: 两次输入的密码不一致, email={email}")
            return {'success': False, 'message': '两次输入的密码不一致'}
        
        # 验证验证码
        code_context = user_data.get('code_context', '')
        if not code_context:
            return {'success': False, 'message': '缺少验证码上下文（code_context），请先获取验证码'}
        code_result = self.code_handle.verify_verification_code(code_context, verification_code)
        if not code_result['ok']:
            return {'success': False, 'message': code_result['message']}
        
        # 使用 username 或 email 作为用户名
        user_name = username if username else email.split('@')[0]
        
        # 创建用户
        result = self.user_handle.register_user(email, user_name, password)
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

    async def send_verification_code(self, email: str):
        logger.info(f"发送验证码请求: email={email}")

        # 使用占位 user_id（用户尚未注册）
        result = self.code_handle.send_verification_code("_pending_registration", email, 'register')
        if not result['ok']:
            logger.error(f"发送验证码失败: {result['message']}, email={email}")
            return {'success': False, 'message': result['message']}

        code = result['data']['code']
        code_context = result['data']['code_context']

        # 异步发送邮件（失败不影响流程）
        if not settings.TEST_MODE:
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(self._send_email_async(email, code))
            except Exception as e:
                logger.warning(f"邮件发送调度失败（非致命）: {email} - {e}")

        return {
            'success': True,
            'message': '验证码已生成',
            'code_context': code_context,
            'test_code': code,
            'expires_in': 300,
        }

    async def _send_email_async(self, email: str, code: str):
        """Fire-and-forget 邮件发送，不阻塞主请求"""
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None, self.email_service.send_verification_email, email, code, 'register'
            )
            logger.info(f"验证码邮件已发送: email={email}")
        except Exception as e:
            logger.warning(f"验证码邮件发送失败（非致命）: {email} - {e}")

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