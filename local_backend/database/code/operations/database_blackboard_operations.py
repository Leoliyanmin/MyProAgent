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
    delete_data
)
from typing import Optional, List, Dict
import time


class BlackboardAccountOperations:
    """Blackboard账号绑定相关的数据库操作"""
    
    def create_or_update_blackboard_account(
        self,
        user_id: str,
        username: str,
        encrypted_cookie: str,
        bind_time: Optional[str] = None,
        last_sync_time: Optional[str] = None
    ) -> int:
        """创建或更新Blackboard账号绑定信息"""
        # 先检查是否已存在绑定
        existing_accounts = list_accounts_by_user(user_id)
        blackboard_account = None
        
        for account in existing_accounts:
            if account['account_platform_type'] == 'blackboard':
                blackboard_account = account
                break
        
        if blackboard_account:
            # 更新现有账号
            # 这里需要先删除再创建，因为account表有唯一约束
            delete_account(blackboard_account['account_id'])
        
        # 创建新账号
        if not bind_time:
            bind_time = time.strftime('%Y-%m-%d %H:%M:%S')
        
        return create_account(
            user_id=user_id,
            account_platform_type='blackboard',
            account_platform_username=username,
            content=encrypted_cookie,
            account_bind_time=bind_time,
            account_last_sync_time=last_sync_time
        )
    
    def get_blackboard_account(self, user_id: str) -> Optional[Dict]:
        """获取用户的Blackboard账号绑定信息"""
        accounts = list_accounts_by_user(user_id)
        for account in accounts:
            if account['account_platform_type'] == 'blackboard':
                return account
        return None
    
    def update_sync_time(self, account_id: int, sync_time: Optional[str] = None) -> None:
        """更新同步时间"""
        if not sync_time:
            sync_time = time.strftime('%Y-%m-%d %H:%M:%S')
        update_account_sync_time(account_id, sync_time)
    
    def delete_blackboard_account(self, user_id: str) -> None:
        """删除Blackboard账号绑定"""
        accounts = list_accounts_by_user(user_id)
        for account in accounts:
            if account['account_platform_type'] == 'blackboard':
                delete_account(account['account_id'])


class BlackboardCourseOperations:
    """Blackboard课程相关的数据库操作"""
    
    def create_or_update_course(
        self,
        user_id: str,
        course_id: str,
        course_name: str,
        course_link: Optional[str] = None,
        course_content: Optional[str] = None,
        course_term: Optional[str] = None,
    ) -> int:
        """创建或更新课程信息"""
        # 先检查是否已存在该课程
        existing_categories = list_categories_by_user(user_id)
        existing_course = None
        
        for category in existing_categories:
            if category['category_kind'] != 'course':
                continue
            if course_id and category.get('category_external_id') == course_id:
                existing_course = category
                break
            if category['category_title'] == course_name:
                existing_course = category
                break
        
        if existing_course:
            # 更新现有课程
            update_category(
                category_id=existing_course['category_id'],
                category_kind='course',
                category_title=course_name,
                category_content=course_content,
                category_link=course_link,
                category_source='tis',
                category_external_id=course_id or None,
                category_term=course_term,
                category_meta_json=course_content,
                category_updated_at=time.strftime('%Y-%m-%d %H:%M:%S'),
            )
            return existing_course['category_id']
        else:
            # 创建新课程
            created_at = time.strftime('%Y-%m-%d %H:%M:%S')
            return create_category(
                user_id=user_id,
                category_kind='course',
                category_title=course_name,
                category_content=course_content,
                category_link=course_link,
                category_source='tis',
                category_external_id=course_id or None,
                category_term=course_term,
                category_meta_json=course_content,
                category_updated_at=created_at,
                category_created_at=created_at
            )
    
    def get_courses(self, user_id: str) -> List[Dict]:
        """获取用户的所有课程"""
        categories = list_categories_by_user(user_id)
        return [cat for cat in categories if cat['category_kind'] == 'course']
    
    def delete_course(self, category_id: int) -> None:
        """删除课程"""
        delete_category(category_id)


class BlackboardAssignmentOperations:
    """Blackboard作业相关的数据库操作"""
    
    def create_or_update_assignment(
        self,
        user_id: str,
        course_id: int,
        assignment_id: str,
        assignment_name: str,
        assignment_content: Optional[str] = None,
        assignment_link: Optional[str] = None,
        due_date: Optional[str] = None,
        is_previewable: int = 1
    ) -> int:
        """创建或更新作业信息"""
        # 先检查是否已存在该作业
        existing_data = list_data_by_user(user_id)
        existing_assignment = None
        
        for data in existing_data:
            if data['data_category_id'] != course_id or data['data_content_type'] != 'assignment':
                continue
            if assignment_id and data.get('data_external_id') == assignment_id:
                existing_assignment = data
                break
            if data['data_title'] == assignment_name:
                existing_assignment = data
                break
        
        if existing_assignment:
            # 更新现有作业
            update_data(
                data_id=existing_assignment['data_id'],
                data_title=assignment_name,
                data_content_text=assignment_content,
                data_link_url=assignment_link,
                data_release_time=None,
                data_ddl_time=due_date,
                data_is_previewable=is_previewable,
                data_source='tis',
                data_external_id=assignment_id or None,
                data_meta_json=assignment_content,
                data_raw_json=assignment_content,
                data_updated_at=time.strftime('%Y-%m-%d %H:%M:%S'),
            )
            return existing_assignment['data_id']
        else:
            # 创建新作业
            created_at = time.strftime('%Y-%m-%d %H:%M:%S')
            return create_data(
                user_id=user_id,
                data_category_id=course_id,
                data_content_type='assignment',
                data_classification_code=1,
                data_title=assignment_name,
                data_content_text=assignment_content,
                data_link_url=assignment_link,
                data_release_time=None,
                data_ddl_time=due_date,
                data_is_previewable=is_previewable,
                data_source='tis',
                data_external_id=assignment_id or None,
                data_meta_json=assignment_content,
                data_raw_json=assignment_content,
                data_updated_at=created_at,
                data_created_at=created_at
            )
    
    def get_assignments(self, user_id: str, course_id: Optional[int] = None) -> List[Dict]:
        """获取用户的作业，可选择按课程筛选"""
        data_list = list_data_by_user(user_id)
        assignments = [d for d in data_list if d['data_content_type'] == 'assignment']
        
        if course_id:
            assignments = [a for a in assignments if a['data_category_id'] == course_id]
        
        return assignments
    
    def delete_assignment(self, data_id: int) -> None:
        """删除作业"""
        delete_data(data_id)


