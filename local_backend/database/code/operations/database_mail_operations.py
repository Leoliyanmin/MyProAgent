import time
from typing import Optional, Dict

from local_backend.database.code.command.database_command import (
    create_account,
    list_accounts_by_user,
    update_account_sync_time,
    delete_account,
)


class MailAccountOperations:
    def create_or_update_mail_account(
        self,
        user_id: str,
        email_address: str,
        app_password: str,
        bind_time: Optional[str] = None,
        last_sync_time: Optional[str] = None,
    ) -> int:
        existing_accounts = list_accounts_by_user(user_id)
        mail_account = None
        for account in existing_accounts:
            if account['account_platform_type'] == 'mail':
                mail_account = account
                break
        if mail_account:
            delete_account(mail_account['account_id'])
        if not bind_time:
            bind_time = time.strftime('%Y-%m-%d %H:%M:%S')
        return create_account(
            user_id=user_id,
            account_platform_type='mail',
            account_platform_username=email_address,
            content=app_password,
            account_bind_time=bind_time,
            account_last_sync_time=last_sync_time,
        )

    def get_mail_account(self, user_id: str) -> Optional[Dict]:
        accounts = list_accounts_by_user(user_id)
        for account in accounts:
            if account['account_platform_type'] == 'mail':
                return account
        return None

    def update_sync_time(self, account_id: int, sync_time: Optional[str] = None) -> None:
        if not sync_time:
            sync_time = time.strftime('%Y-%m-%d %H:%M:%S')
        update_account_sync_time(account_id, sync_time)

    def delete_mail_account(self, user_id: str) -> None:
        accounts = list_accounts_by_user(user_id)
        for account in accounts:
            if account['account_platform_type'] == 'mail':
                delete_account(account['account_id'])
