from local_backend.database.code.operations.database_email_v2_operations import (
    EmailAccountV2Operations,
    EmailMessageV2Operations,
)


class EmailV2Handle:
    def __init__(self):
        self.account_ops = EmailAccountV2Operations()
        self.message_ops = EmailMessageV2Operations()

    def handle_bind_email(self, user_id: str, email_address: str,
                          encrypted_password: str) -> dict:
        try:
            account_id = self.account_ops.create_or_update(
                user_id=user_id, email_address=email_address,
                encrypted_password=encrypted_password,
            )
            return {"success": True, "message": "邮箱绑定成功", "account_id": account_id}
        except Exception as e:
            return {"success": False, "message": "绑定失败: {}".format(e)}

    def handle_get_email_status(self, user_id: str) -> dict:
        try:
            account = self.account_ops.get(user_id)
            if account:
                return {
                    "success": True, "is_bound": True,
                    "email_address": account["email_address"],
                    "bind_time": account.get("bind_time", ""),
                    "last_sync_time": account.get("last_sync_time", ""),
                }
            return {"success": True, "is_bound": False, "message": "未绑定邮箱"}
        except Exception as e:
            return {"success": False, "message": "获取状态失败: {}".format(e)}

    def handle_unbind_email(self, user_id: str) -> dict:
        try:
            self.account_ops.delete(user_id)
            return {"success": True, "message": "邮箱解绑成功"}
        except Exception as e:
            return {"success": False, "message": "解绑失败: {}".format(e)}

    def handle_sync_messages(self, user_id: str, messages: list) -> dict:
        try:
            account = self.account_ops.get(user_id)
            if not account:
                return {"success": False, "message": "未绑定邮箱"}
            account_id = account["account_id"]
            recipient = account.get("email_address", "")
            synced = 0
            for msg in messages:
                self.message_ops.upsert(
                    user_id=user_id, account_id=account_id,
                    mail_id=msg.get("mail_id", ""),
                    subject=msg.get("subject", ""),
                    sender=msg.get("sender", ""),
                    message_time=msg.get("time", ""),
                    recipient_email=recipient,
                    body=msg.get("body"),
                    raw_html=msg.get("raw_html"),
                )
                synced += 1
            self.account_ops.update_sync_time(account_id)
            return {"success": True, "message": "同步 {} 封邮件".format(synced)}
        except Exception as e:
            return {"success": False, "message": "同步失败: {}".format(e)}

    def handle_get_messages(self, user_id: str) -> dict:
        try:
            messages = self.message_ops.list_all(user_id)
            return {"success": True, "messages": messages}
        except Exception as e:
            return {"success": False, "message": "获取失败: {}".format(e)}

    def handle_delete_message(self, user_id: str, message_id: int) -> dict:
        try:
            self.message_ops.delete(message_id)
            return {"success": True, "message": "已移入回收站"}
        except Exception as e:
            return {"success": False, "message": "删除失败: {}".format(e)}

    def handle_get_trash(self, user_id: str) -> dict:
        try:
            messages = self.message_ops.list_trash(user_id)
            return {"success": True, "messages": messages}
        except Exception as e:
            return {"success": False, "message": "获取失败: {}".format(e)}

    def handle_restore_message(self, user_id: str, message_id: int) -> dict:
        try:
            self.message_ops.restore(message_id)
            return {"success": True, "message": "已恢复"}
        except Exception as e:
            return {"success": False, "message": "恢复失败: {}".format(e)}

    def handle_permanent_delete(self, user_id: str, message_id: int) -> dict:
        try:
            self.message_ops.permanent_delete(message_id)
            return {"success": True, "message": "已彻底删除"}
        except Exception as e:
            return {"success": False, "message": "删除失败: {}".format(e)}

    def handle_empty_trash(self, user_id: str) -> dict:
        try:
            self.message_ops.empty_trash(user_id)
            return {"success": True, "message": "回收站已清空"}
        except Exception as e:
            return {"success": False, "message": "清空失败: {}".format(e)}

    def handle_star_email(self, user_id: str, email_id: int, reason: str | None = None) -> dict:
        try:
            from local_backend.database.code.operations.database_email_v2_operations import StarredEmailV2Operations
            star_ops = StarredEmailV2Operations()
            star_ops.add_star(user_id, email_id, reason or '手动标注', 'manual')
            return {'success': True, 'message': '已星标'}
        except Exception as e:
            return {'success': False, 'message': '星标失败: {}'.format(e)}

    def handle_unstar_email(self, user_id: str, email_id: int) -> dict:
        try:
            from local_backend.database.code.operations.database_email_v2_operations import StarredEmailV2Operations
            star_ops = StarredEmailV2Operations()
            star_ops.remove_star(user_id, email_id)
            return {'success': True, 'message': '已取消星标'}
        except Exception as e:
            return {'success': False, 'message': '取消星标失败: {}'.format(e)}

    def handle_get_starred_emails(self, user_id: str) -> dict:
        try:
            from local_backend.database.code.operations.database_email_v2_operations import StarredEmailV2Operations
            star_ops = StarredEmailV2Operations()
            starred = star_ops.list_starred(user_id)
            return {'success': True, 'starred': starred}
        except Exception as e:
            return {'success': False, 'message': '获取失败: {}'.format(e)}
