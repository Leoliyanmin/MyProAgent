from local_backend.database.code.operations.database_mail_operations import (
    MailAccountOperations,
    MailCategoryOperations,
    MailMessageOperations,
)
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class MailHandle:
    """邮件相关的数据库操作流程控制"""

    def __init__(self):
        self.account_ops = MailAccountOperations()
        self.category_ops = MailCategoryOperations()
        self.message_ops = MailMessageOperations()

    def handle_bind_mail(
        self,
        user_id: str,
        email_address: str,
        app_password: str
    ) -> Dict:
        try:
            account_id = self.account_ops.create_or_update_mail_account(
                user_id=user_id,
                email_address=email_address,
                app_password=app_password
            )
            return {
                'success': True,
                'message': '邮箱账号绑定成功',
                'account_id': account_id
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'绑定失败: {str(e)}'
            }

    def handle_get_mail_status(self, user_id: str) -> Dict:
        try:
            account = self.account_ops.get_mail_account(user_id)
            if account:
                return {
                    'success': True,
                    'is_bound': True,
                    'email_address': account['account_platform_username'],
                    'bind_time': account['account_bind_time'],
                    'last_sync_time': account['account_last_sync_time']
                }
            else:
                return {
                    'success': True,
                    'is_bound': False,
                    'message': '未绑定邮箱账号'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'获取状态失败: {str(e)}'
            }

    def handle_sync_mails(
        self,
        user_id: str,
        mail_data: Dict
    ) -> Dict:
        """处理邮件同步，接收 MailScraper 的返回值"""
        try:
            messages = mail_data.get('messages', [])
            if not messages:
                return {
                    'success': True,
                    'message': '无邮件数据需要同步',
                    'synced_count': 0
                }

            # 确保邮件分类存在
            category_id = self.category_ops.ensure_mail_category(user_id)

            synced_messages = []
            for msg in messages:
                mail_id = msg.get('mail_id', '')
                if not mail_id:
                    continue

                data_id = self.message_ops.create_or_update_message(
                    user_id=user_id,
                    category_id=category_id,
                    mail_id=mail_id,
                    subject=msg.get('subject', ''),
                    sender=msg.get('sender', ''),
                    mail_time=msg.get('time', ''),
                    body=msg.get('body'),
                    raw_data=msg,
                )
                synced_messages.append({
                    'id': data_id,
                    'mail_id': mail_id,
                    'subject': msg.get('subject', ''),
                })

            # 更新同步时间
            account = self.account_ops.get_mail_account(user_id)
            if account:
                self.account_ops.update_sync_time(account['account_id'])

            return {
                'success': True,
                'message': f'成功同步 {len(synced_messages)} 封邮件',
                'synced_count': len(synced_messages),
                'synced_messages': synced_messages
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'邮件同步失败: {str(e)}'
            }

    def handle_get_mails(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> Dict:
        try:
            messages = self.message_ops.get_messages(user_id, limit=limit)
            return {
                'success': True,
                'messages': messages,
                'total': len(messages)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'获取邮件失败: {str(e)}'
            }

    def handle_unbind_mail(self, user_id: str) -> Dict:
        try:
            self.account_ops.delete_mail_account(user_id)
            return {
                'success': True,
                'message': '邮箱账号解绑成功'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'解绑失败: {str(e)}'
            }
