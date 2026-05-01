from local_backend.database.code.command.database_command import (
    create_category, update_category, list_categories_by_user,
)
from local_backend.database.code.operations.database_tis_operations import TisAccountOperations
from typing import Optional, Dict, List
import json
import logging
import time

logger = logging.getLogger(__name__)

WEEKDAY_LABELS = {
    "星期一": 1, "Tuesday": 2, "星期三": 3, "星期四": 4,
    "星期五": 5, "星期六": 6, "星期日": 7,
    "Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4,
    "Friday": 5, "Saturday": 6, "Sunday": 7,
}


class TisHandle:
    def __init__(self):
        self.account_ops = TisAccountOperations()

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

    def handle_sync_schedule(
        self,
        user_id: str,
        term: str,
        week: str,
        schedule_data: Dict,
    ) -> Dict:
        try:
            existing_categories = list_categories_by_user(user_id)
            tis_term_cat = None
            for cat in existing_categories:
                if cat['category_kind'] == 'term' and cat.get('category_term') == term:
                    tis_term_cat = cat
                    break

            if tis_term_cat:
                term_category_id = tis_term_cat['category_id']
            else:
                created_at = time.strftime('%Y-%m-%d %H:%M:%S')
                term_category_id = create_category(
                    user_id=user_id,
                    category_kind='term',
                    category_title=f'TIS课表 - {term}',
                    category_content=None,
                    category_link=None,
                    category_source='tis',
                    category_external_id=None,
                    category_term=term,
                    category_meta_json=json.dumps({"term": term, "week": week}),
                    category_updated_at=created_at,
                    category_created_at=created_at,
                )

            existing_courses = list_categories_by_user(user_id)
            stored_courses = [c for c in existing_courses if c['category_kind'] == 'course' and c.get('category_source') == 'tis']

            synced_courses = 0
            for day_label, day_courses in schedule_data.items():
                for course in day_courses:
                    course_name = course.get('title', '')
                    course_teacher = course.get('teacher', '')
                    course_key = f"{course_name}|{course_teacher}"
                    course_category_id = None

                    for sc in stored_courses:
                        meta = sc.get('category_meta_json')
                        if meta:
                            try:
                                meta_dict = json.loads(meta)
                                if meta_dict.get('course_key') == course_key:
                                    course_category_id = sc['category_id']
                                    break
                            except (json.JSONDecodeError, TypeError):
                                pass

                    if course_category_id is None:
                        created_at = time.strftime('%Y-%m-%d %H:%M:%S')
                        course_category_id = create_category(
                            user_id=user_id,
                            category_kind='course',
                            category_title=course_name,
                            category_content=json.dumps(course, ensure_ascii=False),
                            category_link=None,
                            category_source='tis',
                            category_external_id=None,
                            category_term=term,
                            category_meta_json=json.dumps({"course_key": course_key, "teacher": course_teacher}, ensure_ascii=False),
                            category_updated_at=created_at,
                            category_created_at=created_at,
                        )
                        stored_courses.append({"category_id": course_category_id, "category_meta_json": json.dumps({"course_key": course_key})})
                    else:
                        update_category(
                            category_id=course_category_id,
                            category_kind='course',
                            category_title=course_name,
                            category_content=json.dumps(course, ensure_ascii=False),
                            category_link=None,
                            category_source='tis',
                            category_term=term,
                            category_updated_at=time.strftime('%Y-%m-%d %H:%M:%S'),
                        )

                    synced_courses += 1

            account = self.account_ops.get_tis_account(user_id)
            if account:
                self.account_ops.update_sync_time(account['account_id'])

            return {
                'success': True,
                'message': f'成功同步 {synced_courses} 门课程',
                'synced_courses': synced_courses,
            }
        except Exception as e:
            logger.error(f"同步TIS课表失败: {e}")
            return {'success': False, 'message': f'同步课表失败: {str(e)}'}
