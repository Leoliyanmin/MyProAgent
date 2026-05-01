from local_backend.database.code.command.database_command import (
    create_account,
    list_accounts_by_user,
    update_account_sync_time,
    delete_account,
    create_data,
    list_data_by_user,
    update_data,
    delete_data
)
from typing import Optional, Dict, List
import time
import json


class EmailAccountOperations:
    def create_or_update_email_account(
        self,
        user_id: str,
        email_address: str,
        encrypted_app_password: str,
        bind_time: Optional[str] = None,
        last_sync_time: Optional[str] = None,
    ) -> int:
        existing_accounts = list_accounts_by_user(user_id)
        email_account = None

        for account in existing_accounts:
            if account['account_platform_type'] == 'email':
                email_account = account
                break

        if email_account:
            delete_account(email_account['account_id'])

        if not bind_time:
            bind_time = time.strftime('%Y-%m-%d %H:%M:%S')

        return create_account(
            user_id=user_id,
            account_platform_type='email',
            account_platform_username=email_address,
            content=encrypted_app_password,
            account_bind_time=bind_time,
            account_last_sync_time=last_sync_time,
        )

    def get_email_account(self, user_id: str) -> Optional[Dict]:
        accounts = list_accounts_by_user(user_id)
        for account in accounts:
            if account['account_platform_type'] == 'email':
                return account
        return None

    def update_sync_time(self, account_id: int, sync_time: Optional[str] = None) -> None:
        if not sync_time:
            sync_time = time.strftime('%Y-%m-%d %H:%M:%S')
        update_account_sync_time(account_id, sync_time)

    def delete_email_account(self, user_id: str) -> None:
        accounts = list_accounts_by_user(user_id)
        for account in accounts:
            if account['account_platform_type'] == 'email':
                delete_account(account['account_id'])


class EmailMessageOperations:
    def create_or_update_message(
        self,
        user_id: str,
        category_id: int,
        mail_id: str,
        subject: str,
        sender: str,
        message_time: str,
        body: Optional[str] = None,
    ) -> int:
        existing_data = list_data_by_user(user_id)
        existing_message = None

        for data in existing_data:
            if data['data_content_type'] != 'mail':
                continue
            if data.get('data_external_id') == mail_id:
                existing_message = data
                break

        if existing_message:
            update_data(
                data_id=existing_message['data_id'],
                data_title=subject,
                data_content_text=body,
                data_release_time=message_time,
                data_meta_json=json.dumps({"sender": sender}, ensure_ascii=False),
                data_updated_at=time.strftime('%Y-%m-%d %H:%M:%S'),
            )
            return existing_message['data_id']
        else:
            created_at = time.strftime('%Y-%m-%d %H:%M:%S')
            return create_data(
                user_id=user_id,
                data_category_id=category_id,
                data_content_type='mail',
                data_classification_code=4,
                data_title=subject,
                data_content_text=body,
                data_link_url=None,
                data_release_time=message_time,
                data_ddl_time=None,
                data_is_previewable=1,
                data_source='email',
                data_external_id=mail_id,
                data_meta_json=json.dumps({"sender": sender}, ensure_ascii=False),
                data_raw_json=None,
                data_updated_at=created_at,
                data_created_at=created_at,
            )

    def get_messages(self, user_id: str) -> List[Dict]:
        data_list = list_data_by_user(user_id)
        return [d for d in data_list if d['data_content_type'] == 'mail']

    def delete_message(self, data_id: int) -> None:
        delete_data(data_id)