class BlackboardAnnouncementOperations:
    """Blackboard公告相关的数据库操作"""
    
    def create_or_update_announcement(
        self,
        user_id: str,
        course_id: int,
        announcement_id: str,
        announcement_name: str,
        announcement_content: Optional[str] = None,
        announcement_link: Optional[str] = None,
        release_time: Optional[str] = None,
        is_previewable: int = 1
    ) -> int:
        """创建或更新公告信息"""
        existing_data = list_data_by_user(user_id)
        existing_announcement = None
        
        for data in existing_data:
            if data['data_category_id'] != course_id or data['data_content_type'] != 'announcement':
                continue
            if announcement_id and data.get('data_external_id') == announcement_id:
                existing_announcement = data
                break
            if data['data_title'] == announcement_name:
                existing_announcement = data
                break
        
        if existing_announcement:
            update_data(
                data_id=existing_announcement['data_id'],
                data_title=announcement_name,
                data_content_text=announcement_content,
                data_link_url=announcement_link,
                data_release_time=release_time,
                data_ddl_time=None,
                data_is_previewable=is_previewable,
                data_source='blackboard',
                data_external_id=announcement_id or None,
                data_meta_json=announcement_content,
                data_raw_json=announcement_content,
                data_updated_at=time.strftime('%Y-%m-%d %H:%M:%S'),
            )
            return existing_announcement['data_id']
        else:
            created_at = time.strftime('%Y-%m-%d %H:%M:%S')
            return create_data(
                user_id=user_id,
                data_category_id=course_id,
                data_content_type='announcement',
                data_classification_code=2,
                data_title=announcement_name,
                data_content_text=announcement_content,
                data_link_url=announcement_link,
                data_release_time=release_time,
                data_ddl_time=None,
                data_is_previewable=is_previewable,
                data_source='blackboard',
                data_external_id=announcement_id or None,
                data_meta_json=announcement_content,
                data_raw_json=announcement_content,
                data_updated_at=created_at,
                data_created_at=created_at
            )
    
    def get_announcements(self, user_id: str, course_id: Optional[int] = None) -> List[Dict]:
        """获取用户的公告"""
        data_list = list_data_by_user(user_id)
        announcements = [d for d in data_list if d['data_content_type'] == 'announcement']
        
        if course_id:
            announcements = [a for a in announcements if a['data_category_id'] == course_id]
        
        return announcements
    
    def delete_announcement(self, data_id: int) -> None:
        """删除公告"""
        delete_data(data_id)


class BlackboardCourseMaterialOperations:
    """Blackboard课程资料相关的数据库操作"""
    
    def create_or_update_course_material(
        self,
        user_id: str,
        course_id: int,
        material_id: str,
        material_name: str,
        material_content: Optional[str] = None,
        material_link: Optional[str] = None,
        release_time: Optional[str] = None,
        is_previewable: int = 1
    ) -> int:
        """创建或更新课程资料信息"""
        existing_data = list_data_by_user(user_id)
        existing_material = None
        
        for data in existing_data:
            if data['data_category_id'] != course_id or data['data_content_type'] != 'material':
                continue
            if material_id and data.get('data_external_id') == material_id:
                existing_material = data
                break
            if data['data_title'] == material_name:
                existing_material = data
                break
        
        if existing_material:
            update_data(
                data_id=existing_material['data_id'],
                data_title=material_name,
                data_content_text=material_content,
                data_link_url=material_link,
                data_release_time=release_time,
                data_ddl_time=None,
                data_is_previewable=is_previewable,
                data_source='blackboard',
                data_external_id=material_id or None,
                data_meta_json=material_content,
                data_raw_json=material_content,
                data_updated_at=time.strftime('%Y-%m-%d %H:%M:%S'),
            )
            return existing_material['data_id']
        else:
            created_at = time.strftime('%Y-%m-%d %H:%M:%S')
            return create_data(
                user_id=user_id,
                data_category_id=course_id,
                data_content_type='material',
                data_classification_code=3,
                data_title=material_name,
                data_content_text=material_content,
                data_link_url=material_link,
                data_release_time=release_time,
                data_ddl_time=None,
                data_is_previewable=is_previewable,
                data_source='blackboard',
                data_external_id=material_id or None,
                data_meta_json=material_content,
                data_raw_json=material_content,
                data_updated_at=created_at,
                data_created_at=created_at
            )
    
    def get_course_materials(self, user_id: str, course_id: Optional[int] = None) -> List[Dict]:
        """获取用户的课程资料"""
        data_list = list_data_by_user(user_id)
        materials = [d for d in data_list if d['data_content_type'] == 'material']
        
        if course_id:
            materials = [m for m in materials if m['data_category_id'] == course_id]
        
        return materials
    
    def delete_course_material(self, data_id: int) -> None:
        """删除课程资料"""
        delete_data(data_id)
