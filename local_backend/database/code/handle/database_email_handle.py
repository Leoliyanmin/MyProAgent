from local_backend.database.code.operations.database_email_operations import (
    EmailAccountOperations,
    EmailMessageOperations,
)
from typing import Optional, Dict, List
import json
import logging

logger = logging.getLogger(__name__)


class EmailHandle:
    def __init__(self):
        self.account_ops = EmailAccountOperations()
        self.message_ops = EmailMessageOperations()

    def handle_bind_email(
        self,
        user_id: str,
        email_address: str,
        encrypted_app_password: str,
    ) -> Dict:
        try:
            account_id = self.account_ops.create_or_update_email_account(
                user_id=user_id,
                email_address=email_address,
                encrypted_app_password=encrypted_app_password,
            )
            return {
                'success': True,
                'message': '邮箱账号绑定成功',
                'account_id': account_id,
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'绑定失败: {str(e)}',
            }

    def handle_get_email_status(self, user_id: str) -> Dict:
        try:
            account = self.account_ops.get_email_account(user_id)
            if account:
                return {
                    'success': True,
                    'is_bound': True,
                    'email_address': account['account_platform_username'],
                    'bind_time': account['account_bind_time'],
                    'last_sync_time': account['account_last_sync_time'],
                }
            else:
                return {
                    'success': True,
                    'is_bound': False,
                    'message': '未绑定邮箱账号',
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'获取状态失败: {str(e)}',
            }

    def handle_sync_messages(
        self,
        user_id: str,
        messages: List[Dict],
    ) -> Dict:
        try:
            synced_messages = []
            for msg in messages:
                msg_id = self.message_ops.create_or_update_message(
                    user_id=user_id,
                    mail_id=msg.get('mail_id', ''),
                    subject=msg.get('subject', ''),
                    sender=msg.get('sender', ''),
                    message_time=msg.get('time', ''),
                    body=msg.get('body', ''),
                )
                synced_messages.append({
                    'id': msg_id,
                    'subject': msg.get('subject'),
                })

            account = self.account_ops.get_email_account(user_id)
            if account:
                self.account_ops.update_sync_time(account['account_id'])

            return {
                'success': True,
                'message': f'成功同步 {len(synced_messages)} 封邮件',
                'synced_messages': synced_messages,
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'邮件同步失败: {str(e)}',
            }

    def handle_unbind_email(self, user_id: str) -> Dict:
        try:
            self.account_ops.delete_email_account(user_id)
            return {
                'success': True,
                'message': '邮箱账号解绑成功',
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'解绑失败: {str(e)}',
            }
