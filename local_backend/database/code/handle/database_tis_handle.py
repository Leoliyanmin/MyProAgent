from local_backend.database.code.operations.database_tis_operations import TisAccountOperations, TisCourseOperations
from typing import Optional, Dict, List
import json
import logging
import time

logger = logging.getLogger(__name__)


class TisHandle:
    def __init__(self):
        self.account_ops = TisAccountOperations()
        self.course_ops = TisCourseOperations()

    def handle_bind_tis(
        self,
        user_id: str,
        student_id: str,
        encrypted_cookie: str,
    ) -> Dict:
        try:
            account_id = self.account_ops.create_or_update_tis_account(
                user_id=user_id,
                student_id=student_id,
                encrypted_cookie=encrypted_cookie,
            )
            return {'success': True, 'message': 'TIS账号绑定成功', 'account_id': account_id}
        except Exception as e:
            return {'success': False, 'message': f'绑定失败: {str(e)}'}

    def handle_get_tis_status(self, user_id: str) -> Dict:
        try:
            account = self.account_ops.get_tis_account(user_id)
            if account:
                return {
                    'success': True,
                    'is_bound': True,
                    'student_id': account['account_platform_username'],
                    'bind_time': account['account_bind_time'],
                    'last_sync_time': account['account_last_sync_time'],
                }
            else:
                return {'success': True, 'is_bound': False, 'message': '未绑定TIS账号'}
        except Exception as e:
            return {'success': False, 'message': f'获取状态失败: {str(e)}'}

    def handle_unbind_tis(self, user_id: str) -> Dict:
        try:
            self.account_ops.delete_tis_account(user_id)
            return {'success': True, 'message': 'TIS账号解绑成功'}
        except Exception as e:
            return {'success': False, 'message': f'解绑失败: {str(e)}'}

    def save_schedule_v2(self, user_id: str, schedule_data: dict) -> dict:
        return self.course_ops.save_all(user_id, schedule_data)
