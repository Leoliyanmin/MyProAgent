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
            synced = 0
            for msg in messages:
                self.message_ops.upsert(
                    user_id=user_id, account_id=account_id,
                    mail_id=msg.get("mail_id", ""),
                    subject=msg.get("subject", ""),
                    sender=msg.get("sender", ""),
                    message_time=msg.get("message_time", ""),
                    body=msg.get("body"),
                    raw_data=msg.get("raw_data"),
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
            return {"success": True, "message": "删除成功"}
        except Exception as e:
            return {"success": False, "message": "删除失败: {}".format(e)}
