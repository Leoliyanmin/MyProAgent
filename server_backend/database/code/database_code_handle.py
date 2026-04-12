from database.code.database_code_operations import CodeOperations


class CodeHandle:
    """服务端验证码功能调用入口"""

    def __init__(self):
        self.operations = CodeOperations()

    def send_verification_code(self, user_id: str, email: str, purpose: str = 'register') -> dict:
        """发送验证码入口"""
        # 验证输入
        if not user_id or not email:
            return {'ok': False, 'status': 400, 'message': 'user_id 和 email 不能为空'}
        
        try:
            # 清理过期验证码
            self.operations.cleanup_expired_codes()
            
            # 创建验证码
            code, code_context = self.operations.create_verification_code(
                user_id=user_id,
                email=email,
                purpose=purpose,
            )
            
            # 这里应该调用邮件服务发送验证码
            # 实际实现时需要集成邮件发送功能
            print(f"Verification code for {email}: {code}")
            
            return {
                'ok': True,
                'status': 200,
                'data': {
                    'code_context': code_context,
                    'message': '验证码已发送'
                }
            }
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'发送验证码失败: {str(e)}'}

    def verify_verification_code(self, code_context: str, code: str) -> dict:
        """验证验证码入口"""
        # 验证输入
        if not code_context or not code:
            return {'ok': False, 'status': 400, 'message': 'code_context 和 code 不能为空'}
        
        try:
            # 清理过期验证码
            self.operations.cleanup_expired_codes()
            
            # 验证验证码
            if not self.operations.verify_code(code_context, code):
                return {'ok': False, 'status': 400, 'message': '验证码无效或已过期'}
            
            # 标记为已使用
            self.operations.mark_code_as_used(code_context)
            
            return {'ok': True, 'status': 200, 'message': '验证码验证成功'}
        except Exception as e:
            return {'ok': False, 'status': 500, 'message': f'验证验证码失败: {str(e)}'}