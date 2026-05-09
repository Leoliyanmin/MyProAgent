from local_backend.database.code.command.database_command import (
    create_account,
    list_accounts_by_user,
    update_account_sync_time,
    delete_account,
)
from typing import Optional, Dict
import time


class TisAccountOperations:
    def create_or_update_tis_account(
        self,
        user_id: str,
        student_id: str,
        encrypted_cookie: str,
        bind_time: Optional[str] = None,
        last_sync_time: Optional[str] = None,
    ) -> int:
        existing_accounts = list_accounts_by_user(user_id)
        tis_account = None
        for account in existing_accounts:
            if account['account_platform_type'] == 'tis':
                tis_account = account
                break
        if tis_account:
            delete_account(tis_account['account_id'])
        if not bind_time:
            bind_time = time.strftime('%Y-%m-%d %H:%M:%S')
        return create_account(
            user_id=user_id,
            account_platform_type='tis',
            account_platform_username=student_id,
            content=encrypted_cookie,
            account_bind_time=bind_time,
            account_last_sync_time=last_sync_time,
        )

    def get_tis_account(self, user_id: str) -> Optional[Dict]:
        accounts = list_accounts_by_user(user_id)
        for account in accounts:
            if account['account_platform_type'] == 'tis':
                return account
        return None

    def update_sync_time(self, account_id: int, sync_time: Optional[str] = None) -> None:
        if not sync_time:
            sync_time = time.strftime('%Y-%m-%d %H:%M:%S')
        update_account_sync_time(account_id, sync_time)

    def delete_tis_account(self, user_id: str) -> None:
        accounts = list_accounts_by_user(user_id)
        for account in accounts:
            if account['account_platform_type'] == 'tis':
                delete_account(account['account_id'])
