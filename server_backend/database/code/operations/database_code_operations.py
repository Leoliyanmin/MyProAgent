from server_backend.database.code.command.database_command import (
    create_code,
    get_code_by_context,
    list_codes_by_user,
    mark_code_used,
    delete_code,
    delete_expired_codes,
)
from datetime import datetime, timedelta, timezone
from config import settings
import random
import string


class CodeOperations:
    """验证码相关数据库操作封装"""

    @staticmethod
    def generate_verification_code(length: int = 6) -> str:
        """生成验证码"""
        return ''.join(random.choices(string.digits, k=length))

    @staticmethod
    def create_verification_code(user_id: str, email: str, purpose: str = 'register') -> tuple[str, str]:
        """创建验证码记录"""
        # 生成验证码和上下文
        code = CodeOperations.generate_verification_code()
        code_context = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        
        expire_minutes = getattr(settings, 'VERIFICATION_CODE_EXPIRE_MINUTES', 5)
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)).isoformat()
        created_at = datetime.now(timezone.utc).isoformat()
        
        create_code(
            user_id=user_id,
            code_email=email,
            code_value=code,
            code_context=code_context,
            code_purpose=purpose,
            code_is_used=0,
            code_expires_at=expires_at,
            code_created_at=created_at,
        )
        
        return code, code_context

    @staticmethod
    def verify_code(code_context: str, code: str) -> bool:
        """验证验证码"""
        code_record = get_code_by_context(code_context)
        if not code_record:
            return False
        
        # 检查是否已使用
        if code_record['code_is_used'] == 1:
            return False
        
        # 检查是否过期
        if datetime.now(timezone.utc).isoformat() > code_record['code_expires_at']:
            return False
        
        # 检查验证码是否匹配
        # 注意：实际存储的是验证码本身，需要比较
        # 这里假设 code 字段存储的是验证码
        return code_record.get('code_value') == code

    @staticmethod
    def mark_code_as_used(code_context: str) -> None:
        """标记验证码为已使用"""
        code_record = get_code_by_context(code_context)
        if code_record:
            mark_code_used(code_record['code_id'])

    @staticmethod
    def cleanup_expired_codes() -> None:
        now = datetime.now(timezone.utc).isoformat()
        delete_expired_codes(now)
