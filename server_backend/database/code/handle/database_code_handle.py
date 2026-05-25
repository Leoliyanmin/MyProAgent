import logging
from database.code.operations.database_code_operations import CodeOperations

logger = logging.getLogger(__name__)


class CodeHandle:
    """服务端验证码功能调用入口"""

    def __init__(self):
        self.operations = CodeOperations()

    def send_verification_code(self, user_id: str, email: str, purpose: str = 'register') -> dict:
        """发送验证码入口"""
        if not user_id or not email:
            return {'ok': False, 'status': 400, 'message': 'user_id 和 email 不能为空'}

        try:
            self.operations.cleanup_expired_codes()

            code, code_context = self.operations.create_verification_code(
                user_id=user_id,
                email=email,
                purpose=purpose,
            )

            logger.info("验证码已创建 (邮箱: %s, 用途: %s)", email, purpose)

            return {
                'ok': True,
                'status': 200,
                'data': {
                    'code': code,
                    'code_context': code_context,
                    'message': '验证码已创建'
                }
            }
        except Exception as e:
            logger.error("发送验证码失败: %s", e)
            return {'ok': False, 'status': 500, 'message': f'发送验证码失败: {str(e)}'}

    def verify_verification_code(self, code_context: str, code: str) -> dict:
        """验证验证码入口"""
        if not code_context or not code:
            return {'ok': False, 'status': 400, 'message': 'code_context 和 code 不能为空'}

        try:
            self.operations.cleanup_expired_codes()

            if not self.operations.verify_code(code_context, code):
                return {'ok': False, 'status': 400, 'message': '验证码无效或已过期'}

            self.operations.mark_code_as_used(code_context)

            return {'ok': True, 'status': 200, 'message': '验证码验证成功'}
        except Exception as e:
            logger.error("验证验证码失败: %s", e)
            return {'ok': False, 'status': 500, 'message': f'验证验证码失败: {str(e)}'}