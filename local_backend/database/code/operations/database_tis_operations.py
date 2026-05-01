import json
import re
import time
from typing import Optional, List, Dict

from local_backend.database.code.command.database_command import (
    create_account,
    list_accounts_by_user,
    update_account_sync_time,
    delete_account,
    create_category,
    list_categories_by_user,
    update_category,
    delete_category,
    create_data,
    list_data_by_user,
    update_data,
    delete_data,
)


class TisAccountOperations:
    """TIS账号绑定相关的数据库操作"""

    def create_or_update_tis_account(
        self,
        user_id: str,
        username: str,
        encrypted_cookie: str,
        bind_time: Optional[str] = None,
        last_sync_time: Optional[str] = None
    ) -> int:
        existing_accounts = list_accounts_by_user(user_id)
        tis_account = None

        for account in existing_accounts:
            if account['account_platform_type'] == 'tis':
                tis_account = account
                break

        if tis_account:
            delete_account(tis_account['account_id'])

        if not bind_time:
            bind_time = time.strftime('%Y-%m-%d %H:%M:%S')

        return create_account(
            user_id=user_id,
            account_platform_type='tis',
            account_platform_username=username,
            content=encrypted_cookie,
            account_bind_time=bind_time,
            account_last_sync_time=last_sync_time
        )

    def get_tis_account(self, user_id: str) -> Optional[Dict]:
        accounts = list_accounts_by_user(user_id)
        for account in accounts:
            if account['account_platform_type'] == 'tis':
                return account
        return None

    def update_sync_time(self, account_id: int, sync_time: Optional[str] = None) -> None:
        if not sync_time:
            sync_time = time.strftime('%Y-%m-%d %H:%M:%S')
        update_account_sync_time(account_id, sync_time)

    def delete_tis_account(self, user_id: str) -> None:
        accounts = list_accounts_by_user(user_id)
        for account in accounts:
            if account['account_platform_type'] == 'tis':
                delete_account(account['account_id'])


class TisCourseOperations:
    """TIS课程相关的数据库操作"""

    def create_or_update_course(
        self,
        user_id: str,
        course_name: str,
        course_term: Optional[str] = None,
    ) -> int:
        existing_categories = list_categories_by_user(user_id)
        existing_course = None

        for category in existing_categories:
            if category['category_kind'] != 'course':
                continue
            if category.get('category_source') != 'tis':
                continue
            if category['category_title'] == course_name:
                existing_course = category
                break

        if existing_course:
            update_category(
                category_id=existing_course['category_id'],
                category_kind='course',
                category_title=course_name,
                category_content=None,
                category_link=None,
                category_source='tis',
                category_external_id=None,
                category_term=course_term,
                category_meta_json=None,
                category_updated_at=time.strftime('%Y-%m-%d %H:%M:%S'),
            )
            return existing_course['category_id']
        else:
            created_at = time.strftime('%Y-%m-%d %H:%M:%S')
            return create_category(
                user_id=user_id,
                category_kind='course',
                category_title=course_name,
                category_content=None,
                category_link=None,
                category_source='tis',
                category_external_id=None,
                category_term=course_term,
                category_meta_json=None,
                category_updated_at=created_at,
                category_created_at=created_at
            )

    def get_courses(self, user_id: str) -> List[Dict]:
        categories = list_categories_by_user(user_id)
        return [cat for cat in categories
                if cat['category_kind'] == 'course' and cat.get('category_source') == 'tis']

    def get_course_by_name(self, user_id: str, course_name: str) -> Optional[Dict]:
        courses = self.get_courses(user_id)
        for course in courses:
            if course['category_title'] == course_name:
                return course
        return None

    def delete_course(self, category_id: int) -> None:
        delete_category(category_id)


class TisClassSessionOperations:
    """TIS课表时段相关的数据库操作"""

    @staticmethod
    def _extract_periods(periods_str: str):
        """从节次字符串提取开始和结束节次编号"""
        match = re.search(r'(\d+)-(\d+)', periods_str)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None, None

    def create_or_update_session(
        self,
        user_id: str,
        course_id: int,
        course_name: str,
        weekday: int,
        start_time: Optional[str],
        end_time: Optional[str],
        periods: Optional[str],
        teacher: Optional[str],
        weeks: Optional[str],
        location: Optional[str],
        week: Optional[str],
        term: Optional[str],
        raw_data: Optional[Dict] = None,
    ) -> int:
        period_start, period_end = self._extract_periods(periods or "")

        meta = {
            "teacher": teacher or "",
            "weeks": weeks or "",
            "location": location or "",
            "periods": periods or "",
        }

        existing_data = list_data_by_user(user_id)
        existing_session = None

        for data in existing_data:
            if data['data_category_id'] != course_id:
                continue
            if data['data_content_type'] != 'class_session':
                continue
            if (data.get('data_weekday') == weekday
                    and data.get('data_period_start') == period_start
                    and data.get('data_period_end') == period_end
                    and data.get('data_term') == term):
                existing_session = data
                break

        if existing_session:
            update_data(
                data_id=existing_session['data_id'],
                data_title=course_name,
                data_content_text=None,
                data_link_url=None,
                data_release_time=None,
                data_ddl_time=None,
                data_is_previewable=1,
                data_source='tis',
                data_external_id=None,
                data_term=term,
                data_week=week,
                data_weekday=weekday,
                data_period_start=period_start,
                data_period_end=period_end,
                data_start_time=start_time,
                data_end_time=end_time,
                data_meta_json=json.dumps(meta, ensure_ascii=False),
                data_raw_json=json.dumps(raw_data, ensure_ascii=False) if raw_data else None,
                data_updated_at=time.strftime('%Y-%m-%d %H:%M:%S'),
            )
            return existing_session['data_id']
        else:
            created_at = time.strftime('%Y-%m-%d %H:%M:%S')
            return create_data(
                user_id=user_id,
                data_category_id=course_id,
                data_content_type='class_session',
                data_classification_code=1,
                data_title=course_name,
                data_content_text=None,
                data_link_url=None,
                data_release_time=None,
                data_ddl_time=None,
                data_is_previewable=1,
                data_source='tis',
                data_external_id=None,
                data_term=term,
                data_week=week,
                data_weekday=weekday,
                data_period_start=period_start,
                data_period_end=period_end,
                data_start_time=start_time,
                data_end_time=end_time,
                data_meta_json=json.dumps(meta, ensure_ascii=False),
                data_raw_json=json.dumps(raw_data, ensure_ascii=False) if raw_data else None,
                data_updated_at=created_at,
                data_created_at=created_at
            )

    def get_sessions(self, user_id: str, course_id: Optional[int] = None) -> List[Dict]:
        data_list = list_data_by_user(user_id)
        sessions = [d for d in data_list if d['data_content_type'] == 'class_session']

        if course_id is not None:
            sessions = [s for s in sessions if s['data_category_id'] == course_id]

        return sessions

    def get_sessions_by_term(self, user_id: str, term: str) -> List[Dict]:
        sessions = self.get_sessions(user_id)
        return [s for s in sessions if s.get('data_term') == term]

    def delete_session(self, data_id: int) -> None:
        delete_data(data_id)
