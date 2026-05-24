import json
import time
from typing import Optional, Dict, List

from local_backend.database.code.command.database_command import (
    create_email_account,
    get_email_account,
    update_email_account_sync_time,
    delete_email_account,
    create_email_message,
    list_email_messages_by_user,
    delete_email_message,
    restore_email_message,
    permanent_delete_email_message,
)


class EmailAccountV2Operations:
    def create_or_update(self, user_id: str, email_address: str,
                         encrypted_password: str, bind_time: str = None) -> int:
        existing = get_email_account(user_id)
        if existing:
            delete_email_account(existing["account_id"])
        if not bind_time:
            bind_time = time.strftime("%Y-%m-%d %H:%M:%S")
        return create_email_account(
            user_id=user_id, email_address=email_address,
            encrypted_password=encrypted_password, bind_time=bind_time,
        )

    def get(self, user_id: str) -> Optional[Dict]:
        return get_email_account(user_id)

    def get_email_account(self, user_id: str) -> Optional[Dict]:
        return self.get(user_id)

    def update_sync_time(self, account_id: int, sync_time: str = None) -> None:
        if not sync_time:
            sync_time = time.strftime("%Y-%m-%d %H:%M:%S")
        update_email_account_sync_time(account_id, sync_time)

    def delete(self, user_id: str) -> None:
        existing = get_email_account(user_id)
        if existing:
            delete_email_account(existing["account_id"])


class EmailMessageV2Operations:
    def upsert(self, user_id: str, account_id: int, mail_id: str,
               subject: str, sender: str, message_time: str,
               recipient_email: str = None, body: str = None,
               raw_html: str = None) -> int:
        # 检查所有状态的邮件（包括回收站和已删除），避免重复插入
        all_existing = list_email_messages_by_user(user_id, status=0) \
                     + list_email_messages_by_user(user_id, status=1) \
                     + list_email_messages_by_user(user_id, status=2)
        for msg in all_existing:
            if msg.get("mail_uid") == mail_id:
                return msg["message_id"]
        recipients = json.dumps([recipient_email], ensure_ascii=False) if recipient_email else None
        return create_email_message(
            user_id=user_id, account_id=account_id, mail_uid=mail_id,
            subject=subject, sender=sender,
            recipients=recipients,
            body_text=body,
            body_html=raw_html,
            received_at=message_time,
        )

    def list_all(self, user_id: str) -> List[Dict]:
        return list_email_messages_by_user(user_id, status=0)

    def list_trash(self, user_id: str) -> List[Dict]:
        return list_email_messages_by_user(user_id, status=1)

    def delete(self, message_id: int) -> None:
        delete_email_message(message_id)

    def restore(self, message_id: int) -> None:
        restore_email_message(message_id)

    def permanent_delete(self, message_id: int) -> None:
        permanent_delete_email_message(message_id)

    def empty_trash(self, user_id: str) -> None:
        for msg in self.list_trash(user_id):
            permanent_delete_email_message(msg["message_id"])

    def delete_all_for_user(self, user_id: str) -> None:
        from local_backend.database.code.command.database_command import delete_email_messages_by_user
        delete_email_messages_by_user(user_id)


class StarredEmailV2Operations:
    def add_star(self, user_id: str, email_id: int, reason: str | None = None, source: str = 'manual') -> tuple[int, bool]:
        from local_backend.database.code.command.database_command import (
            create_starred_email, get_starred_email
        )
        existing = get_starred_email(user_id, email_id)
        if existing:
            return existing['star_id'], False
        return create_starred_email(user_id=user_id, email_id=email_id, reason=reason, source=source), True

    def remove_star(self, user_id: str, email_id: int) -> None:
        from local_backend.database.code.command.database_command import delete_starred_email
        delete_starred_email(user_id, email_id)

    def list_starred(self, user_id: str) -> list:
        from local_backend.database.code.command.database_command import list_starred_emails_by_user
        return list_starred_emails_by_user(user_id)

    def is_starred(self, user_id: str, email_id: int) -> bool:
        from local_backend.database.code.command.database_command import get_starred_email
        return get_starred_email(user_id, email_id) is not None
