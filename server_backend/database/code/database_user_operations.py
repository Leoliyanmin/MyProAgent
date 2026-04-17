from database.code.database_command import (
    upsert_user,
    get_user,
    list_users,
    delete_user,
    upsert_sync_state,
    get_sync_state,
)
from datetime import datetime
import hashlib
import secrets


class ServerUserOperations:
    """服务端用户相关数据库操作封装"""

    @staticmethod
    def create_user(user_id: str, email: str, username: str, password: str) -> None:
        """创建用户（包含密码加密）"""
        # 生成盐值并加密密码
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        
        now = datetime.utcnow().isoformat()
        upsert_user(
            user_id=user_id,
            username=username,
            user_email=email,
            user_password_hash=password_hash,
            user_salt=salt,
            user_is_active=1,
            user_created_at=now,
            user_last_login=None,
            user_auto_login_token=None,
            user_source_device_id=None,
        )
        # 初始化同步状态
        upsert_sync_state(
            user_id=user_id,
            user_data_updated_at=now,
            user_last_synced_at=None,
            user_version=1,
            sync_updated_at=now,
        )

    @staticmethod
    def get_user_by_id(user_id: str) -> dict | None:
        """通过ID获取用户"""
        return get_user(user_id)

    @staticmethod
    def get_user_by_email(email: str) -> dict | None:
        """通过邮箱获取用户"""
        users = list_users()
        for user in users:
            if user['user_email'] == email:
                return user
        return None

    @staticmethod
    def verify_password(user: dict, password: str) -> bool:
        """验证密码"""
        if not user or 'user_password_hash' not in user or 'user_salt' not in user:
            return False
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            user['user_salt'].encode('utf-8'),
            100000
        ).hex()
        
        return password_hash == user['user_password_hash']

    @staticmethod
    def update_user(user_id: str, update_data: dict) -> None:
        """更新用户信息"""
        user = get_user(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        now = datetime.utcnow().isoformat()
        upsert_user(
            user_id=user_id,
            username=update_data.get('username', user['username']),
            user_email=update_data.get('user_email', user['user_email']),
            user_password_hash=update_data.get('user_password_hash', user['user_password_hash']),
            user_salt=update_data.get('user_salt', user['user_salt']),
            user_is_active=update_data.get('user_is_active', user['user_is_active']),
            user_created_at=user['user_created_at'],
            user_last_login=now,
            user_auto_login_token=update_data.get('user_auto_login_token', user['user_auto_login_token']),
            user_source_device_id=update_data.get('user_source_device_id', user['user_source_device_id']),
        )
        # 更新同步状态
        sync_state = get_sync_state(user_id)
        if sync_state:
            upsert_sync_state(
                user_id=user_id,
                user_data_updated_at=now,
                user_last_synced_at=sync_state['user_last_synced_at'],
                user_version=sync_state['user_version'] + 1,
                sync_updated_at=now,
            )

    @staticmethod
    def delete_user_by_id(user_id: str) -> None:
        """删除用户"""
        delete_user(user_id)