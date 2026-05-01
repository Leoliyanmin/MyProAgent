from local_backend.database.code.operations.database_tis_operations import (
    TisAccountOperations,
    TisCourseOperations,
    TisClassSessionOperations,
)
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

_WEEKDAY_CN_TO_NUM = {
    "星期一": 1,
    "星期二": 2,
    "星期三": 3,
    "星期四": 4,
    "星期五": 5,
    "星期六": 6,
    "星期日": 7,
}


class TisHandle:
    """TIS教务系统相关的数据库操作流程控制"""

    def __init__(self):
        self.account_ops = TisAccountOperations()
        self.course_ops = TisCourseOperations()
        self.session_ops = TisClassSessionOperations()

    def handle_bind_tis(
        self,
        user_id: str,
        username: str,
        encrypted_cookie: str
    ) -> Dict:
        try:
            account_id = self.account_ops.create_or_update_tis_account(
                user_id=user_id,
                username=username,
                encrypted_cookie=encrypted_cookie
            )
            return {
                'success': True,
                'message': 'TIS账号绑定成功',
                'account_id': account_id
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'绑定失败: {str(e)}'
            }

    def handle_get_tis_status(self, user_id: str) -> Dict:
        try:
            account = self.account_ops.get_tis_account(user_id)
            if account:
                return {
                    'success': True,
                    'is_bound': True,
                    'username': account['account_platform_username'],
                    'bind_time': account['account_bind_time'],
                    'last_sync_time': account['account_last_sync_time']
                }
            else:
                return {
                    'success': True,
                    'is_bound': False,
                    'message': '未绑定TIS账号'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'获取状态失败: {str(e)}'
            }

    def handle_sync_schedule(
        self,
        user_id: str,
        schedule_data: Dict
    ) -> Dict:
        """处理课表同步，接收 TIS scraper 的 result_dict"""
        try:
            if not schedule_data.get('success'):
                return {
                    'success': False,
                    'message': f"课表数据无效: {schedule_data.get('message', '未知错误')}"
                }

            term = schedule_data.get('term', '')
            week = schedule_data.get('week', '')
            schedule = schedule_data.get('schedule', {})

            if not schedule:
                return {
                    'success': True,
                    'message': '课表为空，无需同步',
                    'synced_courses': [],
                    'synced_sessions': []
                }

            synced_courses = []
            synced_sessions = []
            course_cache: Dict[str, int] = {}

            for weekday_label, sessions in schedule.items():
                weekday = _WEEKDAY_CN_TO_NUM.get(weekday_label)
                if weekday is None:
                    logger.warning(f"未知的星期标签: {weekday_label}")
                    continue

                for session in sessions:
                    course_name = session.get('title', '')
                    if not course_name:
                        continue

                    if course_name not in course_cache:
                        course_id = self.course_ops.create_or_update_course(
                            user_id=user_id,
                            course_name=course_name,
                            course_term=term
                        )
                        course_cache[course_name] = course_id
                        synced_courses.append({
                            'id': course_id,
                            'name': course_name
                        })
                    else:
                        course_id = course_cache[course_name]

                    session_id = self.session_ops.create_or_update_session(
                        user_id=user_id,
                        course_id=course_id,
                        course_name=course_name,
                        weekday=weekday,
                        start_time=session.get('start'),
                        end_time=session.get('end'),
                        periods=session.get('periods'),
                        teacher=session.get('teacher'),
                        weeks=session.get('weeks'),
                        location=session.get('location'),
                        week=week,
                        term=term,
                        raw_data=session,
                    )
                    synced_sessions.append({
                        'id': session_id,
                        'course_name': course_name,
                        'weekday': weekday,
                        'start_time': session.get('start'),
                        'end_time': session.get('end'),
                    })

            # 更新同步时间
            account = self.account_ops.get_tis_account(user_id)
            if account:
                self.account_ops.update_sync_time(account['account_id'])

            return {
                'success': True,
                'message': f'成功同步 {len(course_cache)} 门课程、{len(synced_sessions)} 个课时',
                'synced_courses': synced_courses,
                'synced_sessions': synced_sessions
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'课表同步失败: {str(e)}'
            }

    def handle_get_schedule(
        self,
        user_id: str,
        term: Optional[str] = None,
        course_id: Optional[int] = None
    ) -> Dict:
        try:
            courses = self.course_ops.get_courses(user_id)
            sessions = self.session_ops.get_sessions(user_id, course_id=course_id)

            if term:
                sessions = [s for s in sessions if s.get('data_term') == term]

            return {
                'success': True,
                'courses': courses,
                'sessions': sessions,
                'total_courses': len(courses),
                'total_sessions': len(sessions)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'获取课表失败: {str(e)}'
            }

    def handle_unbind_tis(self, user_id: str) -> Dict:
        try:
            self.account_ops.delete_tis_account(user_id)
            return {
                'success': True,
                'message': 'TIS账号解绑成功'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'解绑失败: {str(e)}'
            }
