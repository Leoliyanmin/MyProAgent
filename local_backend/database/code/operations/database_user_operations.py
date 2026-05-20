from local_backend.database.code.command.database_command import (
    upsert_user,
    get_user,
    list_users,
    delete_user,
    set_user_password,
    upsert_sync_state,
    get_sync_state,
)
from datetime import datetime


class UserOperations:
    """用户相关数据库操作封装"""

    @staticmethod
    def create_user(user_id: str, email: str, username: str, password_hash: str = None) -> None:
        """创建用户"""
        now = datetime.utcnow().isoformat()
        upsert_user(
            user_id=user_id,
            username=username,
            user_email=email,
            user_is_active=1,
            user_created_at=now,
            user_last_login=None,
            user_source_device_id=None,
        )
        if password_hash is not None:
            set_user_password(user_id, password_hash)
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
            user_is_active=update_data.get('user_is_active', user['user_is_active']),
            user_created_at=user['user_created_at'],
            user_last_login=now,
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