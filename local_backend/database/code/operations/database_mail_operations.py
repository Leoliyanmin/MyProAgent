import json
import time
from typing import Optional, List, Dict

from local_backend.database.code.command.database_command import (
    create_account,
    list_accounts_by_user,
    update_account_sync_time,
    delete_account,
    create_category,
    list_categories_by_user,
    create_data,
    list_data_by_user,
    update_data,
    delete_data,
)


class MailAccountOperations:
    """邮件账号绑定相关的数据库操作"""

    def create_or_update_mail_account(
        self,
        user_id: str,
        email_address: str,
        app_password: str,
        bind_time: Optional[str] = None,
        last_sync_time: Optional[str] = None
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
            account_last_sync_time=last_sync_time
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


class MailCategoryOperations:
    """邮件分类相关的数据库操作"""

    def ensure_mail_category(self, user_id: str) -> int:
        categories = list_categories_by_user(user_id)
        for cat in categories:
            if cat['category_kind'] == 'mail' and cat.get('category_source') == 'mail':
                return cat['category_id']

        created_at = time.strftime('%Y-%m-%d %H:%M:%S')
        return create_category(
            user_id=user_id,
            category_kind='mail',
            category_title='学校邮箱',
            category_content=None,
            category_link=None,
            category_source='mail',
            category_external_id=None,
            category_term=None,
            category_meta_json=None,
            category_updated_at=created_at,
            category_created_at=created_at
        )


class MailMessageOperations:
    """邮件消息相关的数据库操作"""

    def create_or_update_message(
        self,
        user_id: str,
        category_id: int,
        mail_id: str,
        subject: str,
        sender: str,
        mail_time: str,
        body: Optional[str] = None,
        raw_data: Optional[Dict] = None,
    ) -> int:
        existing_data = list_data_by_user(user_id)
        existing_message = None

        for data in existing_data:
            if data['data_content_type'] != 'mail':
                continue
            if data.get('data_external_id') == mail_id:
                existing_message = data
                break

        meta = {"sender": sender}

        if existing_message:
            update_data(
                data_id=existing_message['data_id'],
                data_title=subject,
                data_content_text=body,
                data_link_url=None,
                data_release_time=mail_time,
                data_ddl_time=None,
                data_is_previewable=1,
                data_source='mail',
                data_external_id=mail_id,
                data_meta_json=json.dumps(meta, ensure_ascii=False),
                data_raw_json=json.dumps(raw_data, ensure_ascii=False) if raw_data else None,
                data_updated_at=time.strftime('%Y-%m-%d %H:%M:%S'),
            )
            return existing_message['data_id']
        else:
            created_at = time.strftime('%Y-%m-%d %H:%M:%S')
            return create_data(
                user_id=user_id,
                data_category_id=category_id,
                data_content_type='mail',
                data_classification_code=1,
                data_title=subject,
                data_content_text=body,
                data_link_url=None,
                data_release_time=mail_time,
                data_ddl_time=None,
                data_is_previewable=1,
                data_source='mail',
                data_external_id=mail_id,
                data_meta_json=json.dumps(meta, ensure_ascii=False),
                data_raw_json=json.dumps(raw_data, ensure_ascii=False) if raw_data else None,
                data_updated_at=created_at,
                data_created_at=created_at
            )

    def get_messages(self, user_id: str, limit: Optional[int] = None) -> List[Dict]:
        data_list = list_data_by_user(user_id)
        messages = [d for d in data_list if d['data_content_type'] == 'mail']
        messages.sort(key=lambda m: m.get('data_release_time') or '', reverse=True)
        if limit is not None:
            messages = messages[:limit]
        return messages

    def delete_message(self, data_id: int) -> None:
        delete_data(data_id)
