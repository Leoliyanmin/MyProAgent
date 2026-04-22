from local_backend.database.code.operations.database_blackboard_operations import (
    BlackboardAccountOperations,
    BlackboardCourseOperations,
    BlackboardAssignmentOperations
)
from typing import Optional, Dict, List, Tuple
import json


class BlackboardHandle:
    """Blackboard相关的数据库操作流程控制"""
    
    def __init__(self):
        self.account_ops = BlackboardAccountOperations()
        self.course_ops = BlackboardCourseOperations()
        self.assignment_ops = BlackboardAssignmentOperations()
    
    def handle_bind_blackboard(
        self,
        user_id: str,
        username: str,
        encrypted_cookie: str
    ) -> Dict:
        """处理Blackboard账号绑定"""
        try:
            account_id = self.account_ops.create_or_update_blackboard_account(
                user_id=user_id,
                username=username,
                encrypted_cookie=encrypted_cookie
            )
            return {
                'success': True,
                'message': 'Blackboard账号绑定成功',
                'account_id': account_id
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'绑定失败: {str(e)}'
            }
    
    def handle_get_blackboard_status(self, user_id: str) -> Dict:
        """获取Blackboard绑定状态"""
        try:
            account = self.account_ops.get_blackboard_account(user_id)
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
                    'message': '未绑定Blackboard账号'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'获取状态失败: {str(e)}'
            }
    
    def handle_sync_courses(
        self,
        user_id: str,
        courses: List[Dict]
    ) -> Dict:
        """处理课程同步"""
        try:
            synced_courses = []
            for course in courses:
                course_id = self.course_ops.create_or_update_course(
                    user_id=user_id,
                    course_id=course.get('id'),
                    course_name=course.get('name'),
                    course_link=course.get('link'),
                    course_content=json.dumps(course.get('content', {}))
                )
                synced_courses.append({
                    'id': course_id,
                    'name': course.get('name')
                })
            
            return {
                'success': True,
                'message': f'成功同步 {len(synced_courses)} 门课程',
                'synced_courses': synced_courses
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'课程同步失败: {str(e)}'
            }
    
    def handle_sync_assignments(
        self,
        user_id: str,
        course_id: int,
        assignments: List[Dict]
    ) -> Dict:
        """处理作业同步"""
        try:
            synced_assignments = []
            for assignment in assignments:
                assignment_id = self.assignment_ops.create_or_update_assignment(
                    user_id=user_id,
                    course_id=course_id,
                    assignment_id=assignment.get('id'),
                    assignment_name=assignment.get('name'),
                    assignment_content=json.dumps(assignment.get('content', {})),
                    assignment_link=assignment.get('link'),
                    due_date=assignment.get('due_date'),
                    is_previewable=1
                )
                synced_assignments.append({
                    'id': assignment_id,
                    'name': assignment.get('name'),
                    'due_date': assignment.get('due_date')
                })
            
            return {
                'success': True,
                'message': f'成功同步 {len(synced_assignments)} 个作业',
                'synced_assignments': synced_assignments
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'作业同步失败: {str(e)}'
            }
    
    def handle_full_sync(
        self,
        user_id: str,
        sync_data: Dict
    ) -> Dict:
        """处理完整同步"""
        try:
            # 同步课程
            courses_result = self.handle_sync_courses(user_id, sync_data.get('courses', []))
            if not courses_result['success']:
                return courses_result
            
            # 同步作业
            all_assignments = []
            for course in sync_data.get('courses', []):
                # 查找课程ID
                courses = self.course_ops.get_courses(user_id)
                course_id = None
                for c in courses:
                    if c['category_title'] == course.get('name'):
                        course_id = c['category_id']
                        break
                
                if course_id and 'assignments' in course:
                    assignments_result = self.handle_sync_assignments(
                        user_id, course_id, course['assignments']
                    )
                    if not assignments_result['success']:
                        return assignments_result
                    all_assignments.extend(assignments_result['synced_assignments'])
            
            # 更新同步时间
            account = self.account_ops.get_blackboard_account(user_id)
            if account:
                self.account_ops.update_sync_time(account['account_id'])
            
            return {
                'success': True,
                'message': f'同步完成，共同步 {len(courses_result["synced_courses"])} 门课程和 {len(all_assignments)} 个作业',
                'synced_courses': courses_result['synced_courses'],
                'synced_assignments': all_assignments
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'同步失败: {str(e)}'
            }
    
    def handle_unbind_blackboard(self, user_id: str) -> Dict:
        """处理解绑Blackboard账号"""
        try:
            self.account_ops.delete_blackboard_account(user_id)
            return {
                'success': True,
                'message': 'Blackboard账号解绑成功'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'解绑失败: {str(e)}'
            }
